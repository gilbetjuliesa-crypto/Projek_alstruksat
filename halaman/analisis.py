"""Halaman 2: Analisis & Ekspor."""
import matplotlib.pyplot as plt
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO

MIME_XLSX = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def _tampilkan_grafik(fig):
    st.pyplot(fig)
    plt.close(fig)


def tampil():
    st.header("📊 Analisis dan Ekspor Playlist")

    playlist = st.session_state.playlist
    if not playlist:
        st.info("Buat playlist terlebih dahulu agar analisis " "dan ekspor dapat ditampilkan.")
        return

    df = buat_dataframe(playlist)
    tampilkan_ringkasan(playlist, st.session_state.target_menit)

    st.subheader("📋 Data Lagu")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("📊 Durasi Setiap Lagu")
    _tampilkan_grafik(grafik_durasi_lagu(df))

    st.subheader("📈 Akumulasi Durasi vs Target")
    _tampilkan_grafik(grafik_akumulasi(playlist, st.session_state.target_menit))

    st.divider()
    st.subheader("📥 Ekspor Playlist")
    _tombol_ekspor(playlist, df)


"""Dua visualisasi Matplotlib sesuai proposal (bagian 2.6)."""
def grafik_durasi_lagu(df):
    """Visualisasi 1: bar chart horizontal durasi setiap lagu."""
    n = len(df)
    fig, ax = plt.subplots(figsize=(10, max(3, 0.45 * n + 1)))

    # Posisi numerik + nomor urut: judul yang sama tidak saling menimpa.
    label = [f"{no}. {judul[:35]}" for no, judul in zip(df["No"], df["Judul Lagu"].astype(str))]

    ax.barh(range(n), df["Durasi (menit)"])
    ax.set_yticks(range(n))
    ax.set_yticklabels(label)
    ax.invert_yaxis()
    ax.set_title("Durasi Setiap Lagu")
    ax.set_xlabel("Durasi (menit)")
    fig.tight_layout()
    return fig


def grafik_akumulasi(playlist, target_menit):
    """Visualisasi 2: line chart akumulasi durasi vs target durasi."""
    detik = pd.Series([int(lagu.get("durasi_detik", 0)) for lagu in playlist])

    kumulatif = detik.cumsum() / 60
    urutan = range(1, len(kumulatif) + 1)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(urutan, kumulatif, marker="o", label="Akumulasi durasi playlist")
    ax.axhline(target_menit, color="red", linestyle="--", label=f"Target ({target_menit} menit)",)
        
    ax.set_title("Akumulasi Durasi Playlist vs Target")
    ax.set_xlabel("Lagu ke-")
    ax.set_ylabel("Durasi kumulatif (menit)")
    ax.set_xticks(list(urutan))
    ax.legend()
    fig.tight_layout()
    return fig


"""Ekspor playlist ke CSV, Excel, dan JSON."""
KOLOM_LAGU = (
    "No", "Judul Lagu", "Artis / Channel", "Durasi", "Durasi (menit)",
    "Wilayah Pencarian", "Genre", "Link YouTube", "Video ID",
)

def buat_dataframe(playlist):
    # Setiap baris berupa tuple (urutan sama dengan KOLOM_LAGU).
    rows = [
        (
            no,
            lagu.get("judul", ""),
            lagu.get("artis", ""),
            format_durasi(lagu.get("durasi_detik", 0)),
            round(lagu.get("durasi_detik", 0) / 60, 2),
            lagu.get("negara_pencarian", ""),
            lagu.get("genre", ""),
            lagu.get("tautan", ""),
            lagu.get("id", ""),
        )
        for no, lagu in enumerate(playlist, start=1)
    ]
    return pd.DataFrame(rows, columns=list(KOLOM_LAGU))

def buat_file_excel(playlist, nama, kegiatan, target_menit, alasan):
    buffer = BytesIO()
    ringkasan = pd.DataFrame(
        [(
            nama,
            kegiatan,
            target_menit,
            round(total_durasi(playlist) / 60, 2),
            len(playlist),
            alasan,
            datetime.now().isoformat(timespec="seconds"),
        )],
        columns=[
            "Nama Playlist", "Kegiatan", "Target Durasi (menit)",
            "Durasi Aktual (menit)", "Jumlah Video", "Keterangan",
            "Dibuat Pada",
        ],
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        ringkasan.to_excel(writer, sheet_name="Ringkasan", index=False)
        buat_dataframe(playlist).to_excel(
            writer, sheet_name="Daftar Lagu", index=False
        )

    return buffer.getvalue()

def buat_data_json(playlist, nama, kegiatan, target_menit, alasan):
    data = {
        "nama_playlist": nama,
        "kegiatan": kegiatan,
        "target_durasi_menit": target_menit,
        "durasi_aktual_detik": total_durasi(playlist),
        "jumlah_video": len(playlist),
        "keterangan": alasan,
        "dibuat_pada": datetime.now().isoformat(timespec="seconds"),
        "lagu": playlist,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _tombol_ekspor(playlist, df):
    s = st.session_state
    nama_file = (s.nama_playlist or "music_playlist").lower().replace(" ", "_")
    args = (playlist, s.nama_playlist, s.kegiatan, s.target_menit, s.alasan_ai)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "⬇️ Unduh CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        f"{nama_file}.csv",
        "text/csv",
        use_container_width=True,
    )
    c2.download_button(
        "⬇️ Unduh Excel",
        buat_file_excel(*args),
        f"{nama_file}.xlsx",
        MIME_XLSX,
        use_container_width=True,
    )
    c3.download_button(
        "⬇️ Unduh JSON",
        buat_data_json(*args).encode("utf-8"),
        f"{nama_file}.json",
        "application/json",
        use_container_width=True,
    )