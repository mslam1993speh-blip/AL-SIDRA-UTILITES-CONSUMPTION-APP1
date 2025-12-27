import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. الإعدادات الأساسية والجماليات ---
st.set_page_config(page_title="Sidra Utilities Intelligence", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .anomaly-card { background-color: #fff3f3; border-left: 5px solid #ff4b4b; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .forecast-box { background-color: #e8f5e9; border: 1px dashed #2e7d32; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# نظام اللغة - حل مشكلة all_year
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

translations = {
    'Arabic': {
        'title': "📊 نظام سدرة الذكي لإدارة المرافق والإنتاج",
        'lang_btn': "Switch to English",
        'all_period': "السنة كاملة",
        'summary': "📋 مؤشرات الأداء والإنتاج",
        'forecast': "🔮 التنبؤ بالاستهلاك المتوقع بنهاية الشهر",
        'anom': "🚨 كشف الشذوذ والتنبيهات",
        'footer': "Done by Maintenance Department (Utilities)",
        'wait': "بانتظار رفع ملف البيانات..."
    },
    'English': {
        'title': "📊 SIDRA UTILITIES & PRODUCTION INTELLIGENCE",
        'lang_btn': "التحويل للعربية",
        'all_period': "Full Year",
        'summary': "📋 Performance & Production KPIs",
        'forecast': "🔮 Projected Monthly Forecast",
        'anom': "🚨 Anomaly Detection & Alerts",
        'footer': "Done by Maintenance Department (Utilities)",
        'wait': "Waiting for Data File..."
    }
}
l = translations[st.session_state.lang]

# --- 2. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    try:
        st.image("al sidra new.jpg", use_container_width=True)
    except:
        st.info("Sidra Factory")
    
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    prod_qty = st.number_input("Chicken Production (KG)", min_value=1.0, value=150000.0)
    st.markdown("---")
    st.markdown(f"<div style='text-align:center; color:grey; font-size:12px;'>{l['footer']}</div>", unsafe_allow_html=True)

st.title(l['title'])

if uploaded_file:
    try:
        # معالجة ملف الإكسيل
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

        # فلترة الفترة الزمنية
        month_list = [l['all_period']] + list(full_df['MONTH'].unique())
        selected_period = st.selectbox("Select Period", month_list)
        df = full_df if selected_period == l['all_period'] else full_df[full_df['MONTH'] == selected_period]

        # دالة جلب الأعمدة بمرونة لتجنب KeyError
        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0.0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'WATER IN', 'وارد'])
        df['W_OUT'] = get_col(['SANIT', 'صرف', 'نضح'])

        # --- 3. التنبؤ الذكي ---
        if selected_period != l['all_period']:
            st.subheader(l['forecast'])
            days_passed = len(df)
            if 0 < days_passed < 31:
                p_elec = (df['ELEC'].sum() / days_passed) * 30
                p_water = (df['W_IN'].sum() / days_passed) * 30
                f1, f2 = st.columns(2)
                f1.markdown(f"<div class='forecast-box'>⚡ المتوقع للكهرباء: {p_elec:,.0f} kWh</div>", unsafe_allow_html=True)
                f2.markdown(f"<div class='forecast-box'>💧 المتوقع للمياه: {p_water:,.0f} m³</div>", unsafe_allow_html=True)

        # --- 4. عرض مؤشرات الأداء (KPIs) ---
        st.subheader(l['summary'])
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Electricity", f"{df['ELEC'].sum():,.0f} kWh")
        with c2: st.metric("Total LPG", f"{df['LPG'].sum():,.0f} kg")
        with c3:
            loss = df['W_IN'].sum() - df['W_OUT'].sum()
            loss_pct = (loss / df['W_IN'].sum() * 100) if df['W_IN'].sum() > 0 else 0
            st.metric("Water Loss", f"{loss:,.0f} m³", f"{loss_pct:.1f}% Loss")
        with c4: st.metric("Elec/KG Product", f"{(df['ELEC'].sum()/prod_qty):.3f}")

        # --- 5. كشف الشذوذ والتنبيهات ---
        st.subheader(l['anom'])
        found_anom = False
        for col, label in [('ELEC', 'Electricity'), ('W_IN', 'Water')]:
            m, s = df[col].mean(), df[col].std()
            outliers = df[df[col] > (m + 2*s)]
            for _, r in outliers.iterrows():
                st.markdown(f"<div class='anomaly-card'>⚠️ <b>{label} Peak</b> on {r['DATE']}: {r[col]:,.1f}</div>", unsafe_allow_html=True)
                found_anom = True
        if not found_anom: st.success("Operations are stable. No spikes detected. ✅")

        # --- 6. الرسوم البيانية ---
        st.plotly_chart(px.line(df, x='DATE', y=['ELEC', 'LPG', 'W_IN'], markers=True, title="Utilities Trend Analysis"), use_container_width=True)

    except Exception as e:
        st.error(f"Please check your Excel sheet format. Error: {e}")
else:
    st.info(l['wait'])
