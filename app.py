# app.py
# Versi Profesional dengan UI/UX yang disempurnakan.

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# --- Fungsi Inti (Tidak berubah) ---
def calculate_standard_ma(percentage: float) -> float:
    return 4.0 + (percentage / 100.0) * 16.0

def style_error(v):
    if abs(v) < 1.0: color = 'green'
    elif abs(v) < 2.0: color = 'orange'
    else: color = 'red'
    return f'color: {color}; font-weight: bold;'

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="ProCalibrator",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inisialisasi Session State ---
if 'kalibrasi_dimulai' not in st.session_state:
    st.session_state.kalibrasi_dimulai = False
if 'hasil_tersimpan' not in st.session_state:
    st.session_state.hasil_tersimpan = None

# --- Header Aplikasi ---
st.title("🎛️ ProCalibrator")
st.markdown("###### Aplikasi Kalibrasi Transmitter Cerdas dengan Laporan Interaktif")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Kalibrasi")
    
    transmitter_types = ["Pressure", "Level", "Temperature", "Flow", "Differential Pressure"]
    tipe_transmitter = st.selectbox("Tipe Transmitter", transmitter_types, key="tipe_transmitter")
    tag_item = st.text_input("Nama Tag Item (e.g., PT-101A)", key="tag_item").upper()
    lrv = st.number_input("Lower Range Value (LRV)", format="%.3f", key="lrv")
    urv = st.number_input("Upper Range Value (URV)", value=100.0, format="%.3f", key="urv")
    unit = st.text_input("Unit Pengukuran (e.g., Bar, °C, %)", "Bar", key="unit")
    max_allowable_error = st.number_input("Error Maksimum yang Diizinkan (%)", 0.0, 10.0, 2.0, 0.1, format="%.1f")

    if st.button("▶️ Mulai Kalibrasi", use_container_width=True, type="primary"):
        if not tag_item:
            st.warning("Nama Tag Item wajib diisi.")
        elif urv <= lrv:
            st.error("URV harus lebih besar dari LRV.")
        else:
            st.session_state.kalibrasi_dimulai = True
            st.session_state.hasil_tersimpan = None
            st.session_state.info = {
                "type": st.session_state.tipe_transmitter, "tag": st.session_state.tag_item,
                "lrv": st.session_state.lrv, "urv": st.session_state.urv,
                "unit": st.session_state.unit, "max_error": max_allowable_error
            }

    st.divider()
    st.markdown("###### Dibuat dengan [Streamlit](https://streamlit.io)")


# --- Tampilan Utama ---
if not st.session_state.kalibrasi_dimulai:
    st.info("⬅️ **Selamat Datang!** Silakan isi konfigurasi di sidebar kiri untuk memulai.")
else:
    info = st.session_state.info
    with st.container(border=True):
        st.header(f"📝 Form Pengukuran: {info['tag']}")
        st.caption(f"**Range:** `{info['lrv']}` s/d `{info['urv']}` **{info['unit']}** | **Tipe:** `{info['type']}`")
        
        with st.form("kalibrasi_form"):
            col1, col2 = st.columns(2)
            calibration_points = [0, 25, 50, 75, 100]
            span = info['urv'] - info['lrv']

            with col1:
                st.subheader("⬆️ Proses Naik")
                for p in calibration_points:
                    pv = info['lrv'] + (p / 100.0) * span
                    st.number_input(f"{p}% ({pv:,.2f} {info['unit']})", key=f"naik_{p}", value=None, placeholder="Input mA...", format="%.3f")
            
            with col2:
                st.subheader("⬇️ Proses Turun")
                for p in reversed(calibration_points):
                    pv = info['lrv'] + (p / 100.0) * span
                    st.number_input(f"{p}% ({pv:,.2f} {info['unit']})", key=f"turun_{p}", value=None, placeholder="Input mA...", format="%.3f")

            submitted = st.form_submit_button("📊 Proses & Buat Laporan", use_container_width=True)

            if submitted:
                results_data = []
                for p in calibration_points:
                    if (meas_ma := st.session_state[f'naik_{p}']) is not None:
                        std_ma = calculate_standard_ma(p)
                        error = ((meas_ma - std_ma) / 16.0) * 100.0
                        results_data.append({"Proses": "Naik", "Titik (%)": p, "Nilai Proses (PV)": info['lrv'] + (p / 100.0) * span, "Std (mA)": std_ma, "Ukur (mA)": meas_ma, "Error (%)": error})
                
                for p in reversed(calibration_points):
                    if (meas_ma := st.session_state[f'turun_{p}']) is not None:
                        std_ma = calculate_standard_ma(p)
                        error = ((meas_ma - std_ma) / 16.0) * 100.0
                        results_data.append({"Proses": "Turun", "Titik (%)": p, "Nilai Proses (PV)": info['lrv'] + (p / 100.0) * span, "Std (mA)": std_ma, "Ukur (mA)": meas_ma, "Error (%)": error})
                
                st.session_state.hasil_tersimpan = pd.DataFrame(results_data)

