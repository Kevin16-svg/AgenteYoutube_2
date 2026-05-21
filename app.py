# -*- coding: utf-8 -*-

import os

import streamlit as st
from google.cloud import bigquery


# =========================
# 1. CONFIGURACION DE PAGINA
# =========================

st.set_page_config(
    page_title="Las Damitas Histeria | Agente YouTube",
    page_icon="play",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# 2. CREDENCIALES
# =========================

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("Error critico: no se encontro GOOGLE_API_KEY en Secrets o en el archivo .env.")
    st.stop()

try:
    has_gcp_secret = "gcp_service_account" in st.secrets
except Exception:
    has_gcp_secret = False

if not has_gcp_secret and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    st.warning(
        "No se encontro gcp_service_account en Secrets ni GOOGLE_APPLICATION_CREDENTIALS. "
        "En local se intentara usar credenciales ADC de Google."
    )


# =========================
# 3. IMPORTACION DEL AGENTE
# =========================

try:
    from agent import (
        CHANNEL_ID,
        DATASET_ID,
        PROJECT_ID,
        SEGMENTS_TABLE_ID,
        TABLE_NAME,
        get_agent,
        get_retriever,
    )
except Exception as exc:
    st.error("Error al importar el agente desde agent.py.")
    st.exception(exc)
    st.stop()


# =========================
# 4. RECURSOS
# =========================

try:
    retriever = get_retriever()
    agent = get_agent()
except Exception as exc:
    st.error(
        "No se pudo inicializar BigQuery. Revisa gcp_service_account en "
        "Streamlit Secrets o configura credenciales ADC."
    )
    st.exception(exc)
    st.stop()


def format_compact_number(value):
    try:
        value = float(value or 0)
    except Exception:
        return "0"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{int(value):,}"


@st.cache_data(show_spinner=False, ttl=900)
def load_sidebar_stats():
    try:
        metrics = retriever.analytics_summary() or {}
    except Exception:
        metrics = {}

    try:
        segment_stats = retriever.transcript_segments_stats()
    except Exception:
        segment_stats = {
            "existe": False,
            "videos": 0,
            "segmentos": 0,
            "actualizado": None,
            "embedding_model": None,
        }

    return metrics, segment_stats


metrics, segment_stats = load_sidebar_stats()


# =========================
# 5. ESTILOS GENERALES DE LA APP
# =========================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body, .stApp {
        background-color: #0f0f0f;  /* Fondo oscuro principal */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #f0f0f0;
    }

    /* Ocultar elementos nativos de Streamlit */
    header, footer, #MainMenu {
        display: none !important;
    }

    .block-container {
        padding: 1.5rem 2rem 6rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* Tarjetas oscuras */
    .card, .metric-card, .video-card, .topic-card {
        background-color: #1e1e1e;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        transition: all 0.2s ease;
        border: 1px solid #2c2c2c;
    }
    .card:hover, .video-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.6);
        border-color: #e63946;
    }
    .metric-card {
        padding: 1.2rem 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
    }
    .metric-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #a0a0a0;
    }
    .metric-change {
        color: #10b981;
        font-size: 0.7rem;
        margin-top: 0.3rem;
    }

    /* Header */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    .logo-area {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .logo-icon {
        background: #e63946;
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.6rem;
        box-shadow: 0 4px 12px rgba(230,57,70,0.4);
    }
    .logo-text h1 {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.3px;
    }
    .logo-text p {
        font-size: 0.7rem;
        color: #a0a0a0;
    }
    .badge {
        background: #2c2c2c;
        padding: 0.4rem 1rem;
        border-radius: 40px;
        font-size: 0.75rem;
        color: #e63946;
        font-weight: 700;
        border: 1px solid #3a3a3a;
    }

    /* Grid de videos */
    .videos-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.2rem;
        margin-top: 1rem;
    }
    .video-card {
        overflow: hidden;
    }
    .video-thumb {
        width: 100%;
        aspect-ratio: 16/9;
        object-fit: cover;
        background: #2a2a2a;
    }
    .video-info {
        padding: 0.8rem;
    }
    .video-title {
        font-weight: 700;
        font-size: 0.85rem;
        color: #f0f0f0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .video-stats {
        font-size: 0.7rem;
        color: #a0a0a0;
        display: flex;
        justify-content: space-between;
        margin-top: 0.4rem;
    }

    /* Gráfico (matplotlib) - se ajustará con estilo propio */
    .chart-container {
        background: #1e1e1e;
        border-radius: 20px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #2c2c2c;
    }

    /* Tendencias */
    .topic-grid {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1rem 0;
    }
    .topic-card {
        flex: 1;
        padding: 0.8rem;
        text-align: center;
    }

    /* Chat - fondos oscuros */
    .stChatInput input {
        background-color: #2c2c2c !important;
        border: 1px solid #3a3a3a !important;
        color: #ffffff !important;
        border-radius: 40px !important;
        padding: 0.6rem 1rem !important;
    }
    .stChatInput input::placeholder {
        color: #a0a0a0 !important;
    }
    .stChatInput button {
        background-color: #e63946 !important;
        border-radius: 40px !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stChatInput button:hover {
        background-color: #c1121f !important;
    }

    /* Mensajes del chat */
    [data-testid="stChatMessageContent"] {
        background-color: #1e1e1e !important;
        color: #f0f0f0 !important;
        border: 1px solid #2c2c2c !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 6. HEADER
# =========================

from google.cloud import bigquery

@st.cache_data(ttl=600)
def get_dashboard_data():
    try:
        top_videos = retriever.ranked_videos(order_by="views", limit=6)
        channel_profile = retriever.channel_profile() or {}
        analytics = retriever.analytics_summary() or {}
        topics = retriever.topic_performance(limit=5, order_by="engagement")
        subs_df = []
        # ... (código para subs_df) ...
        return top_videos, channel_profile, analytics, topics, subs_df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return [], {}, {}, [], [] 

# Cargar datos
top_videos, channel_profile, analytics, topics, subs_df = get_dashboard_data()


# --- HEADER ---
st.markdown(f"""
<div class="dashboard-header">
    <div class="logo-area">
        <div class="logo-icon">▶</div>
        <div class="logo-text">
            <h1>INFLUENCER INSIGHTS LAB</h1>
            <p>YouTube Analytics · Gemini AI · BigQuery</p>
        </div>
    </div>
    <div class="badge">Pro Analyst</div>
</div>
""", unsafe_allow_html=True)

# --- Video destacado y métricas ---
if top_videos:
    featured = top_videos[0]
    video_url = featured.get("url_video", "")
    video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else ""
    
    col1, col2 = st.columns([1.6, 1])
    with col1:
        if video_id:
            st.markdown(f"""
            <div class="card">
                <iframe width="100%" height="315" src="https://www.youtube.com/embed/{video_id}" 
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen></iframe>
                <div style="margin-top: 0.8rem;">
                    <strong>{featured.get('titulo_video', 'Top video')}</strong><br>
                    <span style="font-size:0.8rem; color:#606060;">{featured.get('views', 0):,} vistas · {featured.get('engagement', 0):.1%} engagement</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Video destacado no disponible (falta URL)")
    with col2:
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        metrics_data = [
            ("Engagement", f"{analytics.get('engagement_promedio', 0):.1f}%", "+2.1%"),
            ("Watch Time", f"{featured.get('views', 0) * (featured.get('duracion_minutos', 10) / 60):,.0f} hrs", "+14%"),            
            ("Views", f"{analytics.get('views', 0):,.0f}", "+8.5%"),
            ("Subscribers Gained", f"+{channel_profile.get('suscriptores_canal', 0)-100000:,}", "+38%")
        ]
        for label, value, change in metrics_data:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-change">▲ {change}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No hay videos para mostrar. Verifica la conexión con BigQuery.")

# --- Gráfico de suscriptores (opcional) ---
if subs_df:
    import pandas as pd
    import matplotlib.pyplot as plt
    df_subs = pd.DataFrame(subs_df)
    if not df_subs.empty and 'fecha_publicacion' in df_subs.columns and 'suscriptores_canal' in df_subs.columns:
        df_subs['fecha_publicacion'] = pd.to_datetime(df_subs['fecha_publicacion'])
        df_subs = df_subs.sort_values('fecha_publicacion')
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(df_subs['fecha_publicacion'], df_subs['suscriptores_canal'], color='#ff0000', linewidth=2)
        ax.fill_between(df_subs['fecha_publicacion'], df_subs['suscriptores_canal'], alpha=0.1, color='#ff0000')
        ax.set_title("Crecimiento de suscriptores en el tiempo", fontsize=12, fontweight='bold')
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Suscriptores")
        ax.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig)
    else:
        st.info("No hay datos suficientes para el gráfico de suscriptores.")
else:
    st.info("No se encontraron datos de evolución de suscriptores.")

# --- Top videos de crecimiento ---
if top_videos:
    st.markdown("## 🚀 Top Videos de Crecimiento")
    cols = st.columns(3)
    for idx, video in enumerate(top_videos[:6]):
        with cols[idx % 3]:
            thumb_url = video.get('thumbnail_url', 'https://via.placeholder.com/320x180?text=No+Thumbnail')
            st.markdown(f"""
            <div class="video-card">
                <img class="video-thumb" src="{thumb_url}" onerror="this.src='https://via.placeholder.com/320x180?text=Error'">
                <div class="video-info">
                    <div class="video-title">{video.get('titulo_video', 'Sin título')[:60]}</div>
                    <div class="video-stats">
                        <span>👁 {video.get('views', 0):,}</span>
                        <span>❤️ {video.get('likes', 0):,}</span>
                        <span>📈 {video.get('engagement', 0):.1%}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- Tendencias de contenido ---
if topics:
    st.markdown("## 📊 Tendencias de Contenido")
    topic_cols = st.columns(4)
    for i, topic in enumerate(topics[:4]):
        with topic_cols[i]:
            st.metric(label=topic.get('tema_legible', 'Tema'), value=f"{topic.get('engagement_promedio', 0):.1%} engagement", delta=f"{topic.get('videos',0)} videos")
else:
    st.info("No hay datos de temas disponibles.")

# =========================
# 9. MEMORIA
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width:34px;height:34px;fill:white;">
                <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="empty-title">Hola, soy tu agente de YouTube</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="empty-text">
            Puedo analizar el rendimiento de <b>Las Damitas Histeria</b>, encontrar
            en qué episodio hablaron de un tema y recomendarte decisiones con datos.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# 10. HISTORIAL
# =========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# 11. CHAT
# =========================
prompt = st.chat_input("Pregunta sobre el canal... ej: Que temas tuvieron mas engagement?")

# ── Capturar prompts de los botones del sidebar ──
if "prompt_sugerido" in st.session_state:
    prompt = st.session_state.pop("prompt_sugerido")

if prompt:
    history_for_agent = st.session_state.messages[-8:]
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(
            """
            <div class="thinking-box">
                <div class="thinking-dot"></div>
                Analizando métricas y transcripciones...
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            answer = agent.answer(prompt, history=history_for_agent)
            thinking_placeholder.empty()
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as exc:
            thinking_placeholder.empty()
            error_message = (
                "**Ocurrió un error al procesar tu pregunta.**\n\n"
                f"`{str(exc)}`\n\n"
                "Revisa Secrets, permisos de BigQuery y la tabla de segmentos."
            )
            st.error(error_message)
            st.exception(exc)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
