import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# --- 1. الإعدادات والجماليات ---
st.set_page_config(page_title="Al-Sidra Utilities Intelligence", layout="wide")

st.markdown("""
    <style>
    .logo-img { display: block; margin: auto; width: 100px; border-radius: 50%; border: 2px solid #2E7D32; padding: 5px; }
    .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .anomaly-card { background-color: #fff3f3; border-left: 5px solid #ff4b4b; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .forecast-box { background-color: #e8f5e9; border: 1px dashed #2e7d32; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

t = {
    'Arabic': {
        'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "Switch to English",
        'forecast': "🔮 التنبؤ بالاستهلاك المتوقع (Forecast)",
        'summary': "📋 مؤشرات الأداء والإنتاج",
        'anom': "🚨 كشف الشذوذ والتنبيهات",
        'footer': "Done by Maintenance Department (Utilities)"
    },
    'English': {
        'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "التحويل للعربية",
        'forecast': "🔮 Projected Consumption Forecast",
        'summary': "📋 Performance & Production KPIs",
        'anom': "🚨 Anomaly Detection & Alerts",
        'footer': "Done by Maintenance Department (Utilities)"
    }
}
l = t[st.session_state.lang]

# --- 2. القائمة الجانبية ---
with st.sidebar:
    st.markdown(f'<img src="https://raw.githubusercontent.com/mslam1993speh-blip/al-sidra-utilites-consumption-app1/main/logo.png" class="logo-img">', unsafe_allow_html=True)
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    prod_qty = st.number_input("Chicken Production (KG)", min_value=1.0, value=150000.0)
    st.markdown(f"<div style='text-align:center; color:grey; font-size:12px; margin-top:50px;'>{l['footer']}</div>", unsafe_allow_html=True)

st.title(l['title'])

if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        dfs = []
        for sheet in xl.sheet_names:
            temp_df = xl.parse(sheet); temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            temp_df.rename(columns={'DAY': 'DATE'}, inplace=True); temp_df = temp_df[pd.to_numeric(temp_df['DATE'], errors='coerce').notnull()]
            temp_df['MONTH'] = sheet; dfs.append(temp_df)
        full_df = pd.concat(dfs, ignore_index=True)

        selected_period = st.selectbox("Select Period", [l['all_year']] + list(full_df['MONTH'].unique()))
        df = full_df if selected_period == l['all_year'] else full_df[full_df['MONTH'] == selected_period]

        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء']); df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'وارد']); df['W_OUT'] = get_col(['SANIT', 'صرف', 'نضح'])

        # --- 3. قسم التنبؤ الذكي (Forecast) ---
        if selected_period != l['all_year']:
            st.subheader(l['forecast'])
            days_passed = len(df)
            total_days = 30 # تقريبياً
            if days_passed > 0 and days_passed < total_days:
                projected_elec = (df['ELEC'].sum() / days_passed) * total_days
                projected_water = (df['W_IN'].sum() / days_passed) * total_days
                f1, f2 = st.columns(2)
                f1.markdown(f"<div class='forecast-box'>⚡ المتوقع للكهرباء بنهاية الشهر: <br> <b>{projected_elec:,.0f} kWh</b></div>", unsafe_allow_html=True)
                f2.markdown(f"<div class='forecast-box'>💧 المتوقع للمياه بنهاية الشهر: <br> <b>{projected_water:,.0f} m³</b></div>", unsafe_allow_html=True)

        # --- 4. عرض KPIs الشاملة ---
        st.subheader(l['summary'])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Elec", f"{df['ELEC'].sum():,.0f} kWh")
        c2.metric("Total LPG", f"{df['LPG'].sum():,.0f} kg")
        loss = df['W_IN'].sum() - df['W_OUT'].sum()
        c3.metric("Water Loss", f"{loss:,.0f} m³", f"{(loss/df['W_IN'].sum()*100 if df['W_IN'].sum()>0 else 0):.1f}%")
        c4.metric("kWh/kg Product", f"{(df['ELEC'].sum()/prod_qty):.3f}")

        # --- 5. كشف الشذوذ والرسوم البيانية ---
        st.subheader(l['anom'])
        for col, label in [('ELEC', 'Electricity'), ('W_IN', 'Water')]:
            m, s = df[col].mean(), df[col].std()
            out = df[df[col] > (m + 2*s)]
            for _, r in out.iterrows():
                st.markdown(f"<div class='anomaly-card'>⚠️ <b>{label} Peak</b> on {r['DATE']}: {r[col]:,.0f}</div>", unsafe_allow_html=True)

        st.plotly_chart(px.line(df, x='DATE', y=['ELEC', 'LPG'], markers=True, title="Consumption Trend"), use_container_width=True)

    except Exception as e: st.error(f"Error: {e}")
else: st.info("Waiting for file...")
