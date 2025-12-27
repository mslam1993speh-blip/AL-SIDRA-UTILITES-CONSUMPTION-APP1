import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# إعداد الصفحة
st.set_page_config(page_title="Al-Sidra Utilities Intelligence", layout="wide")

# نظام تبديل اللغة
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

t = {
    'Arabic': {
        'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "Switch to English",
        'filter': "اختر الفترة الزمنية",
        'all_year': "السنة كاملة (2025)",
        'summary': "📋 مؤشرات الأداء والنسب (KPIs & Ratios)",
        'anom': "🚨 كشف الشذوذ والتنبيهات (Anomalies)",
        'charts': "📈 الرسوم البيانية والتحليلات",
        'no_file': "نظام سدرة بانتظار رفع الملف..."
    },
    'English': {
        'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "التحويل للعربية",
        'filter': "Select Time Period",
        'all_year': "Full Year (2025)",
        'summary': "📋 Performance Summary & Ratios",
        'anom': "🚨 Anomaly Detection & Alerts",
        'charts': "📈 Analytics & Charts",
        'no_file': "System waiting for file upload..."
    }
}
l = t[st.session_state.lang]

st.sidebar.button(l['lang_btn'], on_click=toggle_lang)
st.title(l['title'])

uploaded_file = st.sidebar.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])

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

        # فلترة الشهور
        month_list = [l['all_year']] + list(full_df['MONTH'].unique())
        selected_period = st.sidebar.selectbox(l['filter'], month_list)
        df = full_df if selected_period == l['all_year'] else full_df[full_df['MONTH'] == selected_period]

        # سحب البيانات (بناءً على الترتيب والأسماء)
        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'وارد'])
        df['W_OUT'] = get_col(['SANIT', 'صرف', 'نضح'])

        # حساب KPIs مع معالجة الـ nan
        st.subheader(f"{l['summary']} - {selected_period}")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            loss = df['W_IN'].sum() - df['W_OUT'].sum()
            lpct = (loss / df['W_IN'].sum() * 100) if df['W_IN'].sum() > 0 else 0
            st.metric("Water Loss", f"{loss:,.0f} m³", f"{lpct:.1f}% Loss")
        
        with c2:
            e_ratio = (df['ELEC'].sum() / df['LPG'].sum()) if df['LPG'].sum() > 0 else 0
            st.metric("Energy Efficiency", f"{e_ratio:.2f}", "KWH/LPG")

        with c3:
            df['DT'] = pd.to_datetime(df['DATE'], errors='coerce')
            f_data = df[df['DT'].dt.day_name() == 'Friday']['ELEC']
            f_base = f_data.mean() if not f_data.empty else 0
            st.metric("Friday Baseline", f"{np.nan_to_num(f_base):,.0f} kWh")

        with c4:
            s_months = ['JUNE', 'JULY', 'AUGUST', 'يونيو', 'يوليو', 'أغسطس']
            s_data = df[df['MONTH'].str.upper().isin(s_months)]['ELEC']
            s_base = s_data.mean() if not s_data.empty else 0
            st.metric("Summer Baseline", f"{np.nan_to_num(s_base):,.0f} kWh")

        st.markdown("---")
        # الرسوم البيانية
        st.subheader(l['charts'])
        st.plotly_chart(px.line(df, x='DATE', y=['ELEC', 'LPG', 'W_IN', 'W_OUT'], markers=True), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(l['no_file'])
