import streamlit as st
import pandas as pd
import numpy as np

# 1. Pengaturan Halaman Web
st.set_page_config(page_title="SPK Daya Saing UMKM Minuman", layout="wide")
st.title("🥤 Sistem Pendukung Keputusan Strategi Penjualan UMKM Minuman")
st.write("Integrasi Metode **RFM (Recency, Frequency, Monetary)** dan **SAW (Simple Additive Weighting)**")

# 2. Menu Upload Data Transaksi
st.sidebar.header("1. Input Data Penjualan")
uploaded_file = st.sidebar.file_uploader("Upload File Excel Transaksi (.xlsx)", type=["xlsx"])

# Buat data contoh otomatis jika belum upload file
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
else:
    st.info("Menampilkan data simulasi bawaan. Silakan upload file 'data_penjualan.xlsx' di menu kiri untuk menguji data lengkap.")
    df = pd.DataFrame({
        'ID_Pelanggan': ['P01', 'P02', 'P03', 'P01', 'P04', 'P02', 'P05', 'P01', 'P03', 'P06'],
        'Tanggal': pd.to_datetime(['2026-11-01', '2026-11-05', '2026-10-10', '2026-11-18', '2026-09-15',
                                   '2026-11-20', '2026-11-21', '2026-11-22', '2026-10-25', '2026-08-12']),
        'Total_Belanja': [25000, 40000, 15000, 30000, 12000, 50000, 18000, 35000, 20000, 10000]
    })

# ==========================================
# TAHAP A: PERHITUNGAN METODE RFM
# ==========================================
st.subheader("📊 Tahap 1: Segmentasi Pelanggan (Metode RFM)")
tanggal_acuan = df['Tanggal'].max() + pd.Timedelta(days=1)

rfm = df.groupby('ID_Pelanggan').agg({
    'Tanggal': lambda x: (tanggal_acuan - x.max()).days, # Recency
    'ID_Pelanggan': 'count',                             # Frequency
    'Total_Belanja': 'sum'                               # Monetary
}).rename(columns={'Tanggal': 'Recency', 'ID_Pelanggan': 'Frequency', 'Total_Belanja': 'Monetary'})

# Pemberian Skor 1-3 (Sederhana)
rfm['R_Score'] = pd.qcut(rfm['Recency'].rank(method='first'), 3, labels=[3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 3, labels=[1, 2, 3]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 3, labels=[1, 2, 3]).astype(int)
rfm['Total_Skor_RFM'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

def kategori_pelanggan(skor):
    if skor >= 7:
        return "Pelanggan Loyal (VIP)"
    elif skor >= 5:
        return "Pelanggan Potensial"
    else:
        return "Pelanggan Pasif (Berisiko Pergi)"

rfm['Segmen'] = rfm['Total_Skor_RFM'].apply(kategori_pelanggan)

col1, col2 = st.columns(2)
with col1:
    st.dataframe(rfm, use_container_width=True)
with col2:
    st.bar_chart(rfm['Segmen'].value_counts())

# ==========================================
# TAHAP B: PERHITUNGAN METODE SAW
# ==========================================
st.subheader("🏆 Tahap 2: Rekomendasi Strategi Penjualan (Metode SAW)")

# Pengaturan Bobot Kriteria Dinamis di Sidebar
st.sidebar.header("2. Pengaturan Bobot Kriteria SAW")
w_biaya = st.sidebar.slider("Bobot Biaya Promosi (Cost)", 0.1, 0.5, 0.25)
w_omzet = st.sidebar.slider("Bobot Potensi Kenaikan Omzet (Benefit)", 0.1, 0.5, 0.35)
w_retensi = st.sidebar.slider("Bobot Retensi Pelanggan (Benefit)", 0.1, 0.5, 0.25)
w_mudah = st.sidebar.slider("Bobot Kemudahan Eksekusi (Benefit)", 0.1, 0.5, 0.15)

# Data Alternatif Strategi Penjualan UMKM Minuman
strategi = pd.DataFrame({
    'Alternatif_Strategi': [
        'Promo Bundling (Beli 2 Gratis 1)',
        'Voucher Cashback Pelanggan Loyal',
        'Rilis Varian Rasa Musiman Baru',
        'Iklan Konten Video Lokal (TikTok/Reels)'
    ],
    'Biaya': [4, 3, 5, 2],       # Cost (Semakin kecil semakin baik)
    'Omzet': [5, 4, 5, 4],       # Benefit (Semakin besar semakin baik)
    'Retensi': [4, 5, 3, 3],     # Benefit
    'Kemudahan': [5, 4, 2, 4]    # Benefit
})

# Normalisasi Matriks SAW
norm = strategi.copy()
norm['Biaya'] = strategi['Biaya'].min() / strategi['Biaya']           # Rumus Cost
norm['Omzet'] = strategi['Omzet'] / strategi['Omzet'].max()           # Rumus Benefit
norm['Retensi'] = strategi['Retensi'] / strategi['Retensi'].max()     # Rumus Benefit
norm['Kemudahan'] = strategi['Kemudahan'] / strategi['Kemudahan'].max() # Rumus Benefit

# Hitung Nilai Preferensi (V) & Ranking
strategi['Nilai_SAW'] = (
    (norm['Biaya'] * w_biaya) +
    (norm['Omzet'] * w_omzet) +
    (norm['Retensi'] * w_retensi) +
    (norm['Kemudahan'] * w_mudah)
).round(4)

strategi['Ranking'] = strategi['Nilai_SAW'].rank(ascending=False).astype(int)
hasil_akhir = strategi.sort_values(by='Ranking')

st.dataframe(hasil_akhir, use_container_width=True)
st.success(f"💡 **Rekomendasi Utama:** Jalankan strategi **{hasil_akhir.iloc[0]['Alternatif_Strategi']}** dengan skor tertinggi **{hasil_akhir.iloc[0]['Nilai_SAW']}**.")