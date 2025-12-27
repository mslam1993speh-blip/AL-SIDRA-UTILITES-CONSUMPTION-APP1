import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. إعدادات الصفحة والجماليات ---
st.set_page_config(page_title="Al-Sidra Utilities Intelligence", layout="wide")

st.markdown("""
    <style>
    .logo-img { display: block; margin: auto; width: 120px; border-radius: 50%; border: 2px solid #2E7D32; padding: 5px; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# نظام اللغة
if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

t = {
    'Arabic': {
        'title': "📊 نظام سدرة الذكي للمرافق والإنتاج",
        'lang_btn': "Switch to English",
        'prod_input': "إدخال كمية الإنتاج (كيلوغرام)",
        'summary': "📋 مؤشرات كفاءة الإنتاج (Baselines per KG)",
        'charts': "📈 تحليل الاستهلاك والإنتاج",
        'footer': "تم بواسطة قسم الصيانة (المرافق)"
    },
    'English': {
        'title': "📊 AL-SIDRA UTILITIES & PRODUCTION INTELLIGENCE",
        'lang_btn': "التحويل للعربية",
        'prod_input': "Production Quantity (KG)",
        'summary': "📋 Production Efficiency (Baselines per KG)",
        'charts': "📈 Consumption & Production Analytics",
        'footer': "Done by Maintenance Department (Utilities)"
    }
}
l = t[st.session_state.lang]

# --- 2. القائمة الجانبية (الشعار + الإنتاج) ---
with st.sidebar:
    # الشعار
    st.markdown(f'<img src="https://raw.githubusercontent.com/mslam1993speh-blip/al-sidra-utilites-consumption-app1/main/logo.png" class="logo-img">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>AL-SIDRA</h3>", unsafe_allow_html=True)
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    
    # مدخلات الإنتاج يدوياً لكل شهر
    st.subheader(l['prod_input'])
    prod_qty = st.number_input("Chicken Production (KG)", min_value=1.0, value=100000.0, step=1000.0)
    st.markdown("---")
    st.write(l['footer'])

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

        # فلترة الشهور
        month_list = list(full_df['MONTH'].unique())
        selected_month = st.selectbox("Select Month for Efficiency Analysis", month_list)
        df = full_df[full_df['MONTH'] == selected_month]

        # سحب البيانات
        def get_col(keys):
            for col in df.columns:
                if any(k in col for k in keys): return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0]*len(df))

        df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        df['LPG'] = get_col(['LPG', 'غاز'])
        df['W_IN'] = get_col(['WATER REC', 'وارد'])

        # --- 3. حساب مؤشرات الإنتاج (Efficiency Baselines) ---
        st.subheader(f"{l['summary']} - {selected_month}")
        k1, k2, k3 = st.columns(3)
        
        with k1:
            elec_per_kg = df['ELEC'].sum() / prod_qty
            st.metric("Electricity/KG", f"{elec_per_kg:.3f} kWh/kg", delta="Power Efficiency")
        
        with k2:
            lpg_per_kg = (df['LPG'].sum() * 1000) / prod_qty # تحويل لغرام لسهولة القراءة
            st.metric("LPG/KG", f"{lpg_per_kg:.2f} g/kg", delta="Gas Efficiency")

        with k3:
            water_per_kg = (df['W_IN'].sum() * 1000) / prod_qty # تحويل للتر
            st.metric("Water/KG", f"{water_per_kg:.2f} L/kg", delta="Water Efficiency")

        st.markdown("---")
        
        # الرسوم البيانية
        st.subheader(l['charts'])
        fig = px.bar(df, x='DATE', y=['ELEC', 'LPG'], title=f"Daily Consumption vs Production for {selected_month}")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Waiting for file...")
