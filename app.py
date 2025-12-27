import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- الإعدادات الأساسية ---
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
        'download': "تحميل التقرير (CSV)",
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
        'download': "Download Report (CSV)",
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

        # دالة الربط المرن للأعمدة (لتجنب KeyError)
        def get_col_data(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0]*len(df))

        df['ELEC'] = get_col_data(['ELEC', 'كهرباء'])
        df['LPG'] = get_col_data(['LPG', 'غاز'])
        df['W_IN'] = get_col_data(['WATER REC', 'WATER IN', 'وارد'])
        df['W_OUT'] = get_col_data(['SANIT', 'WATER OUT', 'صرف', 'نضح'])

        # --- 1. القسم الأول: KPIs & Ratios ---
        st.subheader(f"{l['summary']} - {selected_period}")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            loss_m3 = df['W_IN'].sum() - df['W_OUT'].sum()
            loss_pct = (loss_m3 / df['W_IN'].sum() * 100) if df['W_IN'].sum() > 0 else 0
            st.metric("Water Loss", f"{loss_m3:,.0f} m³", f"{loss_pct:.1f}% Loss")
        
        with c2:
            e_ratio = (df['ELEC'].sum() / df['LPG'].sum()) if df['LPG'].sum() > 0 else 0
            st.metric("Energy Efficiency", f"{e_ratio:.2f}", "KWH/LPG")

        with c3:
            df['DT'] = pd.to_datetime(df['DATE'], errors='coerce')
            fri_base = df[df['DT'].dt.day_name() == 'Friday']['ELEC'].mean()
            st.metric("Friday Baseline", f"{fri_base:,.0f} kWh")

        with c4:
            sum_base = df[df['MONTH'].str.upper().isin(['JUNE','JULY','AUGUST'])]['ELEC'].mean()
            st.metric("Summer Baseline", f"{sum_base:,.0f} kWh")

        st.markdown("---")

        # --- 2. القسم الثاني: الشذوذ (Anomalies) ---
        st.subheader(l['anom'])
        anom_list = []
        for col, name in [('ELEC', 'Electricity'), ('LPG', 'LPG'), ('W_IN', 'Water In')]:
            m, s = df[col].mean(), df[col].std()
            anoms = df[df[col] > (m + 2*s)]
            for _, row in anoms.iterrows():
                anom_list.append({'Date': row['DATE'], 'Utility': name, 'Value': row[col], 'Alert': 'High Peak ⚠️'})
        
        if anom_list: st.table(pd.DataFrame(anom_list))
        else: st.success("Operations are normal.")

        # --- 3. القسم الثالث: الرسوم البيانية ---
        st.subheader(l['charts'])
        fig = px.line(df, x='DATE', y=['ELEC', 'LPG', 'W_IN', 'W_OUT'], markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # زر التحميل
        st.download_button(l['download'], df.to_csv(index=False).encode('utf-8-sig'), "Sidra_Report.csv", "text/csv")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(l['no_file'])
