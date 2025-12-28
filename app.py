import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from fpdf import FPDF
import base64

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Sidra Utilities Intelligence", layout="wide")

# --- 2. القائمة الجانبية ---
with st.sidebar:
    try: st.image("al sidra new.jpg", use_container_width=True)
    except: st.header("AL-SIDRA")
    
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
    prod_qty = st.number_input("Monthly Production (KG)", min_value=1.0, value=150000.0)

# --- 3. المعالجة الذكية (حل مشكلة TypeError) ---
if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        all_dfs = []
        for sheet in xl.sheet_names:
            temp = xl.parse(sheet)
            # تنظيف أسماء الأعمدة من الفراغات وتحويلها لكبير
            temp.columns = [str(c).strip().upper() for c in temp.columns]
            temp['SHEET_NAME'] = sheet
            all_dfs.append(temp)
        
        df_full = pd.concat(all_dfs, ignore_index=True)
        
        # اختيار الشهر
        selected_month = st.selectbox("Select Month", list(df_full['SHEET_NAME'].unique()))
        df = df_full[df_full['SHEET_NAME'] == selected_month].copy()

        # دالة "الأمان القصوى" لجلب البيانات (تمنع خطأ TypeError)
        def get_safe_data(keywords):
            # البحث عن أول عمود يحتوي على الكلمة المطلوبة
            col_name = next((c for c in df.columns if any(k in c for k in keywords)), None)
            if col_name is not None:
                # التأكد من أننا نرسل "Series" للدالة وليس None
                return pd.to_numeric(df[col_name], errors='coerce').fillna(0)
            else:
                # إذا لم يجد العمود، ينشئ عمود أصفار بنفس الطول
                return pd.Series([0.0] * len(df))

        # جلب البيانات باستخدام الدالة الجديدة
        df['E_CLEAN'] = get_safe_data(['ELEC', 'كهرباء'])
        df['L_CLEAN'] = get_safe_data(['LPG', 'غاز'])
        df['W_IN'] = get_safe_data(['WATER REC', 'وارد'])
        df['W_OUT'] = get_safe_data(['SANIT', 'صرف'])

        # --- 4. الحسابات المنطقية ---
        avg_prod_daily = prod_qty / 30
        kpi_elec = (df['E_CLEAN'].mean() / avg_prod_daily) if avg_daily_prod > 0 else 0
        
        # ذكاء العطلات (Friday & Day Off)
        # نعتبر أي يوم استهلاكه أقل من 45% من المتوسط هو يوم عطلة
        holiday_mask = (df['E_CLEAN'] < df['E_CLEAN'].mean() * 0.45)
        baseline_val = df[holiday_mask]['E_CLEAN'].mean() if holiday_mask.any() else df['E_CLEAN'].min()

        # --- 5. العرض والتقرير ---
        st.title("📊 Sidra Intelligence System")
        c1, c2, c3 = st.columns(3)
        c1.metric("Electricity/KG", f"{kpi_elec:.3f} kWh/kg")
        c2.metric("Holiday Baseline", f"{baseline_val:,.0f} kWh")
        c3.metric("Total Monthly Elec", f"{df['E_CLEAN'].sum():,.0f} kWh")

        # التقرير PDF
        if st.button("📄 Generate Professional PDF Report"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(200, 0, 0)
            pdf.rect(0, 0, 210, 40, 'F')
            pdf.set_font("Arial", 'B', 20)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 20, "AL-SIDRA UTILITIES REPORT", 0, 1, 'C')
            pdf.ln(20)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(95, 10, "Metric", 1); pdf.cell(95, 10, "Value", 1, 1)
            pdf.set_font("Arial", '', 12)
            pdf.cell(95, 10, "Elec Efficiency", 1); pdf.cell(95, 10, f"{kpi_elec:.3f} kWh/kg", 1, 1)
            pdf.cell(95, 10, "Holiday Baseline", 1); pdf.cell(95, 10, f"{baseline_val:,.0f} kWh", 1, 1)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Sidra_Report.pdf" style="background-color:red; color:white; padding:10px; border-radius:5px; text-decoration:none;">Download PDF</a>', unsafe_allow_html=True)

        st.plotly_chart(px.line(df, y='E_CLEAN', title="Daily Electricity Trend"), use_container_width=True)

    except Exception as e:
        st.error(f"Error Detail: {e}")
else:
    st.info("Ready for your Daily Report Excel...")
