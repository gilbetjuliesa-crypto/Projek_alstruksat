"""Halaman pencarian, rekomendasi, pemutar, dan daftar lagu."""
import streamlit as st

from config import KEGIATAN, kosongkan_playlist, simpan_playlist


def _indeks(pilihan, nilai):
    return pilihan.index(nilai) if nilai in pilihan else 0


def _form_pencarian():
    """Form dibuat ringkas agar pengaturan mudah dibaca."""
    with st.form("form_pencarian"):
        kiri, kanan = st.columns(2)

        with kiri:
            negara = st.selectbox(
                "Negara / wilayah musik",
                NAMA_NEGARA,
                index=_indeks(NAMA_NEGARA, st.session_state.negara),
            )
            genre = st.selectbox(
                "Genre musik",
                ["Semua genre", *DAFTAR_GENRE],
            )
            kata_kunci = st.text_input(
                "Artis atau judul lagu (opsional)",
                placeholder="Contoh: Tulus, NIKI, Coldplay",
            )

        with kanan:
            kegiatan = st.selectbox(
                "Kegiatan",
                KEGIATAN,
                index=_indeks(KEGIATAN, st.session_state.kegiatan),
            )
            target_menit = st.number_input(
                "Target durasi (menit)",
                min_value=5,
                max_value=600,
                value=int(st.session_state.target_menit),
                step=5,
            )
            st.caption("Playlist akan disusun mendekati durasi yang dipilih.")

        kirim = st.form_submit_button(
            "🔎 Cari dan Buat Playlist",
            type="primary",
            use_container_width=True,
        )

    if kirim:
        return negara, genre, kata_kunci, kegiatan, target_menit
    return None


def _proses_pencarian(
    negara,
    genre,
    kata_kunci,
    kegiatan,
    target_menit,
    profil_riwayat=None,
):
    if profil_riwayat is None:
        profil_riwayat = buat_profil(
            st.session_state.get("username", "")
        )

    try:
        with st.spinner("Mencari video dan menyusun playlist..."):
            hasil = susun_playlist(
                negara=negara,
                genre=genre,
                kata_kunci=kata_kunci,
                kegiatan=kegiatan,
                target_menit=target_menit,
                profil_riwayat=profil_riwayat,
            )
    except GagalSusun as exc:
        (st.error if exc.level == "error" else st.warning)(str(exc))
        return

    simpan_playlist(hasil, negara, kegiatan, target_menit)
    st.rerun()


def _tampilkan_playlist():
    playlist = st.session_state.playlist

    st.subheader("🎶 Playlist Saya")
    if not playlist:
        st.info("Playlist belum dibuat. Atur pencarian di atas untuk memulai.")
        return

    st.markdown(f"### {st.session_state.nama_playlist or 'Playlist Musik'}")
    st.caption(
        f"{st.session_state.kegiatan}  ·  "
        f"Wilayah: {st.session_state.negara}"
    )

    tampilkan_ringkasan(playlist, st.session_state.target_menit)

    if st.session_state.ai_aktif:
        st.success(
            "✨ Rekomendasi Gemini AI aktif. Gemini menilai kandidat lagu, "
            "kemudian Greedy menyusun playlist sesuai target durasi."
        )
    elif st.session_state.pesan_ai:
        st.warning(
            "Gemini AI sedang tidak tersedia. Playlist tetap dibuat "
            "menggunakan hasil YouTube dan algoritma Greedy."
        )

    if st.session_state.alasan_ai:
        with st.expander("Tentang playlist ini"):
            st.write(st.session_state.alasan_ai)
            if not st.session_state.ai_aktif and st.session_state.pesan_ai:
                st.caption(f"Informasi: {st.session_state.pesan_ai}")

    st.divider()
    tampilkan_player(playlist)

    st.divider()
    st.subheader("📃 Daftar Lagu")
    st.caption("Atur urutan lagu atau hapus lagu yang tidak diinginkan.")
    tampilkan_lagu(playlist)

    st.divider()
    if st.button("🗑️ Hapus Playlist", type="secondary"):
        kosongkan_playlist()
        st.rerun()


def _tampilkan_riwayat():
    username = st.session_state.get("username", "")
    profil = buat_profil(username)

    with st.expander("🧠 Personalisasi dan riwayat mendengarkan"):
        st.caption(
            "Riwayat lagu membantu Gemini AI memahami genre dan artis yang "
            "sering didengarkan. Riwayat digunakan sebagai konteks rekomendasi, "
            "bukan untuk melatih ulang model."
        )

        if not profil["jumlah_sesi"]:
            st.info(
                "Belum ada riwayat. Putar lagu minimal 30 detik agar "
                "preferensimu mulai tercatat."
            )
        else:
            kiri, kanan = st.columns(2)
            kiri.metric("Sesi tercatat", profil["jumlah_sesi"])
            kanan.metric(
                "Genre teratas",
                profil["genre_teratas"][0][0]
                if profil["genre_teratas"] else "Belum ada",
            )

            if profil["genre_teratas"]:
                st.caption(
                    "Genre: " + " · ".join(
                        f"{nama} ({jumlah})"
                        for nama, jumlah in profil["genre_teratas"]
                    )
                )
            if profil["artis_teratas"]:
                st.caption(
                    "Artis: " + " · ".join(
                        f"{nama} ({jumlah})"
                        for nama, jumlah in profil["artis_teratas"]
                    )
                )

            st.markdown("**Sesi terbaru**")
            for item in reversed(profil["riwayat_terbaru"]):
                st.write(
                    f"🎵 **{item.get('judul', 'Tanpa judul')}** — "
                    f"{item.get('artis', 'Tidak diketahui')}"
                )
                st.caption(
                    f"{item.get('genre', 'Genre tidak diketahui')} · "
                    f"{item.get('detik_didengarkan', 0)} detik · "
                    f"{item.get('waktu', '')}"
                )

        kiri, kanan = st.columns(2)
        with kiri:
            if st.button(
                "✨ Rekomendasi dari riwayat",
                disabled=not profil["jumlah_sesi"],
                use_container_width=True,
            ):
                genre_utama = (
                    profil["genre_teratas"][0][0]
                    if profil["genre_teratas"] else "Semua genre"
                )
                if genre_utama not in DAFTAR_GENRE:
                    genre_utama = "Semua genre"

                _proses_pencarian(
                    st.session_state.negara,
                    genre_utama,
                    "",
                    st.session_state.kegiatan,
                    int(st.session_state.target_menit),
                    profil,
                )

        with kanan:
            if st.button("Hapus riwayat", use_container_width=True):
                hapus_riwayat(username)
                st.rerun()


def tampil():
    st.title("🎧 Temukan & Dengarkan")
    st.caption(
        "Cari video musik, buat playlist sesuai suasana, dan dengarkan "
        "langsung dari pemutar YouTube."
    )

    st.subheader("🔎 Buat playlist")
    with st.expander("Bagaimana playlist dibuat?", expanded=False):
        st.write(
            "YouTube Data API mencari kandidat video. Gemini AI menilai "
            "kecocokan lagu berdasarkan preferensi dan riwayat. Algoritma "
            "Greedy memilih serta menyusun lagu agar mendekati target durasi."
        )

    input_pengguna = _form_pencarian()
    if input_pengguna:
        _proses_pencarian(*input_pengguna)

    st.divider()
    _tampilkan_playlist()
    st.divider()
    _tampilkan_riwayat()
