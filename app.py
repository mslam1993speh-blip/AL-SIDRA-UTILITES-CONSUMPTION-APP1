import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Page config ---
st.set_page_config(page_title="Sidra Utilities Intelligence", layout="wide")

st.markdown("""
<style>
.stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
.forecast-box { background-color: #e8f5e9; border: 1px dashed #2e7d32; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; }
.anomaly-card { background-color: #fff3f3; border-left: 5px solid #ff4b4b; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- Language ---
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

translations = {
    'Arabic': {
        'title': "📊 نظام سدرة الذكي الشامل للمرافق والإنتاج",
        'lang_btn': "Switch to English",
        'all_period': "السنة كاملة",
        'summary': "📋 مؤشرات الأداء والإنتاج (KPIs)",
        'forecast': "🔮 التنبؤ بالاستهلاك المتوقع بنهاية الشهر",
        'anom': "🚨 كشف الشذوذ والتنبيهات",
        'baselines': "📉 خطوط الأساس (Baselines)",
        'footer': "Done by Maintenance Department (Utilities)"
    },
    'English': {
        'title': "📊 SIDRA COMPREHENSIVE UTILITIES & PRODUCTION SYSTEM",
        'lang_btn': "التحويل للعربية",
        'all_period': "Full Year",
        'summary': "📋 Production & Efficiency KPIs",
        'forecast': "🔮 Monthly Forecast",
        'anom': "🚨 Anomaly Detection",
        'baselines': "📉 Baselines Analysis",
        'footer': "Done by Maintenance Department (Utilities)"
    }
}
l = translations[st.session_state.lang]

# --- PDF generation function ---
def generate_professional_pdf(month, df, prod_qty, logo_path="al sidra new.jpg"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    styleH = styles['Heading1']
    styleN = styles['Normal']

    # Logo
    try:
        im = Image(logo_path, width=120, height=50)
        elements.append(im)
    except:
        pass
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Monthly Utilities Report</b>", styleH))
    elements.append(Paragraph(f"Month: {month}", styleN))
    elements.append(Spacer(1, 12))

    avg_daily_prod = prod_qty / 30 if prod_qty > 0 else 0

    # KPIs table
    data = [
        ["Metric", "Value", "Unit"],
        ["Total Electricity", f"{df['ELEC'].sum():,.0f}", "kWh"],
        ["Total LPG", f"{df['LPG'].sum():,.0f}", "kg"],
        ["Total Water In", f"{df['W_IN'].sum():,.1f}", "m³"],
        ["Water Loss", f"{(df['W_IN'].sum() - df['W_OUT'].sum()):,.1f}", "m³"],
        ["Electricity/KG", f"{(df['ELEC'].mean()/avg_daily_prod if avg_daily_prod else 0):.4f}", "kWh/kg"],
        ["LPG/KG", f"{(df['LPG'].mean()/avg_daily_prod if avg_daily_prod else 0):.5f}", "kg/kg"],
        ["Water/KG (L)", f"{(df['W_IN'].mean()/avg_daily_prod*1000 if avg_daily_prod else 0):.2f}", "L/kg"],
    ]

    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Charts using Plotly images
    for col, title, color in [('ELEC', 'Electricity', 'blue'),
                              ('LPG', 'LPG', 'red'),
                              ('W_IN', 'Water', 'green')]:
        fig = px.line(df, x='DATE', y=col, title=title, markers=True, color_discrete_sequence=[color])
        img_bytes = fig.to_image(format="png")
        img = Image(io.BytesIO(img_bytes), width=450, height=200)
        elements.append(img)
        elements.append(Spacer(1,12))

    # Prepared by footer
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Prepared by: Utilities Department", styleN))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- Sidebar ---
with st.sidebar:
    try:
        st.image("al sidra new.jpg", use_container_width=True)
    except:
        st.subheader("AL-SIDRA")
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    prod_qty = st.number_input("Total Monthly Production (KG)", min_value=1.0, value=150000.0)
    st.markdown("---")
    st.markdown(f"<div style='text-align:center; color:grey; font-size:12px;'>{l['footer']}</div>", unsafe_allow_html=True)

st.title(l['title'])

if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        dfs = []
        for sheet in xl.sheet_names:
            temp_df = xl.parse(sheet)
            temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            temp_df.rename(columns={'DAY': 'DATE'}, inplace=True)
            temp_df = temp_df[pd.to_numeric(temp_df['DATE'], errors='coerce').notnull()]
            temp_df['MONTH'] = sheet
            dfs.append(temp_df)
        full_df = pd.concat(dfs, ignore_index=True)

        month_list = [l['all_period']] + list(full_df['MONTH'].unique())
        selected_period = st.selectbox("Select Period", month_list)
        df = full_df if selected_period == l['all_period'] else full_df[full_df['MONTH'] == selected_period]

        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0.0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'وارد'])
        df['W_OUT'] = get_col(['SANIT', 'صرف', 'نضح'])

        # --- PDF Download ---
        if selected_period != l['all_period']:
            pdf = generate_professional_pdf(selected_period, df, prod_qty)
            st.download_button(
                label="📄 Download Professional PDF Report",
                data=pdf,
                file_name=f"{selected_period}_Utilities_Professional_Report.pdf",
                mime="application/pdf"
            )

        # --- Forecast ---
        st.subheader(l['forecast'])
        days_in_data = len(df)
        if days_in_data > 0:
            p_elec = (df['ELEC'].sum() / days_in_data) * 30
            p_lpg = (df['LPG'].sum() / days_in_data) * 30
            p_water = (df['W_IN'].sum() / days_in_data) * 30
            
            f1, f2, f3 = st.columns(3)
            f1.markdown(f"<div class='forecast-box'>⚡ {l['forecast']} (Elec):<br>{p_elec:,.0f} kWh</div>", unsafe_allow_html=True)
            f2.markdown(f"<div class='forecast-box'>🔥 {l['forecast']} (LPG):<br>{p_lpg:,.0f} kg</div>", unsafe_allow_html=True)
            f3.markdown(f"<div class='forecast-box'>💧 {l['forecast']} (Water):<br>{p_water:,.0f} m³</div>", unsafe_allow_html=True)

        # --- KPIs ---
        avg_daily_prod = prod_qty / 30
        st.subheader(l['summary'])
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Electricity/KG", f"{(df['ELEC'].mean() / avg_daily_prod if avg_daily_prod>0 else 0):.3f} kWh/kg")
        with c2: st.metric("LPG/KG", f"{(df['LPG'].mean()/avg_daily_prod if avg_daily_prod>0 else 0):.4f} kg/kg")
        with c3: st.metric("Water/KG", f"{(df['W_IN'].mean()/avg_daily_prod*1000 if avg_daily_prod>0 else 0):.2f} L/kg")
        with c4: st.metric("Water Loss", f"{df['W_IN'].sum()-df['W_OUT'].sum():,.0f} m³", f"{(df['W_IN'].sum()-df['W_OUT'].sum())/df['W_IN'].sum()*100 if df['W_IN'].sum()>0 else 0:.1f}%")

        # --- Baselines ---
        st.subheader(l['baselines'])
        df['DT'] = pd.to_datetime(df['DATE'], errors='coerce')
        friday_data = df[df['DT'].dt.day_name() == 'Friday']
        summer_data = df[df['MONTH'].str.upper().isin(['JUNE','JULY','AUGUST','يونيو','يوليو','أغسطس'])]
        b1,b2,b3,b4 = st.columns(4)
        with b1: st.metric("Friday Elec Baseline", f"{np.nan_to_num(friday_data['ELEC'].mean()):,.0f} kWh")
        with b2: st.metric("Summer Elec Baseline", f"{np.nan_to_num(summer_data['ELEC'].mean()):,.0f} kWh")
        with b3: st.metric("Avg Daily LPG", f"{df['LPG'].mean():,.1f} kg")
        with b4: st.metric("Avg Daily Water", f"{df['W_IN'].mean():,.1f} m³")

        # --- Anomalies ---
        st.subheader(l['anom'])
        anom_found = False
        for col,label in [('ELEC','Elec'),('W_IN','Water')]:
            m,s = df[col].mean(), df[col].std()
            out = df[df[col] > (m + 2*s)]
            for _,r in out.iterrows():
                st.warning(f"Peak {label} on {r['DATE']}: {r[col]:,.0f}")
                anom_found=True
        if not anom_found: st.success("Stable Operations ✅")

        st.plotly_chart(px.line(df, x='DATE', y=['ELEC','LPG','W_IN'], title="Daily Trends Analysis"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("System Ready. Please upload Excel.")
