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

    # Filtre Date
    min_date = df['Timestamp'].min().date()
    max_date = df['Timestamp'].max().date()
    
    date_range = st.date_input(
        "Période",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.markdown("---")

    # Filtres EventId et IPs
    event_options = df['EventId'].unique().tolist()
    event_options.insert(0, "Tous")
    selected_event = st.selectbox("Type d'événement :", event_options)

    ip_options = sorted(df['SourceIP'].dropna().unique().tolist())
    selected_ips = st.multiselect("IPs spécifiques :", ip_options)

# --- 4. LOGIQUE DE FILTRAGE ---
df_filtered = df.copy()

# Filtre Date
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df_filtered['Timestamp'].dt.date >= start_date) & (df_filtered['Timestamp'].dt.date <= end_date)
    df_filtered = df_filtered[mask]

# Filtre EventId
if selected_event != "Tous":
    df_filtered = df_filtered[df_filtered['EventId'] == selected_event]

# Filtre IPs
if selected_ips:
    df_filtered = df_filtered[df_filtered['SourceIP'].isin(selected_ips)]

if df_filtered.empty:
    st.warning("Aucune donnée ne correspond à vos filtres.")
    st.stop()

# --- 5. KPIs ---
st.subheader("Statistiques Globales")
col1, col2, col3 = st.columns(3)
col1.metric("Total Événements", len(df_filtered))
col2.metric("IPs Uniques", df_filtered['SourceIP'].nunique())
col3.metric("Utilisateurs Visés", df_filtered['User'].nunique())

st.markdown("---")

# --- 6. GRAPHIQUES ---
st.subheader("Analyses visuelles")

# --- PREMIÈRE LIGNE ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.caption("📈 Volume d'attaques par heure")
    if not df_filtered['Timestamp'].isnull().all():
        time_data = df_filtered.set_index('Timestamp').resample('h').size()
        st.line_chart(time_data)
    else:
        st.info("Données temporelles insuffisantes.")

with row1_col2:
    st.caption("🏆 Top 10 IPs Sources")
    top_ips = df_filtered['SourceIP'].value_counts().head(10)
    # AJOUT : horizontal=True pour mieux lire les IPs
    st.bar_chart(top_ips, horizontal=True)

# --- DEUXIÈME LIGNE ---
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.caption("🍕 Répartition des types d'événements")
    
    event_counts = df_filtered['EventId'].value_counts()
    
    fig, ax = plt.subplots(figsize=(6, 4)) # J'ai ajusté la taille
    
    # ASTUCE : Une petite fonction pour masquer les % trop petits (< 5%)
    def autopct_clean(pct):
        return ('%1.1f%%' % pct) if pct > 5 else ''
    
    wedges, texts, autotexts = ax.pie(
        event_counts, 
        labels=None,          # Pas de nom sur le camembert
        autopct=autopct_clean, # On utilise notre filtre intelligent
        startangle=90,
        textprops={'fontsize': 9, 'color': 'white'} # Texte en blanc si ton fond est foncé, ou 'black'
    )
    
    # Pour s'assurer que le texte des % est bien lisible (noir par défaut)
    plt.setp(autotexts, size=9, weight="bold", color="black")
    
    ax.axis('equal')
    
    # Légende déplacée encore plus à droite pour éviter tout contact
    ax.legend(
        wedges, 
        event_counts.index,
        title="Type d'Event",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1) # Décale la légende vers l'extérieur
    )
    
    st.pyplot(fig)

with row2_col2:
    st.caption("👤 Top 10 Utilisateurs tentés")
    top_users = df_filtered['User'].dropna().value_counts().head(10)
    # AJOUT : horizontal=True pour mieux lire les noms
    st.bar_chart(top_users, horizontal=True)