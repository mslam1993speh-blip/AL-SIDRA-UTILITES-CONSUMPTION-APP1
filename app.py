import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# إعدادات الصفحة
st.set_page_config(page_title="Al-Sidra Intelligence", layout="wide")

# نظام تبديل اللغة
if 'lang' not in st.session_state:
    st.session_state.lang = 'Arabic'

def toggle_lang():
    st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

t = {
    'Arabic': {
        'title': "🛡️ AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "Switch to English",
        'upload': "ارفع ملف DAILY REPORT 2025",
        'anom_title': "🔍 كشف الشذوذ (Anomalies)",
        'download': "تحميل البيانات CSV",
        'no_file': "بانتظار رفع الملف..."
    },
    'English': {
        'title': "🛡️ AL-SIDRA UTILITES INTELLIGENCE SYSTEM",
        'lang_btn': "التحويل للعربية",
        'upload': "Upload DAILY REPORT 2025",
        'anom_title': "🔍 Anomaly Detection",
        'download': "Download CSV",
        'no_file': "Waiting for file upload..."
    }
}
l = t[st.session_state.lang]

st.sidebar.button(l['lang_btn'], on_click=toggle_lang)
st.title(l['title'])

uploaded_file = st.sidebar.file_uploader(l['upload'], type=['xlsx'])

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
        
        df = pd.concat(dfs, ignore_index=True)

        # دالة ذكية للبحث عن الأعمدة لتجنب الـ KeyError
        def find_col(keywords):
            for col in df.columns:
                if any(k in col for k in keywords):
                    return col
            return None

        # ربط الأعمدة ديناميكياً
        elec_col = find_col(['ELEC', 'كهرباء'])
        lpg_col = find_col(['LPG', 'غاز'])
        win_col = find_col(['WATER REC', 'WATER IN', 'وارد'])
        wout_col = find_col(['SANIT', 'WATER OUT', 'صرف'])

        # تحويل البيانات مع معالجة الأخطاء
        for col in [elec_col, lpg_col, win_col, wout_col]:
            if col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # حساب KPIs
        c1, c2, c3 = st.columns(3)
        if elec_col:
            c1.metric("Electricity Total", f"{df[elec_col].sum():,.0f} kWh")
        if win_col and wout_col:
            c2.metric("Water Loss", f"{df[win_col].sum() - df[wout_col].sum():,.0f} m³")
        
        # كشف الشذوذ (Anomalies)
        if elec_col:
            mean_v = df[elec_col].mean()
            std_v = df[elec_col].std()
            anomalies = df[df[elec_col] > (mean_v + 2*std_v)]
            if not anomalies.empty:
                st.error(f"{l['anom_title']}")
                st.dataframe(anomalies[['MONTH', 'DATE', elec_col]])

        # الرسم البياني
        if elec_col:
            fig = px.line(df, x='DATE', y=elec_col, color='MONTH', title="Daily Consumption Trend")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading columns: {e}")
        st.info("تأكد من أن أسماء الأعمدة في الإكسيل قريبة من (ELECTRICITY, LPG, WATER)")
else:
    st.info(l['no_file'])
