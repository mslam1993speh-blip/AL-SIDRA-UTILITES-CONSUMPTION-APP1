import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# إعدادات الصفحة
st.set_page_config(page_title="Sidra Power Intelligence", layout="wide")

# --- نظام تبديل اللغة ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'Arabic'

def toggle_lang():
    st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

# قاموس الترجمة
t = {
    'Arabic': {
        'title': "🛡️ نظام سدرة الذكي لإدارة الطاقة",
        'lang_btn': "Switch to English",
        'upload': "ارفع ملف DAILY REPORT 2025",
        'kpi_eff': "كفاءة KWH/LPG",
        'water_waste': "هدر المياه (الفقد)",
        'fri_base': "خط الأساس (الجمعة)",
        'sum_base': "خط الأساس (الصيف)",
        'anom_title': "🔍 كشف الشذوذ في الاستهلاك (Anomalies)",
        'anom_desc': "تم اكتشاف قيم غير طبيعية في الأيام التالية:",
        'download': "تحميل التقرير PDF (CSV حالياً)",
        'charts': "الرسوم البيانية والتحليلات",
        'no_file': "نظام سدرة بانتظار الملف.. ارفعه من القائمة الجانبية."
    },
    'English': {
        'title': "🛡️ Sidra Power Intelligence System",
        'lang_btn': "التحويل للعربية",
        'upload': "Upload DAILY REPORT 2025",
        'kpi_eff': "Efficiency KWH/LPG",
        'water_waste': "Water Waste (Loss)",
        'fri_base': "Friday Baseline",
        'sum_base': "Summer Baseline",
        'anom_title': "🔍 Consumption Anomaly Detection",
        'anom_desc': "Abnormal values detected on the following days:",
        'download': "Download PDF Report",
        'charts': "Charts & Analytics",
        'no_file': "System waiting for file.. upload from sidebar."
    }
}

l = t[st.session_state.lang]

# الواجهة
st.sidebar.button(l['lang_btn'], on_click=toggle_lang)
st.title(l['title'])

uploaded_file = st.sidebar.file_uploader(l['upload'], type=['xlsx'])

if uploaded_file:
    # معالجة البيانات
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
    
    # تنظيف الأرقام
    df['ELEC'] = pd.to_numeric(df['ELECTRICITY (KWH)'], errors='coerce').fillna(0)
    df['LPG'] = pd.to_numeric(df['LPG CONS (KG)'], errors='coerce').fillna(0)
    df['W_IN'] = pd.to_numeric(df['WATER RECIVED (M3)'], errors='coerce').fillna(0)
    df['W_OUT'] = pd.to_numeric(df['SANITAION (M3)'], errors='coerce').fillna(0)

    # --- اكتشاف الشذوذ (Anomalies) ---
    # نعتبر أي قيمة تزيد أو تنقص عن المتوسط بـ 2 Standard Deviation هي شذوذ
    mean_elec = df['ELEC'].mean()
    std_elec = df['ELEC'].std()
    anomalies = df[(df['ELEC'] > mean_elec + 2*std_elec) | (df['ELEC'] < mean_elec - 2*std_elec)]

    # العرض
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(l['kpi_eff'], f"{(df['ELEC'].sum()/df['LPG'].sum() if df['LPG'].sum()>0 else 0):.2f}")
    c2.metric(l['water_waste'], f"{df['W_IN'].sum() - df['W_OUT'].sum():,.0f} m³")
    
    # Baselines
    df['IS_FRI'] = pd.to_datetime(df['DATE'], errors='coerce').dt.day_name() == 'Friday'
    c3.metric(l['fri_base'], f"{df[df['IS_FRI']]['ELEC'].mean():,.0f}")
    c4.metric(l['sum_base'], f"{df[df['MONTH'].str.upper().isin(['JULY','AUGUST'])]['ELEC'].mean():,.0f}")

    # قسم الشذوذ
    if not anomalies.empty:
        st.error(l['anom_title'])
        st.write(l['anom_desc'])
        st.dataframe(anomalies[['MONTH', 'DATE', 'ELEC']], use_container_width=True)

    # شارت الكهرباء
    st.subheader(l['charts'])
    fig = px.line(df, x='DATE', y='ELEC', color='MONTH', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # زر التحميل
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(l['download'], data=csv, file_name="Sidra_Report.csv", mime='text/csv')

else:
    st.info(l['no_file'])
