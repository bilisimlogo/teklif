import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from base64 import b64encode

# SQLite veritabanına bağlan
conn = sqlite3.connect('teklifler.db')
cursor = conn.cursor()

# Müşteri tablosunu oluştur
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Musteri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firma_adi TEXT,
        durum TEXT,
        telefon TEXT,
        email TEXT
    )
''')

# Teklif tablosunu oluştur
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Teklif (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id INTEGER,
        teklif_icerik TEXT,
        teklif_tutari REAL,
        FOREIGN KEY (musteri_id) REFERENCES Musteri(id)
    )
''')

# Yeni müşteri oluşturmak için fonksiyon


def musteri_olustur():
    st.subheader("Müşteri Oluştur")

    firma_adi = st.text_input("Firma Adı:")
    durum = st.text_input("Durum:")
    telefon = st.text_input("Telefon:")
    email = st.text_input("Email:")

    if st.button("Müşteri Oluştur"):
        cursor.execute('''
            INSERT INTO Musteri (firma_adi, durum, telefon, email)
            VALUES (?, ?, ?, ?)
        ''', (firma_adi, durum, telefon, email))
        conn.commit()
        st.success("Müşteri başarıyla oluşturuldu.")

# Yeni teklif oluşturmak için fonksiyon


def teklif_olustur():
    st.subheader("Teklif Oluştur")

    musteriler = cursor.execute(
        'SELECT id, firma_adi FROM Musteri').fetchall()
    musteri_id = st.selectbox("Müşteri Seç:", musteriler)
    teklif_icerik = st.text_area("Teklif İçeriği:")
    teklif_tutari = st.number_input("Teklif Tutarı:")

    if st.button("Teklif Oluştur"):
        cursor.execute('''
            INSERT INTO Teklif (musteri_id, teklif_icerik, teklif_tutari)
            VALUES (?, ?, ?)
        ''', (musteri_id[0], teklif_icerik, teklif_tutari))
        conn.commit()
        st.success("Teklif başarıyla oluşturuldu.")

# Mevcut teklifleri görüntülemek için fonksiyon

# Tüm teklifler için PDF oluşturmak için fonksiyon


def teklifleri_goruntule():
    st.subheader("Teklifleri Görüntüle")

    teklifler = cursor.execute('''
        SELECT t.id, m.firma_adi, t.teklif_icerik, t.teklif_tutari
        FROM Teklif t
        JOIN Musteri m ON t.musteri_id = m.id
    ''').fetchall()

    if not teklifler:
        st.info("Henüz hiç teklif yok.")
    else:
        # Belirli bir teklifi seçmek için bir açılır kutu görüntüle
        secilen_teklif_id = st.selectbox(
            "Teklif Seç:", [teklif[0] for teklif in teklifler])

        # Seçilen teklifin detaylarını bul
        secilen_teklif = next(
            (teklif for teklif in teklifler if teklif[0] == secilen_teklif_id), None)

        if secilen_teklif:
            st.write(f"Firma Adı: {secilen_teklif[1]}")
            st.write(f"Teklif ID: {secilen_teklif[0]}")
            st.write(f"Teklif İçeriği: {secilen_teklif[2]}")
            st.write(f"Teklif Tutarı: {secilen_teklif[3]:,.2f}")

            # Seçilen teklif için PDF oluşturmak için bir düğme oluştur
            pdf_olustur_buton_anahtari = f"pdf_olustur_buton_{secilen_teklif[0]}"
            if st.button(f"Seçilen Teklif İçin PDF Oluştur", key=pdf_olustur_buton_anahtari):
                pdf_buffer = teklif_pdf_olustur(secilen_teklif)
                st.markdown(get_binary_file_downloader_html(
                    pdf_buffer, f"teklif_{secilen_teklif[0]}.pdf"), unsafe_allow_html=True)


def teklif_pdf_olustur(teklif):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)

    # Helvetica fontunu kullanarak düzelme
    c.setFont("Helvetica", 12)

    # Seçilen teklif için bilgileri PDF'ye ekle
    text_lines = [
        f"Firma Adı: {teklif[1]}",
        f"Teklif ID: {teklif[0]}",
        f"Teklif İçeriği: {teklif[2]}",
        f"Teklif Tutarı: {teklif[3]:,.2f}",
        "--------------------------------------"
    ]

    # Belirli bir konumdan başlayarak metni çizmek
    y_position = 750
    line_height = 14  # Satır yüksekliği
    for line in text_lines:
        c.drawString(100, y_position, line)
        y_position -= 2 * line_height  # 2 satır aralığı bırak

    c.save()

    return pdf_buffer


