import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from fpdf import FPDF
import base64
from datetime import datetime

# --- 1. الإعدادات والجماليات ---
st.set_page_config(page_title="Sidra Utilities Intelligence", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .forecast-box { background-color: #f1f8e9; border: 1px dashed #2e7d32; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; color: #1b5e20; }
    .pdf-download { text-align: center; padding: 20px; background-color: #e3f2fd; border-radius: 10px; margin-top: 10px; border: 1px solid #2196f3; }
    </style>
    """, unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

translations = {
    'Arabic': {
        'title': "📊 نظام سدرة الذكي للمرافق والإنتاج",
        'lang_btn': "Switch to English",
        'all_period': "السنة كاملة",
        'summary': "📋 مؤشرات الأداء والإنتاج (KPIs)",
        'baselines': "📉 خطوط الأساس (Baselines)",
        'forecast': "🔮 التنبؤ بنهاية الشهر",
        'anom': "🚨 كشف الشذوذ والتنبيهات",
        'pdf_btn': "📄 إصدار التقرير الشهري الاحترافي (PDF)",
        'footer': "قسم الصيانة - وحدة المرافق"
    },
    'English': {
        'title': "📊 SIDRA UTILITIES INTELLIGENCE",
        'lang_btn': "التحويل للعربية",
        'all_period': "Full Year",
        'summary': "📋 Production & Efficiency KPIs",
        'baselines': "📉 Baselines Analysis",
        'forecast': "🔮 Monthly Forecast",
        'anom': "🚨 Anomaly Detection",
        'pdf_btn': "📄 Generate Professional PDF Report",
        'footer': "Maintenance Dept - Utilities Unit"
    }
}
l = translations[st.session_state.lang]

# --- وظيفة إنشاء الـ PDF الجذاب ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(200, 30, 30) # Sidra Red color theme
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 20, 'AL-SIDRA UTILITIES REPORT', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(15)

    def create_table(self, header, data):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        for h in header:
            self.cell(95, 10, h, 1, 0, 'C', True)
        self.ln()
        self.set_font('Arial', '', 12)
        for desc, val in data:
            self.cell(95, 10, desc, 1)
            self.cell(95, 10, val, 1, 1, 'C')

def generate_pdf(df, kpis, period, footer_text):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Analysis for: {period}", 0, 1, 'L')
    pdf.ln(5)
    
    table_data = [
        ("Electricity Intensity", f"{kpis['elec']:.3f} kWh/kg"),
        ("LPG Intensity", f"{kpis['lpg']:.4f} kg/kg"),
        ("Water Intensity", f"{kpis['water']:.2f} L/kg"),
        ("Total Water Loss", f"{kpis['loss']:,.0f} m3"),
        ("Friday/Day Off Baseline", f"{kpis['baseline']:,.0f} kWh")
    ]
    pdf.create_table(["Metric Description", "Value"], table_data)
    
    pdf.ln(20)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, footer_text, 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- 2. القائمة الجانبية ---
with st.sidebar:
    try: st.image("al sidra new.jpg", use_container_width=True)
    except: st.subheader("AL-SIDRA")
    
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    prod_qty = st.number_input("Total Monthly Production (KG)", min_value=1.0, value=150000.0)
    st.markdown(f"<div style='text-align:center; color:grey; font-size:12px;'>{l['footer']}</div>", unsafe_allow_html=True)

st.title(l['title'])

if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        dfs = [xl.parse(s).assign(MONTH=s) for s in xl.sheet_names]
        full_df = pd.concat(dfs, ignore_index=True)
        full_df.columns = [str(c).strip().upper() for c in full_df.columns]
        full_df.rename(columns={'DAY': 'DATE'}, inplace=True)
        full_df = full_df[pd.to_numeric(full_df['DATE'], errors='coerce').notnull()]

        selected_period = st.selectbox("Select Period", [l['all_period']] + list(full_df['MONTH'].unique()))
        df = full_df if selected_period == l['all_period'] else full_df[full_df['MONTH'] == selected_period]

        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0.0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'وارد'])
        df['W_OUT'] = get_col(['SANIT', 'صرف'])

        # --- الحسابات المنطقية ---
        avg_daily_prod = prod_qty / 30
        kpis = {
            'elec': (df['ELEC'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0,
            'lpg': (df['LPG'].mean() / avg_daily_prod) if avg_daily_prod > 0 else 0,
            'water': (df['W_IN'].mean() / avg_daily_prod * 1000) if avg_daily_prod > 0 else 0,
            'loss': df['W_IN'].sum() - df['W_OUT'].sum()
        }

        # --- دمج Friday & Day Off Baseline ---
        df['DT'] = pd.to_datetime(df['DATE'], errors='coerce')
        # تعريف العطلة: يوم جمعة أو استهلاك أقل من 40% من متوسط الاستهلاك
        elec_threshold = df['ELEC'].mean() * 0.4
        off_days = df[(df['DT'].dt.day_name() == 'Friday') | (df['ELEC'] < elec_threshold)]
        kpis['baseline'] = off_days['ELEC'].mean() if not off_days.empty else 0

        # --- قسم الـ PDF المطور ---
        st.markdown(f"<div class='pdf-download'>", unsafe_allow_html=True)
        if st.button(l['pdf_btn']):
            pdf_bytes = generate_pdf(df, kpis, selected_period, l['footer'])
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Sidra_Report_{selected_period}.pdf" style="text-decoration:none; color:white; background-color:#d32f2f; padding:10px 20px; border-radius:5px; font-weight:bold;">📥 Click to Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- عرض KPIs ---
        st.subheader(l['summary'])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Electricity/KG", f"{kpis['elec']:.3f} kWh/kg")
        c2.metric("LPG/KG", f"{kpis['lpg']:.4f} kg/kg")
        c3.metric("Water Intensity", f"{kpis['water']:.1f} L/kg")
        c4.metric("Water Loss", f"{kpis['loss']:,.0f} m³")

        # --- خطوط الأساس المدمجة ---
        st.subheader(l['baselines'])
        b1, b2 = st.columns(2)
        b1.metric("Friday & Day-Off Baseline", f"{kpis['baseline']:,.0f} kWh", help="Average consumption on Fridays and very low-activity days")
        
        summer_data = df[df['MONTH'].str.upper().isin(['JUNE', 'JULY', 'AUGUST', 'يونيو', 'يوليو', 'أغسطس'])]
        b2.metric("Summer Peak Baseline", f"{np.nan_to_num(summer_data['ELEC'].mean()):,.0f} kWh")

        st.plotly_chart(px.line(df, x='DATE', y=['ELEC', 'LPG', 'W_IN'], title="Consumption Trends Analysis"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("System Ready. Please upload Excel.")
