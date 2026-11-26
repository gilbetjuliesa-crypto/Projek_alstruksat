# Music PlaylistPas

Aplikasi playlist musik berbasis Streamlit. Pengguna dapat mencari video musik dari YouTube, memperoleh penilaian kandidat dari Gemini AI, menyusun lagu dengan algoritma Greedy, mendengarkan melalui YouTube Player, melihat analisis, dan mengunduh playlist.

## Fitur

1. Pengaturan wilayah, genre, kata kunci, kegiatan, dan target durasi.
2. Pencarian video musik menggunakan YouTube Data API v3.
3. Penilaian kandidat dan rekomendasi personal menggunakan Gemini AI.
4. Pemilihan serta penyusunan lagu menggunakan algoritma Greedy.
5. Mengubah urutan dan menghapus lagu dari playlist.
6. Pemutar YouTube dengan lanjut otomatis dan pencatatan riwayat.
7. Analisis data dan visualisasi durasi menggunakan Pandas dan Matplotlib.
8. Ekspor playlist ke CSV, Excel, dan JSON.

## Struktur project

```text
MusicPlaylistPas/
├── app.py
├── config.py
├── login.py
├── playlist.py
├── akun.json
├── riwayat.json
├── halaman/
│   ├── __init__.py
│   ├── temukan.py
│   └── analisis.py
├── services/
│   ├── __init__.py
│   ├── youtube_api.py
│   ├── gemini_api.py
│   └── riwayat.py
├── ui/
│   ├── __init__.py
│   ├── daftar_lagu.py
│   ├── player.py
│   └── youtube_player/
│       └── index.html
├── .streamlit/
│   └── secrets.toml.example
└── requirements.txt
```

## Instalasi

Gunakan Python 3.10 atau lebih baru.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Instal dependensi:

```bash
pip install -r requirements.txt
```

Buat file `.streamlit/secrets.toml` berdasarkan `secrets.toml.example`, kemudian isi API key:

```toml
YOUTUBE_API_KEY = "API_KEY_YOUTUBE"
GEMINI_API_KEY = "API_KEY_GEMINI"
```

Jalankan aplikasi:

```bash
streamlit run app.py
```

## Catatan

- Riwayat disimpan pada `riwayat.json` dan dipisahkan berdasarkan akun.
- Sesi pemutaran dicatat setelah lagu didengarkan minimal 30 detik.
- Riwayat digunakan sebagai konteks rekomendasi Gemini, bukan untuk melatih ulang model.
- `regionCode` YouTube merupakan petunjuk wilayah hasil pencarian, bukan bukti negara asal artis.
- Pemutar hanya memainkan video YouTube yang mengizinkan pemutaran melalui embed.
- Jika Gemini mengalami gangguan sementara, aplikasi tetap dapat membuat playlist dengan algoritma Greedy tanpa penilaian AI.
- Jangan membagikan file `secrets.toml` atau API key.
