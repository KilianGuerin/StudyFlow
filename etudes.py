import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="StudyFlow", page_icon="🎓", layout="centered")

# --- DESIGN CUSTOM (CSS pour rendre ça beau) ---
# On cache le menu par défaut pour un look "App Native"
st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('study_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  matiere TEXT,
                  tache TEXT,
                  progress INTEGER,
                  deadline TEXT,
                  notes TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- FONCTIONS ---
def add_task(matiere, tache, deadline, notes):
    c = conn.cursor()
    c.execute("INSERT INTO tasks (matiere, tache, progress, deadline, notes) VALUES (?, ?, 0, ?, ?)",
              (matiere, tache, deadline, notes))
    conn.commit()

def update_progress(task_id, new_progress):
    c = conn.cursor()
    c.execute("UPDATE tasks SET progress=? WHERE id=?", (new_progress, task_id))
    conn.commit()

def delete_task(task_id):
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()

def load_data():
    return pd.read_sql_query("SELECT * FROM tasks ORDER BY deadline", conn)

# --- INTERFACE ---

# 1. Header & Stats Globales
st.title("🎓 Mes Études")

df = load_data()

if not df.empty:
    avg_progress = df['progress'].mean()
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Progression Globale", f"{int(avg_progress)}%")
    with col_stat2:
        st.metric("Tâches actives", len(df))
    # Barre globale
    st.progress(int(avg_progress))
else:
    st.info("Ajoute ta première matière pour commencer ! 🚀")

st.divider()

# 2. Sidebar : Ajouter une tâche
with st.sidebar:
    st.header("➕ Nouveau devoir / Révision")
    matiere_input = st.selectbox("Matière", ["Maths 📐", "Physique ⚛️", "Info 💻", "Anglais 🇬🇧", "Histoire 🏛️", "Autre 📚"])
    tache_input = st.text_input("Titre (ex: Chapitre 3)")
    date_input = st.date_input("Pour le", value=date.today())
    note_input = st.text_area("Notes / Détails")
    
    if st.button("Ajouter au planning", use_container_width=True):
        if tache_input:
            add_task(matiere_input, tache_input, date_input, note_input)
            st.success("Ajouté !")
            st.rerun()

# 3. Filtres
matieres_existantes = df['matiere'].unique().tolist() if not df.empty else []
filtre_matiere = st.multiselect("Filtrer par matière", matieres_existantes)

if filtre_matiere:
    df = df[df['matiere'].isin(filtre_matiere)]

# 4. Affichage des Cartes de Tâches
for index, row in df.iterrows():
    # Conteneur style "Carte"
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        
        with c1:
            st.markdown(f"### {row['matiere']}")
            st.caption(f"📅 Pour le : {row['deadline']}")
            st.write(f"**{row['tache']}**")
            if row['notes']:
                st.info(row['notes'], icon="📝")
        
        with c2:
            # Bouton supprimer discret
            if st.button("🗑️", key=f"del_{row['id']}"):
                delete_task(row['id'])
                st.rerun()

        # BARRE DE PROGRESSION INTERACTIVE
        # C'est ici que la magie opère : un slider qui met à jour la DB
        progress_val = st.slider(
            f"Avancement ({row['progress']}%)", 
            0, 100, 
            value=row['progress'], 
            key=f"slider_{row['id']}"
        )
        
        # Mise à jour immédiate si on change le slider
        if progress_val != row['progress']:
            update_progress(row['id'], progress_val)
            st.rerun()
        
        # Feedback visuel couleur
        if progress_val == 100:
            st.success("Terminé ! 🎉")
        elif progress_val > 0:
            st.progress(progress_val)
        else:
            st.warning("Pas encore commencé")