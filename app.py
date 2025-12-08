import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Monitor SSH",
    page_icon="🛡️",
    layout="wide"
)

st.title("Dashboard de surveillance SSH")

# --- 2. ETL & CACHE ---
@st.cache_data
def load_data():
    df = pd.read_csv('dataset_ssh.csv')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Erreur : Le fichier 'dataset_ssh.csv' est introuvable.")
    st.stop()

# --- 3. SIDEBAR & FILTRES (C'est ici que ça change !) ---
with st.sidebar:
    st.header("Filtres")

    # --- Filtre 1 : EventId (Selectbox) ---
    # On récupère la liste unique des EventId
    event_options = df['EventId'].unique().tolist()
    # On ajoute une option 'Tous' au début pour pouvoir tout voir
    event_options.insert(0, "Tous")
    
    selected_event = st.selectbox("Sélectionner un EventId :", event_options)

    # --- Filtre 2 : SourceIP (Multiselect) ---
    # On récupère les IPs uniques, triées
    ip_options = sorted(df['SourceIP'].dropna().unique().tolist())
    selected_ips = st.multiselect("Sélectionner des IPs spécifiques :", ip_options)


# --- 4. LOGIQUE DE FILTRAGE ---
# On part du DataFrame complet
df_filtered = df.copy()

# Application du filtre EventId
if selected_event != "Tous":
    df_filtered = df_filtered[df_filtered['EventId'] == selected_event]

# Application du filtre IPs (seulement si l'utilisateur a sélectionné quelque chose)
if selected_ips:
    df_filtered = df_filtered[df_filtered['SourceIP'].isin(selected_ips)]


# --- 5. FEEDBACK UTILISATEUR ---
# Si le filtrage ne donne rien, on arrête tout et on prévient
if df_filtered.empty:
    st.warning("Aucune donnée ne correspond à vos filtres actuels.")
    st.stop() # Arrête l'exécution du script ici pour éviter les erreurs graphiques


# --- 6. INDICATEURS CLÉS (KPIs) ---
# ATTENTION : On utilise maintenant df_filtered !
st.subheader("Indicateurs Clés (Filtrés)")

total_events = len(df_filtered)
unique_ips = df_filtered['SourceIP'].nunique()
unique_users = df_filtered['User'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Événements", total_events)
col2.metric("IPs Uniques", unique_ips)
col3.metric("Utilisateurs Visés", unique_users)

st.markdown("---")

# --- 7. GRAPHIQUES ---
st.subheader("Analyses visuelles")

chart_col1, chart_col2 = st.columns(2)

# --- GRAPHIQUE 1 : TOP IPs ---
with chart_col1:
    st.caption("Top 10 des adresses IP (sur la sélection)")
    top_ips = df_filtered['SourceIP'].value_counts().head(10)
    st.bar_chart(top_ips)

# --- GRAPHIQUE 2 : Évolution Temporelle ---
with chart_col2:
    st.caption("Volume d'attaques par heure")
    if not df_filtered['Timestamp'].isnull().all():
        time_data = df_filtered.set_index('Timestamp').resample('h').size()
        st.line_chart(time_data)
    else:
        st.info("Pas assez de données temporelles pour afficher le graphique.")

# --- 8. APERÇU DES DONNÉES ---
with st.expander("Voir les données filtrées"):
    st.dataframe(df_filtered)