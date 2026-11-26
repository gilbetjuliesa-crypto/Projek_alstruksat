"""Autentikasi untuk aplikasi Streamlit: login, daftar, ganti password, logout.

- Password di-hash dengan scrypt + salt acak per akun (hanya library standar).
- Akun format lama (SHA-256) tetap bisa login dan otomatis di-upgrade ke scrypt.
- Username tidak membedakan huruf besar/kecil ("Gege" == "gege").
- Percobaan login gagal dibatasi per username (kunci sementara).
- Penyimpanan atomik ke akun.json agar file tidak rusak saat tulis bersamaan.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
import time
from pathlib import Path

import streamlit as st

from config import kosongkan_playlist

FILE_AKUN = Path(__file__).with_name("akun.json")
POLA_USERNAME = re.compile(r"^[A-Za-z0-9._]{3,20}$")
MIN_PASSWORD = 8
MAKS_GAGAL = 5   # percobaan gagal sebelum dikunci
JEDA_KUNCI = 60  # lama kunci (detik)

_KUNCI = threading.Lock()
_GAGAL = {}  # username -> (jumlah gagal, waktu kunci berakhir)


# ---------------------------------------------------------------------------
# Hash password
# ---------------------------------------------------------------------------
def _scrypt(password, salt):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)


def _hash_baru(password):
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_scrypt(password, salt).hex()}"


def _cocok(akun, password):
    """Cek password terhadap catatan akun (mendukung scrypt dan SHA-256 lama)."""
    try:
        skema, *bagian = akun["sandi"].split("$")
        if skema == "scrypt":
            hitung = _scrypt(password, bytes.fromhex(bagian[0])).hex()
            return hmac.compare_digest(hitung, bagian[1])
        if skema == "sha256":  # format lama: sha256("username:password")
            hitung = hashlib.sha256(f"{akun['nama']}:{password}".encode("utf-8")).hexdigest()
            return hmac.compare_digest(hitung, bagian[0])
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return False


# ---------------------------------------------------------------------------
# Penyimpanan akun: {"username_kecil": {"nama": "Username", "sandi": "skema$..."}}
# ---------------------------------------------------------------------------
def load_users():
    try:
        data = json.loads(FILE_AKUN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, list):  # format lama: [[username, sha256hex], ...]
        users = {}
        for item in data:
            if isinstance(item, list) and len(item) == 2:
                users.setdefault(item[0].lower(), {"nama": item[0], "sandi": f"sha256${item[1]}"})
        return users
    return data if isinstance(data, dict) else {}


def _perbarui(ubah):
    """Baca-ubah-tulis akun.json secara atomik.

    `ubah(users)` mengubah dict akun dan mengembalikan pesan error (atau None).
    """
    with _KUNCI:
        users = load_users()
        if error := ubah(users):
            return error
        fd, tmp = tempfile.mkstemp(dir=FILE_AKUN.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(users, file, ensure_ascii=False, indent=2)
        os.replace(tmp, FILE_AKUN)
    return None


def _set_sandi(key, sandi):
    def ubah(users):
        if key not in users:
            return "Akun tidak ditemukan."
        users[key]["sandi"] = sandi

    return _perbarui(ubah)


# ---------------------------------------------------------------------------
# Validasi dan pembatasan percobaan gagal
# ---------------------------------------------------------------------------
def validasi_password(password, username=""):
    if len(password) < MIN_PASSWORD:
        return f"Password minimal {MIN_PASSWORD} karakter."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        return "Password harus mengandung huruf dan angka."
    if password.lower() == username.lower():
        return "Password tidak boleh sama dengan username."
    return None


def _sisa_kunci(key):
    with _KUNCI:
        return max(0, int(_GAGAL.get(key, (0, 0))[1] - time.time()))


def _catat_gagal(key):
    with _KUNCI:
        if len(_GAGAL) > 1000:  # cegah memori membengkak
            _GAGAL.clear()
        jumlah = _GAGAL.get(key, (0, 0))[0] + 1
        _GAGAL[key] = (0, time.time() + JEDA_KUNCI) if jumlah >= MAKS_GAGAL else (jumlah, 0)


# ---------------------------------------------------------------------------
# Logika (mengembalikan pesan error, atau None jika berhasil)
# ---------------------------------------------------------------------------
def masuk(username, password):
    key = username.strip().lower()
    if sisa := _sisa_kunci(key):
        return f"Terlalu banyak percobaan gagal. Coba lagi dalam {sisa} detik."

    akun = load_users().get(key)
    if akun is None:
        _hash_baru(password)  # samakan waktu proses agar username tidak bisa ditebak
    if akun is None or not _cocok(akun, password):
        _catat_gagal(key)
        return "Username atau password salah."

    if akun["sandi"].startswith("sha256$"):  # upgrade hash lama
        _set_sandi(key, _hash_baru(password))
    with _KUNCI:
        _GAGAL.pop(key, None)
    st.session_state.update(logged_in=True, username=akun["nama"])
    return None


def daftar(username, password, ulang):
    username = username.strip()
    if not POLA_USERNAME.match(username):
        return "Username 3-20 karakter: huruf, angka, titik, atau underscore."
    if password != ulang:
        return "Konfirmasi password tidak sama."
    if error := validasi_password(password, username):
        return error

    key, sandi = username.lower(), _hash_baru(password)

    def tambah(users):
        if key in users:
            return "Username sudah digunakan."
        users[key] = {"nama": username, "sandi": sandi}

    return _perbarui(tambah)


def ganti_password(lama, baru, ulang):
    username = st.session_state.get("username", "")
    akun = load_users().get(username.lower())
    if akun is None or not _cocok(akun, lama):
        return "Password lama salah."
    if baru != ulang:
        return "Konfirmasi password baru tidak sama."
    if error := validasi_password(baru, username):
        return error
    return _set_sandi(username.lower(), _hash_baru(baru))


def logout():
    st.session_state.pop("logged_in", None)
    st.session_state.pop("username", None)
    kosongkan_playlist()  # data playlist tidak terbawa ke pengguna berikutnya


# ---------------------------------------------------------------------------
# Tampilan
# ---------------------------------------------------------------------------
def login_page():
    st.title("Selamat Datang di Music PlaylistPas")

    # Setelah daftar berhasil: pindah ke Login (harus diatur sebelum pilihan dibuat).
    if st.session_state.pop("daftar_berhasil", False):
        st.session_state.update(mode_auth="Login", pesan_login="Akun berhasil dibuat. Silakan login.")
    st.session_state.setdefault("mode_auth", "Login")

    # Hanya satu form yang tampil sekaligus, jadi isian form lain otomatis kosong lagi.
    mode = st.segmented_control("Mode", ["Login", "Register"], key="mode_auth",
                                label_visibility="collapsed") or "Login"

    if mode == "Login":
        st.title("🔐 Login Akun")
        if pesan := st.session_state.pop("pesan_login", None):
            st.success(pesan)
        with st.form("form_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            kirim = st.form_submit_button("Masuk", use_container_width=True, type="primary")
        if kirim:
            if not username.strip() or not password:
                st.warning("Username dan password harus diisi.")
            elif error := masuk(username, password):
                st.error(error)
            else:
                st.rerun()
    else:
        st.title("📝 Register Akun")
        with st.form("form_daftar"):
            username_baru = st.text_input("Username")
            password_baru = st.text_input("Password", type="password")
            ulang = st.text_input("Ulangi Password", type="password")
            st.caption(f"Username 3-20 karakter (huruf, angka, . atau _). "
                       f"Password minimal {MIN_PASSWORD} karakter, ada huruf dan angka.")
            kirim = st.form_submit_button("Register", use_container_width=True)
        if kirim:
            if error := daftar(username_baru, password_baru, ulang):
                st.warning(error)
            else:
                st.session_state.daftar_berhasil = True
                st.rerun()


def ganti_password_form():
    """Tampilkan form ganti password (dipanggil dari sidebar)."""
    with st.expander("🔑 Ganti password"):
        with st.form("form_ganti_password", clear_on_submit=True):
            lama = st.text_input("Password lama", type="password")
            baru = st.text_input("Password baru", type="password")
            ulang = st.text_input("Ulangi password baru", type="password")
            kirim = st.form_submit_button("Simpan", use_container_width=True)
        if kirim:
            if error := ganti_password(lama, baru, ulang):
                st.warning(error)
            else:
                st.success("Password berhasil diganti.")