# --- Tampilan Hasil ---
if st.session_state.hasil_tersimpan is not None:
    with st.container(border=True):
        st.header("📈 Laporan Hasil Kalibrasi")
        
        info = st.session_state.info
        df_results = st.session_state.hasil_tersimpan
        max_error = df_results['Error (%)'].abs().max()

        # Kartu Hasil / Metrics Card
        verdict = "LULUS" if max_error <= info['max_error'] else "GAGAL"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Tag Item:** {info['tag']}", icon="🏷️")
        with col2:
            st.info(f"**Tanggal:** {datetime.now().strftime('%Y-%m-%d')}", icon="📅")
        with col3:
            if verdict == "LULUS":
                st.success(f"**Verdict: {verdict}**", icon="✅")
            else:
                st.error(f"**Verdict: {verdict}**", icon="❌")
        
        # Expander untuk menyembunyikan detail
        with st.expander("Lihat Detail Tabel dan Grafik Interaktif", expanded=True):
            st.subheader("Tabel Hasil")
            st.dataframe(df_results.style.applymap(style_error, subset=['Error (%)']).format(formatter={
                'Nilai Proses (PV)': '{:,.3f}', 'Std (mA)': '{:.3f}', 'Ukur (mA)': '{:.3f}', 'Error (%)': '{:+.3f}%'
            }), use_container_width=True, hide_index=True)
            st.metric(label="⚠️ Error Maksimum Tercatat", value=f"{max_error:.3f}%")

            st.subheader("Grafik Linearitas & Histeresis")
            df_naik = df_results[df_results['Proses'] == 'Naik']
            df_turun = df_results[df_results['Proses'] == 'Turun']

            # Membuat grafik dengan Plotly
            fig = go.Figure()
            # Garis Standar Ideal
            fig.add_trace(go.Scatter(x=df_naik['Nilai Proses (PV)'], y=df_naik['Std (mA)'], mode='lines+markers', name='Standar Ideal', line=dict(color='gray', dash='dash'), marker=dict(symbol='x')))
            # Garis Pengukuran Naik
            fig.add_trace(go.Scatter(x=df_naik['Nilai Proses (PV)'], y=df_naik['Ukur (mA)'], mode='lines+markers', name='Ukur (Naik)', marker=dict(symbol='triangle-up', color='blue')))
            # Garis Pengukuran Turun
            fig.add_trace(go.Scatter(x=df_turun['Nilai Proses (PV)'], y=df_turun['Ukur (mA)'], mode='lines+markers', name='Ukur (Turun)', marker=dict(symbol='triangle-down', color='green')))

            fig.update_layout(
                title=f"<b>Grafik Kalibrasi - {info['tag']}</b>",
                xaxis_title=f"Nilai Proses ({info['unit']})",
                yaxis_title="Sinyal Output (mA)",
                legend_title="Legenda",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
