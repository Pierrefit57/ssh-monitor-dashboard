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

# --- 3. SIDEBAR & FILTRES ---
with st.sidebar:
    st.header("Filtres")

    # --- NOUVEAU : Filtre par Date (Période) ---
    # On cherche la date min et max dans le fichier pour configurer le widget
    min_date = df['Timestamp'].min().date()
    max_date = df['Timestamp'].max().date()

    # Le widget renvoie un tuple (date_debut, date_fin)
    date_range = st.date_input(
        "Sélectionner une période",
        value=(min_date, max_date), # Valeurs par défaut
        min_value=min_date,
        max_value=max_date
    )

    st.markdown("---")

    # --- Filtre EventId ---
    event_options = df['EventId'].unique().tolist()
    event_options.insert(0, "Tous")
    selected_event = st.selectbox("Type d'événement (EventId) :", event_options)

    # --- Filtre IPs ---
    ip_options = sorted(df['SourceIP'].dropna().unique().tolist())
    selected_ips = st.multiselect("IPs spécifiques :", ip_options)


# --- 4. LOGIQUE DE FILTRAGE ---
df_filtered = df.copy()

# A. Filtre par Date
# On vérifie que l'utilisateur a bien sélectionné une date de début ET de fin
if len(date_range) == 2:
    start_date, end_date = date_range
    # On filtre : on ne garde que ce qui est >= debut ET <= fin
    # .dt.date est important pour comparer des jours et pas des heures précises
    mask = (df_filtered['Timestamp'].dt.date >= start_date) & (df_filtered['Timestamp'].dt.date <= end_date)
    df_filtered = df_filtered[mask]

# B. Filtre EventId
if selected_event != "Tous":
    df_filtered = df_filtered[df_filtered['EventId'] == selected_event]

# C. Filtre IPs
if selected_ips:
    df_filtered = df_filtered[df_filtered['SourceIP'].isin(selected_ips)]


# --- 5. FEEDBACK UTILISATEUR ---
if df_filtered.empty:
    st.warning("Aucune donnée ne correspond à vos filtres actuels.")
    st.stop()


# --- 6. INDICATEURS CLÉS (KPIs) ---
st.subheader(f"Statistiques (Période du {date_range[0]} au {date_range[1] if len(date_range)>1 else '...'})")

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
    st.caption("Top 10 des adresses IP")
    top_ips = df_filtered['SourceIP'].value_counts().head(10)
    st.bar_chart(top_ips)

# --- GRAPHIQUE 2 : Évolution Temporelle ---
with chart_col2:
    st.caption("Volume d'attaques par heure")
    if not df_filtered['Timestamp'].isnull().all():
        # Le graphique va s'adapter automatiquement aux dates filtrées !
        time_data = df_filtered.set_index('Timestamp').resample('h').size()
        st.line_chart(time_data)
    else:
        st.info("Pas assez de données temporelles.")

# --- 8. APERÇU DES DONNÉES ---
with st.expander("Voir les données filtrées"):
    st.dataframe(df_filtered)