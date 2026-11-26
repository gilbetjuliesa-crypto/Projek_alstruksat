import streamlit as st
from copy import deepcopy

NAMA_APLIKASI = "MUSIC PLAYLISTPAS"
HALAMAN_TEMUKAN = "🎧 Temukan & Dengarkan"
HALAMAN_ANALISIS = "📊 Analisis & Ekspor"

KEGIATAN = (
    "Fokus & Produktivitas",
    "Santai & Relaksasi",
    "Olahraga & Energi",
    "Perjalanan & Berkendara",
    "Hiburan & Gaming",
    "Sosial & Perayaan",
    "Kreativitas",
    "Suasana & Mood",
)

# Tuple pasangan (key, value) menggantikan dictionary konfigurasi awal.
# Nilai list playlist tetap dibuat baru saat inisialisasi agar tidak berbagi referensi.
DEFAULT_STATE = (
    ("playlist", []),
    ("nama_playlist", ""),
    ("alasan_ai", ""),
    ("negara", "Indonesia"),
    ("kegiatan", "Santai & Relaksasi"),
    ("target_menit", 30),
    ("pesan_ai", ""),
    ("ai_aktif", False),
)

# =========================================================
# Pengelolaan Session State (data bertahan saat Streamlit rerun).
# =========================================================
def init_state():
    """Isi state awal. deepcopy mencegah list default dipakai bersama."""
    for key, value in DEFAULT_STATE:
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)

def simpan_playlist(hasil, negara, kegiatan, target_menit):
    st.session_state.playlist = hasil.playlist
    st.session_state.nama_playlist = hasil.nama
    st.session_state.alasan_ai = hasil.alasan
    st.session_state.ai_aktif = hasil.ai_aktif
    st.session_state.pesan_ai = hasil.pesan_ai
    st.session_state.negara = negara
    st.session_state.kegiatan = kegiatan
    st.session_state.target_menit = target_menit

def kosongkan_playlist():
    st.session_state.playlist = []
    st.session_state.nama_playlist = ""
    st.session_state.alasan_ai = ""
    st.session_state.pesan_ai = ""
    st.session_state.ai_aktif = False
