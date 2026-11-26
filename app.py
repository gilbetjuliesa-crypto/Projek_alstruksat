"""Titik masuk aplikasi Music PlaylistPas."""
import streamlit as st
import sys
import os

sys.pycache_prefix = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__pycache__")

from config import (
    HALAMAN_ANALISIS,
    HALAMAN_TEMUKAN,
    NAMA_APLIKASI,
    init_state,
)
from halaman import analisis, temukan
from login import ganti_password_form, login_page, logout

st.set_page_config(
    page_title=NAMA_APLIKASI,
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tampilan global agar seluruh halaman konsisten.
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1450px;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
    [data-testid="stSidebar"] .block-container {padding-top: 1.5rem;}
    div[data-testid="stMetric"] {background: rgba(128,128,128,.07); padding: 14px 16px; border-radius: 12px;}
    div.stButton > button, div.stDownloadButton > button {border-radius: 10px; min-height: 40px;}
    div[data-testid="stForm"] {border: 1px solid rgba(128,128,128,.2); border-radius: 14px; padding: 1.2rem;}
    div[data-testid="stExpander"] {border-radius: 12px;}
    @media (max-width: 700px) {
      .block-container {padding-left: 1rem; padding-right: 1rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_state()

if not st.session_state.get("logged_in", False):
    login_page()
    st.stop()


def sidebar():
    """Navigasi utama dan informasi akun."""
    with st.sidebar:
        st.title("🎧 Music PlaylistPas")
        st.caption("Cari musik, susun playlist, lalu dengarkan.")
        st.divider()

        halaman = st.radio(
            "Navigasi",
            [HALAMAN_TEMUKAN, HALAMAN_ANALISIS],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption(f"Akun: **{st.session_state.get('username', '')}**")
        ganti_password_form()

        if st.button("Keluar", use_container_width=True):
            logout()
            st.rerun()

        st.caption("Video musik disediakan oleh YouTube.")

    return halaman


HALAMAN = {
    HALAMAN_TEMUKAN: temukan.tampil,
    HALAMAN_ANALISIS: analisis.tampil,
}

pilihan = sidebar()
HALAMAN[pilihan]()
