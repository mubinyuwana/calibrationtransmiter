# app.py
# Versi Streamlit dari skrip kalibrasi transmitter dengan tambahan grafik.

import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

def calculate_standard_ma(percentage: float) -> float:
    """
    Menghitung nilai miliampere (mA) standar berdasarkan persentase.
    Rentang standar adalah 4-20mA, dengan span 16mA.
    """
    return 4.0 + (percentage / 100.0) * 16.0

def style_error(v):
    """Memberi warna pada sel error. Hijau jika < 1%, Kuning jika < 2%, Merah jika >= 2%."""
    if abs(v) < 1.0:
        color = 'green'
    elif abs(v) < 2.0:
        color = 'orange'
    else:
        color = 'red'
    return f'color: {color}; font-weight: bold;'

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Kalibrasi Transmitter",
    page_icon="️️🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Judul Aplikasi ---
st.title("🎛️ Aplikasi Kalibrasi Transmitter 4-20mA")
st.markdown("Alat bantu untuk melakukan, mendokumentasikan, dan memvisualisasikan kalibrasi transmitter.")

# --- Inisialisasi Session State ---
if 'kalibrasi_dimulai' not in st.session_state:
    st.session_state.kalibrasi_dimulai = False
if 'hasil_tersimpan' not in st.session_state:
    st.session_state.hasil_tersimpan = None


# --- Sidebar untuk Input Data Awal ---
with st.sidebar:
    st.header("1. Informasi Transmitter")
    
    transmitter_types = ["Pressure", "Level", "Temperature", "Flow", "Differential Pressure"]
    tipe_transmitter = st.selectbox("Tipe Transmitter", transmitter_types)
    tag_item = st.text_input("Nama Tag Item (e.g., PT-101A)", "").upper()
    lrv = st.number_input("Lower Range Value (LRV)", format="%.3f")
    urv = st.number_input("Upper Range Value (URV)", value=100.0, format="%.3f")
    unit = st.text_input("Unit Pengukuran (e.g., Bar, °C, %)", "Unit")


    if st.button("▶️ Mulai Kalibrasi", use_container_width=True, type="primary"):
        if not tag_item:
            st.warning("Nama Tag Item tidak boleh kosong.")
        elif urv <= lrv:
            st.error("URV harus lebih besar dari LRV.")
        else:
            st.session_state.kalibrasi_dimulai = True
            st.session_state.hasil_tersimpan = None # Reset hasil sebelumnya
            # Simpan info ke state untuk digunakan nanti
            st.session_state.info = {
                "type": tipe_transmitter,
                "tag": tag_item,
                "lrv": lrv,
                "urv": urv,
                "unit": unit
            }


# --- Tampilan Utama Aplikasi ---

