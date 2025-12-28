import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Sidra Intelligence", layout="wide")
st.markdown("<style>.stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
t = {
    'Arabic': {'title': "📊 نظام سدرة الذكي", 'summary': "📋 مؤشرات الكفاءة", 'pdf': "📄 تحميل تقرير PDF", 'all': "السنة كاملة"},
    'English': {'title': "📊 Sidra Intelligence", 'summary': "📋 Efficiency KPIs", 'pdf': "📄 Download PDF Report", 'all': "Full Year"}
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
        df_all = pd.concat(dfs, ignore_index=True)
        df_all.columns = [str(c).strip().upper() for c in df_all.columns]
        
        sel_month = st.selectbox("Select Period", [l['all']] + list(df_all['MONTH'].unique()))
        df = df_all if sel_month == l['all'] else df_all[df_all['MONTH'] == sel_month]

        # جلب الأعمدة بذكاء وحل مشكلة TypeError
        cols = {'ELEC': ['ELEC', 'كهرباء'], 'LPG': ['LPG', 'غاز'], 'W_IN': ['WATER REC', 'وارد'], 'W_OUT': ['SANIT', 'صرف']}
        for key, aliases in cols.items():
            actual = next((c for c in df.columns if any(a in c for a in aliases)), None)
            df[key] = pd.to_numeric(df[actual], errors='coerce').fillna(0) if actual is not None else 0

        # --- الحسابات المنطقية (المتوسطات) ---
        avg_daily_prod = prod_qty / 30
        days = len(df) if len(df) > 0 else 1
        
        kpi_elec = (df['ELEC'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0
        kpi_lpg = (df['LPG'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0
        w_loss = df['W_IN'].sum() - df['W_OUT'].sum()

        # --- العرض ---
        st.subheader(l['summary'])
        c1, c2, c3 = st.columns(3)
        c1.metric("Electricity/KG", f"{kpi_elec:.3f} kWh/kg") # الرقم هيطلع منطقي (0.200)
        c2.metric("LPG/KG", f"{kpi_lpg:.4f} kg/kg")
        c3.metric("Water Loss", f"{w_loss:,.0f} m³")

        st.plotly_chart(px.line(df, x=df.index, y=['ELEC', 'LPG'], title="Consumption Trends"), use_container_width=True)

        # --- وظيفة الـ PDF الجذابة ---
        if st.button(l['pdf']):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "AL-SIDRA MONTHLY UTILITIES REPORT", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)
            pdf.cell(95, 10, f"Period: {sel_month}", border=1)
            pdf.cell(95, 10, f"Efficiency: {kpi_elec:.3f} kWh/kg", border=1, ln=True)
            pdf.cell(95, 10, f"Total Water Loss: {w_loss:,.0f} m3", border=1, ln=True)
            
            pdf_data = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_data).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Sidra_Report.pdf" style="padding:10px; background-color:green; color:white; border-radius:5px; text-decoration:none;">Click here to Download PDF</a>', unsafe_allow_html=True)

    except Exception as e: st.error(f"Error: {e}")
else: st.info("Please upload the file to start analysis.")