def musteri_listesi():
    st.subheader("Müşteri Listesi")

    # Tüm müşteri verilerini getirmek için sorgu
    sorgu = 'SELECT * FROM Musteri'
    musteriler_df = pd.read_sql_query(sorgu, conn)

    # DataFrame'i görüntüle
    st.dataframe(musteriler_df)

# Müşteri detaylarını düzenlemek için fonksiyon


def musteri_listesi_duzenle():
    st.subheader("Müşteri Listesini Düzenle")

    # Tüm müşteri verilerini getirmek için sorgu
    sorgu = 'SELECT * FROM Musteri'
    musteriler_df = pd.read_sql_query(sorgu, conn)

    # DataFrame'i görüntüle
    st.dataframe(musteriler_df)

    # Düzenlenecek müşteriyi seçmek için bir seçim kutusu ekleyin
    secilen_musteri_id = st.selectbox(
        "Düzenlenecek Müşteriyi Seç", musteriler_df['id'])

    # Seçilen müşterinin detaylarını görüntüle
    secilen_musteri_verisi = musteriler_df[musteriler_df['id']
                                           == secilen_musteri_id]
    st.write(f"Seçilen Müşteri Detayları:")
    st.write(secilen_musteri_verisi)

    # Kullanıcıya detayları düzenleme izni ver
    duzenlenen_firma_adi = st.text_input(
        "Düzenlenen Firma Adı:", secilen_musteri_verisi['firma_adi'].values[0])
    duzenlenen_durum = st.text_input(
        "Düzenlenen Durum:", secilen_musteri_verisi['durum'].values[0])
    duzenlenen_telefon = st.text_input(
        "Düzenlenen Telefon:", secilen_musteri_verisi['telefon'].values[0])
    duzenlenen_email = st.text_input(
        "Düzenlenen Email:", secilen_musteri_verisi['email'].values[0])

    # Değişiklikleri kaydetmek için düğme
    if st.button("Değişiklikleri Kaydet"):
        cursor.execute('''
            UPDATE Musteri
            SET firma_adi=?, durum=?, telefon=?, email=?
            WHERE id=?
        ''', (duzenlenen_firma_adi, duzenlenen_durum,
              duzenlenen_telefon, duzenlenen_email, secilen_musteri_id))
        conn.commit()
        st.success("Müşteri detayları başarıyla güncellendi.")

# Bir teklif için PDF oluşturmak için fonksiyon


def pdf_olustur(teklif):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)

    # Helvetica fontunu kullanarak düzelme
    c.setFont("Helvetica", 12)

    # Metin çizimi
    text_lines = [
        f"Firma Adı: {teklif[1]}",
        f"Teklif ID: {teklif[0]}",
        f"Teklif İçeriği: {teklif[2]}",
        f"Teklif Tutarı: {teklif[3]:,.2f}",
        "--------------------------------------"
    ]

    # Belirli bir konumdan başlayarak metni çizmek
    y_position = 750
    line_height = 14  # Satır yüksekliği
    for line in text_lines:
        c.drawString(100, y_position, line)
        y_position -= 2 * line_height  # 2 satır aralığı bırak

    c.save()

    return pdf_buffer

# Bin dosyası indirme için HTML'i almak için fonksiyon


def get_binary_file_downloader_html(bin_file, file_label='Dosya'):
    bin_str = bin_file.getvalue()
    data_url = f"data:application/pdf;base64,{b64encode(bin_str).decode()}"
    html = f'<a href="{data_url}" download="{file_label}.pdf">PDF İndir</a>'
    return html


# Sayfaları oluştur
sayfa = st.sidebar.selectbox(
    "Sayfa Seç:", ["Müşteri Oluştur", "Teklif Oluştur", "Teklifleri Görüntüle", "Müşteri Listesi", "Müşteri Listesini Düzenle"])

if sayfa == "Müşteri Oluştur":
    musteri_olustur()
elif sayfa == "Teklif Oluştur":
    teklif_olustur()
elif sayfa == "Teklifleri Görüntüle":
    teklifleri_goruntule()
elif sayfa == "Müşteri Listesi":
    musteri_listesi()
elif sayfa == "Müşteri Listesini Düzenle":
    musteri_listesi_duzenle()

# SQLite veritabanı bağlantısını kapat
conn.close()