# Tampilkan form input hanya jika kalibrasi telah dimulai
if st.session_state.kalibrasi_dimulai:
    st.header(f"2. Pengukuran untuk: **{st.session_state.info['tag']}**")
    st.write(f"**Range:** `{st.session_state.info['lrv']}` s/d `{st.session_state.info['urv']}` **{st.session_state.info['unit']}**")

    calibration_points = [0, 25, 50, 75, 100]
    span = st.session_state.info['urv'] - st.session_state.info['lrv']
    
    with st.form("kalibrasi_form"):
        col1, col2 = st.columns(2)

        # --- Kolom Kalibrasi Naik ---
        with col1:
            st.subheader("Proses Naik (0% → 100%)")
            for percent in calibration_points:
                pv = st.session_state.info['lrv'] + (percent / 100.0) * span
                st.number_input(
                    f"{percent}% ({pv:,.2f} {st.session_state.info['unit']})", 
                    key=f"naik_{percent}",
                    value=None,
                    placeholder="Masukkan hasil ukur (mA)",
                    format="%.3f"
                )
        
        # --- Kolom Kalibrasi Turun ---
        with col2:
            st.subheader("Proses Turun (100% → 0%)")
            for percent in reversed(calibration_points):
                pv = st.session_state.info['lrv'] + (percent / 100.0) * span
                st.number_input(
                    f"{percent}% ({pv:,.2f} {st.session_state.info['unit']})", 
                    key=f"turun_{percent}",
                    value=None,
                    placeholder="Masukkan hasil ukur (mA)",
                    format="%.3f"
                )

        submitted = st.form_submit_button("✅ Proses & Tampilkan Hasil", use_container_width=True)

        if submitted:
            # Proses data setelah form disubmit
            results_data = []
            info = st.session_state.info
            
            # Proses Naik
            for p in calibration_points:
                meas_ma = st.session_state[f'naik_{p}']
                if meas_ma is not None:
                    std_ma = calculate_standard_ma(p)
                    error = ((meas_ma - std_ma) / 16.0) * 100.0
                    results_data.append({
                        "Proses": "Naik", "Titik (%)": p, "Nilai Proses (PV)": info['lrv'] + (p / 100.0) * (info['urv'] - info['lrv']),
                        "Std (mA)": std_ma, "Ukur (mA)": meas_ma, "Error (%)": error
                    })
            
            # Proses Turun
            for p in reversed(calibration_points):
                meas_ma = st.session_state[f'turun_{p}']
                if meas_ma is not None:
                    std_ma = calculate_standard_ma(p)
                    error = ((meas_ma - std_ma) / 16.0) * 100.0
                    results_data.append({
                        "Proses": "Turun", "Titik (%)": p, "Nilai Proses (PV)": info['lrv'] + (p / 100.0) * (info['urv'] - info['lrv']),
                        "Std (mA)": std_ma, "Ukur (mA)": meas_ma, "Error (%)": error
                    })
            
            df = pd.DataFrame(results_data)
            st.session_state.hasil_tersimpan = df


# Tampilkan hasil jika sudah ada
if st.session_state.hasil_tersimpan is not None:
    st.divider()
    st.header("3. Hasil Kalibrasi")

    info = st.session_state.info
    df_results = st.session_state.hasil_tersimpan
    max_error = df_results['Error (%)'].abs().max()

    st.markdown(f"**Tag Item:** `{info['tag']}` | **Tipe:** `{info['type']}` | **Tanggal:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}`")

    # Layout hasil: Tabel di kiri, Grafik di kanan
    col_table, col_graph = st.columns([1.5, 1])

    with col_table:
        st.subheader("Tabel Hasil")
        # Tampilkan tabel hasil dengan pewarnaan
        st.dataframe(
            df_results.style
            .applymap(style_error, subset=['Error (%)'])
            .format({
                'Nilai Proses (PV)': '{:,.3f}',
                'Std (mA)': '{:.3f}',
                'Ukur (mA)': '{:.3f}',
                'Error (%)': '{:+.3f}%'
            }),
            use_container_width=True,
            hide_index=True
        )
        st.metric(label="⚠️ Error Maksimum", value=f"{max_error:.3f}%")
        st.caption("Catatan: Error (%) dihitung dari span sinyal 16mA.")

    with col_graph:
        st.subheader("Grafik Hasil")
        
        # Pisahkan data naik dan turun untuk plot
        df_naik = df_results[df_results['Proses'] == 'Naik']
        df_turun = df_results[df_results['Proses'] == 'Turun']

        # Membuat plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Garis standar ideal
        ax.plot(df_naik['Nilai Proses (PV)'], df_naik['Std (mA)'], 'o--', color='gray', label='Standar Ideal')
        
        # Garis pengukuran naik
        ax.plot(df_naik['Nilai Proses (PV)'], df_naik['Ukur (mA)'], '^-', color='blue', label='Ukur (Naik)')
        
        # Garis pengukuran turun
        ax.plot(df_turun['Nilai Proses (PV)'], df_turun['Ukur (mA)'], 'v-', color='green', label='Ukur (Turun)')

        ax.set_title(f"Grafik Linearitas & Histeresis - {info['tag']}", fontsize=14, weight='bold')
        ax.set_xlabel(f"Nilai Proses ({info['unit']})", fontsize=12)
        ax.set_ylabel("Sinyal Output (mA)", fontsize=12)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        plt.tight_layout()

        st.pyplot(fig)

else:
    # Tampilan awal sebelum kalibrasi dimulai
    if not st.session_state.kalibrasi_dimulai:
        st.info("⬅️ Silakan isi informasi transmitter di sidebar kiri dan klik **'Mulai Kalibrasi'**.")