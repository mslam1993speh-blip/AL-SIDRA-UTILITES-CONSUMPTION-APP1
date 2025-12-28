import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from fpdf import FPDF
import base64

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Al-Sidra Dashboard", layout="wide")
st.markdown("<style>.stMetric { background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

# نظام اللغة (تصحيح خطأ all_year)
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
t = {
    'Arabic': {'all': "السنة كاملة", 'summary': "📋 مؤشرات الكفاءة والإنتاج", 'pdf': "📄 تحميل التقرير الشهري PDF"},
    'English': {'all': "Full Year", 'summary': "📋 Efficiency & Production KPIs", 'pdf': "📄 Download PDF Report"}
}
l = t[st.session_state.lang]

# --- Sidebar ---
with st.sidebar:
    try: st.image("al sidra new.jpg", use_container_width=True)
    except: st.title("AL-SIDRA")
    
    if st.button("تغيير اللغة / Switch Language"):
        st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'
        st.rerun()
    
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
    # الإنتاج الشهري المتوقع (مثلاً 150 ألف كيلو)
    prod_qty = st.number_input("Monthly Production (KG)", min_value=1.0, value=150000.0)

# --- معالجة البيانات ---
if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    dfs = [xl.parse(s).assign(MONTH=s) for s in xl.sheet_names]
    df_full = pd.concat(dfs, ignore_index=True)
    df_full.columns = [str(c).strip().upper() for c in df_full.columns]
    
    # فلترة الفترة
    months = [l['all']] + list(df_full['MONTH'].unique())
    sel_month = st.selectbox("Select Period", months)
    df = df_full if sel_month == l['all'] else df_full[df_full['MONTH'] == sel_month]
    
    # تنظيف البيانات
    for col in ['ELEC', 'LPG', 'WATER REC', 'SANIT']:
        actual_col = next((c for c in df.columns if col in c), None)
        df[col] = pd.to_numeric(df[actual_col], errors='coerce').fillna(0) if actual_col else 0

    # --- حسابات KPIs المنطقية (المتوسط اليومي) ---
    days = len(df) if len(df) > 0 else 1
    avg_daily_prod = prod_qty / 30  # متوسط الإنتاج اليومي
    
    kpi_elec = (df['ELEC'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0
    kpi_lpg = (df['LPG'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0
    water_loss = df['WATER REC'].sum() - df['SANIT'].sum()

    # عرض النتائج
    st.subheader(l['summary'])
    c1, c2, c3 = st.columns(3)
    c1.metric("Electricity/KG", f"{kpi_elec:.3f} kWh/kg") # سيظهر الآن 0.200 بدل 297
    c2.metric("LPG/KG", f"{kpi_lpg:.4f} kg/kg")
    c3.metric("Water Loss", f"{water_loss:,.0f} m³")

    # الشارتات (عادت للظهور)
    st.markdown("---")
    st.plotly_chart(px.line(df, x=df.index, y=['ELEC', 'LPG'], title="Daily Trends"), use_container_width=True)

    # وظيفة الـ PDF (مبسطة لتجنب الأخطاء)
    if st.button(l['pdf']):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, f"Utility Report - {sel_month}", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.ln(10)
        pdf.cell(95, 10, "Total Elec:", 1); pdf.cell(95, 10, f"{df['ELEC'].sum():,.0f} kWh", 1, 1)
        pdf.cell(95, 10, "Elec Efficiency:", 1); pdf.cell(95, 10, f"{kpi_elec:.3f} kWh/kg", 1, 1)
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_out).decode()
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Report.pdf">Download PDF</a>', unsafe_allow_html=True)
else:
    st.info("Waiting for data...")
