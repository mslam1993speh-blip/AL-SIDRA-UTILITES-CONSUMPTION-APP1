import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from fpdf import FPDF
import base64

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Sidra Intelligence", layout="wide")
st.markdown("<style>.stMetric { background-color: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

# --- نظام اللغة ---
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
t = {
    'Arabic': {'all': "السنة كاملة", 'summary': "📋 مؤشرات الكفاءة", 'pdf': "📄 تحميل تقرير PDF احترافي", 'base': "📉 خطوط الأساس (العطل والجمع)"},
    'English': {'all': "Full Year", 'summary': "📋 Efficiency KPIs", 'pdf': "📄 Download Pro PDF Report", 'base': "📉 Baselines (Fridays & Offs)"}
}
l = t[st.session_state.lang]

# --- Sidebar ---
with st.sidebar:
    try: st.image("al sidra new.jpg", use_container_width=True)
    except: st.title("AL-SIDRA")
    if st.button("Switch Language"):
        st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'
        st.rerun()
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
    prod_qty = st.number_input("Monthly Production (KG)", min_value=1.0, value=150000.0)

# --- معالجة البيانات ---
if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        dfs = [xl.parse(s).assign(MONTH=s) for s in xl.sheet_names]
        df_full = pd.concat(dfs, ignore_index=True)
        df_full.columns = [str(c).strip().upper() for c in df_full.columns]
        
        sel_month = st.selectbox("Select Period", [l['all']] + list(df_full['MONTH'].unique()))
        df = df_full if sel_month == l['all'] else df_full[df_full['MONTH'] == sel_month]

        # دالة جلب البيانات الآمنة (حل مشكلة TypeError)
        def safe_get(keys):
            found_col = next((c for c in df.columns if any(k in c for k in keys)), None)
            if found_col is not None:
                return pd.to_numeric(df[found_col], errors='coerce').fillna(0)
            return pd.Series([0.0] * len(df))

        df['ELEC'] = safe_get(['ELEC', 'كهرباء'])
        df['LPG'] = safe_get(['LPG', 'غاز'])
        df['W_IN'] = safe_get(['WATER REC', 'وارد'])
        df['W_OUT'] = safe_get(['SANIT', 'صرف'])

        # --- الحسابات المنطقية ---
        days = len(df) if len(df) > 0 else 1
        avg_daily_prod = prod_qty / 30
        kpi_elec = (df['ELEC'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0
        kpi_lpg = (df['LPG'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0

        # --- ذكاء الـ Baseline (الجمعة + العطل) ---
        df['DATE_DT'] = pd.to_datetime(df.get('DATE', df.index), errors='coerce')
        # العطلة: إما يوم جمعة أو استهلاك كهرباء أقل من 40% من المتوسط
        off_days = df[(df['DATE_DT'].dt.day_name() == 'Friday') | (df['ELEC'] < df['ELEC'].mean() * 0.4)]
        base_elec = off_days['ELEC'].mean() if not off_days.empty else 0

        # --- العرض ---
        st.subheader(l['summary'])
        c1, c2, c3 = st.columns(3)
        c1.metric("Electricity/KG", f"{kpi_elec:.3f} kWh/kg")
        c2.metric("LPG/KG", f"{kpi_lpg:.4f} kg/kg")
        c3.metric("Friday & Off Baseline", f"{base_elec:,.0f} kWh")

        st.plotly_chart(px.line(df, y=['ELEC', 'LPG'], title="Daily Trends"), use_container_width=True)

        # --- التقرير الجذاب PDF ---
        if st.button(l['pdf']):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(190, 10, "AL-SIDRA UTILITIES REPORT", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(95, 10, "Elec Efficiency:", 1); pdf.cell(95, 10, f"{kpi_elec:.3f} kWh/kg", 1, 1)
            pdf.cell(95, 10, "Holiday Baseline:", 1); pdf.cell(95, 10, f"{base_elec:,.0f} kWh", 1, 1)
            
            pdf_data = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_data).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Report.pdf" style="background:red; color:white; padding:10px; border-radius:5px; text-decoration:none;">📥 Download PDF Report</a>', unsafe_allow_html=True)

    except Exception as e: st.error(f"Error Detail: {e}")
else: st.info("Waiting for Excel file...")  
