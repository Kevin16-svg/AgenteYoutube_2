# -*- coding: utf-8 -*-

import os

import streamlit as st


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

    /* Fondo general de toda la aplicación */
    .stApp {
        background: #f7f7f7;
        color: #111827;
    }

    /* Contenedor principal donde vive el contenido */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 6rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* Fuente general de la app */
    html, body, [class*="css"] {
        font-family: Inter, "Segoe UI", sans-serif;
    }

    /* Oculta elementos nativos de Streamlit: menú, header y footer */
    header, footer, #MainMenu {
        display: none !important;
        visibility: hidden;
    }

    /* =========================
       HEADER SUPERIOR TIPO YOUTUBE
    ========================= */

    .yt-header-wrapper {
        width: 100%;
        min-height: 60px;
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 1.2rem;
        margin: 0rem -2rem 1.5rem -2rem;
        box-sizing: border-box;
    }

    .yt-header-left {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    /* Logos reutilizados: header, sidebar y pantalla vacía */
    .yt-logo, .sidebar-logo, .empty-logo {
        background: #ff0000;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        letter-spacing: 0;
    }

    .yt-logo {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        font-size: 0.8rem;
    }

    .yt-title {
        color: #0f0f0f;
        font-size: 1rem;
        font-weight: 850;
        line-height: 1.1;
    }

    .yt-subtitle {
        color: #6b7280;
        font-size: 0.75rem;
        margin-top: 2px;
    }

    .yt-header-right {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        flex-wrap: wrap;
    }

    /* Etiquetas tipo píldora del header */
    .yt-pill {
        background: #ffffff;
        border: 1px solid #919191;
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        font-size: 0.76rem;
        font-weight: 650;
        color: #4b5563;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        white-space: nowrap;
    }

    /* =========================
       TARJETA DE BIENVENIDA
    ========================= */

    .welcome-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1.2rem 1.3rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .welcome-top {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }

    .welcome-icon {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: linear-gradient(135deg, #ff0033, #ff4d6d);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 900;
        flex-shrink: 0;
    }

    .welcome-title {
        font-size: 1rem;
        font-weight: 850;
        color: #0f0f0f;
        margin-bottom: 0.25rem;
    }

    .welcome-subtitle {
        font-size: 0.84rem;
        line-height: 1.5;
        color: #6b7280;
    }

    .welcome-tags-text {
        margin-top: 1rem;
        color: #374151;
        font-size: 0.78rem;
        font-weight: 650;
    }

    /* =========================
       SIDEBAR
    ========================= */

    [data-testid="stSidebar"] {
        background-color: #f2f2f2;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.45rem !important;
    }

    .sidebar-title {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.8rem;
    }

    .sidebar-logo {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        font-size: 0.7rem;
    }

    .sidebar-main-title {
        font-size: 0.9rem;
        font-weight: 850;
        color: #0f0f0f;
    }

    .sidebar-subtitle {
        font-size: 0.67rem;
        color: #8a8a8a;
    }

    .sidebar-section-title {
        font-size: 0.64rem;
        font-weight: 850;
        color: #9ca3af;
        letter-spacing: 0.08rem;
        margin: 0.48rem 0 0.32rem 0;
    }

    .sidebar-item {
        background: transparent;
        border-radius: 10px;
        padding: 0.34rem 0.38rem;
        margin-bottom: 0.04rem;
        color: #0f0f0f;
        font-size: 0.74rem;
        display: grid;
        grid-template-columns: 24px 1fr;
        column-gap: 0.35rem;
        align-items: center;
    }

    .sidebar-item:hover {
        background: #e5e5e5;
    }

    .sidebar-item span {
        font-weight: 750;
    }

    .sidebar-item small {
        grid-column: 2;
        color: #8a8a8a;
        font-size: 0.63rem;
        margin-top: -0.08rem;
    }

    .sidebar-divider {
        height: 1px;
        background: #dddddd;
        margin: 0.55rem 0;
    }

    /* Estado del canal dentro del sidebar */
    .channel-status-card {
        border-top: 1px solid #dddddd;
        padding-top: 0.55rem;
        margin-top: 0.35rem;
    }

    .channel-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.72rem;
        margin-bottom: 0.28rem;
        gap: 0.8rem;
    }

    .channel-row span {
        color: #8a8a8a;
        font-weight: 520;
    }

    .channel-row b {
        color: #0f0f0f;
        font-weight: 780;
        text-align: right;
    }

    .agent-active {
        color: #e60023 !important;
    }

    /* Información de conexión: proyecto, dataset, tabla, etc. */
    .connection-info {
        margin-top: 0.8rem;
        color: #0f0f0f;
        font-size: 0.82rem;
    }

    .connection-info code {
        background: #111827;
        color: #22c55e;
        padding: 0.15rem 0.35rem;
        border-radius: 6px;
    }

    /* =========================
       BOTONES DE STREAMLIT
    ========================= */

    .stButton > button {
        border-radius: 999px;
        border: 1px solid #d1d5db;
        background-color: #ffffff;
        color: #374151;
        font-weight: 700;
        min-height: 32px;
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        font-size: 0.78rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #f1f1f1;
        border-color: #c7c7c7;
        color: #0f0f0f;
        transform: translateY(-1px);
    }

    /* =========================
       PANTALLA VACÍA / ESTADO INICIAL
    ========================= */

    .empty-logo, .empty-title, .empty-text {
        max-width: 560px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
    }

    .empty-logo {
        width: 64px;
        height: 48px;
        margin-top: 4rem;
        margin-bottom: 1.2rem;
        border-radius: 16px;
        font-size: 0.9rem;
        box-shadow: 0 8px 20px rgba(255,0,0,0.25);
    }

    .empty-title {
        font-size: 1.35rem;
        font-weight: 850;
        color: #111827;
        margin-bottom: 0.8rem;
    }

    .empty-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #4b5563;
    }

    /* =========================
       MENSAJES DEL CHAT
    ========================= */

    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0 !important;
    }

    [data-testid="stChatMessageContent"] {
        background: white;
        color: #0f0f0f;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }

    /* Caja que aparece mientras el agente está pensando */
    .thinking-box {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 0.9rem 1rem;
        width: fit-content;
        color: #4b5563;
        font-size: 0.9rem;
    }

    .thinking-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #ff0000;
        animation: pulse 1s infinite;
    }

    /* Animación del punto rojo de carga */
    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.1); }
        100% { opacity: 0.4; transform: scale(0.9); }
    }

    /* =========================
       BARRA INFERIOR DEL CHAT
    ========================= */
    
    [data-testid="stBottom"] {
        background: #ffffff !important;
        border-top: 1px solid #272727 !important;
        padding: 0.9rem 2rem !important;
    }
    
    /* Contenedor interno */
    [data-testid="stBottom"] > div {
        max-width: 1050px !important;
        margin: 0 auto !important;
        background: transparent !important;
    }
    
    /* Caja completa del input */
    [data-baseweb="textarea"] {
        border-radius: 999px !important;
        border: 1px solid #ffffff !important;
        background: #ffffff !important;
        box-shadow: none !important;
    }
    
    /* Textarea real */
    [data-baseweb="textarea"] textarea {
        background: #ffffff !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        padding-top: 0.95rem !important;
        padding-left: 1.2rem !important;
    }
    
    /* Placeholder */
    [data-baseweb="textarea"] textarea::placeholder {
        color: #ffffff !important;
        opacity: 1 !important;
    }
    
    /* Botón enviar */
    [data-testid="stChatInput"] button {
        background: #ff0000 !important;
        color: white !important;
        border-radius: 999px !important;
        border: none !important;
    }
    
    /* Hover botón */
    [data-testid="stChatInput"] button:hover {
        background: #cc0000 !important;
    }

    /* Botón de enviar mensaje */
    [data-testid="stChatInput"] button {
        background: #ff0000 !important;
        color: white !important;
        border-radius: 999px !important;
        border: none !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 6. HEADER
# =========================
videos_count = segment_stats.get("videos") or metrics.get("videos") or 0
st.markdown(
    f"""
    <div class="yt-header-wrapper">
        <div class="yt-header-left">
            <div class="yt-logo">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width:22px;height:22px;fill:white;">
                    <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
                </svg>
            </div>
            <div>
                <div class="yt-title">Las Damitas Histeria</div>
                <div class="yt-subtitle">Agente de análisis · Gemini + BigQuery</div>
            </div>
        </div>
        <div class="yt-header-right">
            <div class="yt-pill">
                <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#2BA84A;margin-right:6px;vertical-align:middle;"></span>
                Gemini conectado
            </div>
            <div class="yt-pill">
                <svg viewBox="0 0 24 24" style="width:13px;height:13px;fill:#555;margin-right:5px;vertical-align:middle;flex-shrink:0">
                    <path d="M19.59 7a2.5 2.5 0 0 0-1.76-1.76C16.46 5 12 5 12 5s-4.46 0-5.83.24A2.5 2.5 0 0 0 4.41 7 26 26 0 0 0 4.17 12a26 26 0 0 0 .24 5 2.5 2.5 0 0 0 1.76 1.76C7.54 19 12 19 12 19s4.46 0 5.83-.24A2.5 2.5 0 0 0 19.59 17 26 26 0 0 0 19.83 12a26 26 0 0 0-.24-5zM10 15v-6l5 3-5 3z"/>
                </svg>
                {format_compact_number(videos_count)} videos
            </div>
            <div class="yt-pill">
                <svg viewBox="0 0 24 24" style="width:13px;height:13px;fill:#555;margin-right:5px;vertical-align:middle;flex-shrink:0">
                    <path d="M4 6h16M4 10h16M4 14h10"/>
                    <circle cx="18" cy="17" r="3"/>
                    <path d="M18 14v3l2 1"/>
                </svg>
                {format_compact_number(segment_stats.get("segmentos"))} segmentos
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 7. SIDEBAR
# =========================
with st.sidebar:

    # ── Header ──
    st.markdown(
        """
        <div class="sidebar-title">
            <span class="sidebar-logo">YT</span>
            <div>
                <div class="sidebar-main-title">Las Damitas Histeria</div>
                <div class="sidebar-subtitle">Agente YouTube Analytics</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Accesos rápidos (botones funcionales) ──
    st.markdown('<div class="sidebar-section-title">ACCESOS RAPIDOS</div>', unsafe_allow_html=True)

    accesos = [
        ("🏆", "Top videos",              "Ranking por vistas",            "¿Cuáles son los 5 videos con más vistas?"),
        ("📅", "Mejor día para publicar", "Views, likes y engagement",     "¿Qué día de la semana es mejor para publicar?"),
        ("🔥", "Temas exitosos",          "Por interacción",               "¿Qué temas tienen mejor interacción?"),
        ("📊", "Resumen del canal",       "Métricas generales",            "Dame un resumen general del canal"),
        ("🔍", "Buscar por tema",         "En qué episodio hablaron de X", "¿En qué episodio se habló de familia?"),
    ]

    for emoji, titulo, subtitulo, prompt_texto in accesos:
        col_btn, col_txt = st.columns([1, 5])
        with col_btn:
            st.markdown(f"<div style='font-size:20px;padding-top:6px;text-align:center'>{emoji}</div>", unsafe_allow_html=True)
        with col_txt:
            if st.button(titulo, key=f"acc_{titulo}", use_container_width=True):
                st.session_state.prompt_sugerido = prompt_texto
        st.markdown(f"<div style='font-size:11px;color:#999;margin:-8px 0 6px 44px'>{subtitulo}</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Canal al día ──
    st.markdown('<div class="sidebar-section-title">CANAL AL DIA</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="channel-status-card">
            <div class="channel-row"><span>Videos</span><b>{format_compact_number(metrics.get("videos") or videos_count)}</b></div>
            <div class="channel-row"><span>Views</span><b>{format_compact_number(metrics.get("views"))}</b></div>
            <div class="channel-row"><span>Likes</span><b>{format_compact_number(metrics.get("likes"))}</b></div>
            <div class="channel-row"><span>Comentarios</span><b>{format_compact_number(metrics.get("comentarios"))}</b></div>
            <div class="channel-row"><span>Segmentos</span><b>{format_compact_number(segment_stats.get("segmentos"))}</b></div>
            <div class="channel-row"><span>Estado</span><b class="agent-active">Activo</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Limpiar conversación ──
    if st.button("🗑️ Limpiar conversación", use_container_width=True, key="btn_clear"):
        st.session_state.messages = []
        st.rerun()


# =========================
# 8. BIENVENIDA
# =========================

st.markdown(
    """
    <div class="welcome-card">
        <div class="welcome-top">
            <div class="welcome-icon">AI</div>
            <div>
                <div class="welcome-title">Que puede hacer este agente?</div>
                <div class="welcome-subtitle">
                    Consulta metricas, rendimiento, temas, transcripciones, recomendaciones,
                    mejores dias para publicar y momentos aproximados dentro de episodios.
                </div>
            </div>
        </div>
        <div class="welcome-tags-text">
            Analytics · Videos · Engagement · Transcripciones · Gemini AI · BigQuery
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 9. MEMORIA
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown('<div class="empty-logo">PLAY</div>', unsafe_allow_html=True)
    st.markdown('<div class="empty-title">Hola, soy tu agente de YouTube</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="empty-text">
            Puedo analizar el rendimiento de <b>Las Damitas Histeria</b>, encontrar
            en que episodio hablaron de un tema y recomendarte decisiones con datos.
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
