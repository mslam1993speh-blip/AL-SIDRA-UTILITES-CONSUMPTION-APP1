import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. إعدادات الصفحة والشعار ---
st.set_page_config(page_title="Al-Sidra Utilities Intelligence", layout="wide")

# كود لتعديل شكل الشعار ليصبح ناعم ودائري (CSS)
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        padding-top: 20px;
    }
    .logo-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 120px;
        border-radius: 50%; /* لجعل الصورة دائرية */
        border: 2px solid #2E7D32; /* إطار خفيف بلون المصنع */
        padding: 5px;
    }
    .footer {
        position: fixed;
        left: 10px;
        bottom: 10px;
        width: 250px;
        color: grey;
        font-size: 12px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. القائمة الجانبية (الشعار والحقوق) ---
with st.sidebar:
    # ضع رابط صورة شعار الشركة هنا أو ارفعها على GitHub واستخدم الرابط
    # إذا كانت الصورة موجودة بجانب الملف سمّها logo.png واستبدل الرابط بـ "logo.png"
    logo_url = "https://raw.githubusercontent.com/mslam1993speh-blip/al-sidra-utilites-consumption-app1/main/logo.png" # مثال لرابط
    
    st.markdown(f'<img src="{logo_url}" class="logo-img">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #2E7D32;'>Al-Sidra Factory</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # إضافة عبارة الحقوق في أسفل القائمة الجانبية بشكل ناعم
    st.markdown("""
        <div style='text-align: center; margin-top: 50px; font-size: 0.8em; color: #666;'>
            Done by Maintenance Department (Utilities)
        </div>
    """, unsafe_allow_html=True)

# --- باقي الكود البرمجي (نفس النسخة المصححة السابقة) ---

if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

t = {
    'Arabic': {'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM", 'lang_btn': "Switch to English", 'no_file': "بانتظار الملف..."},
    'English': {'title': "📊 AL-SIDRA UTILITES INTELLIGENCE SYSTEM", 'lang_btn': "التحويل للعربية", 'no_file': "Waiting for file..."}
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

        def get_col(keys):
            for col in full_df.columns:
                if any(k in col for k in keys): return pd.to_numeric(full_df[col], errors='coerce').fillna(0)
            return pd.Series([0]*len(full_df))

        full_df['ELEC'] = get_col(['ELEC', 'كهرباء'])
        full_df['LPG'] = get_col(['LPG', 'غاز'])
        full_df['W_IN'] = get_col(['WATER REC', 'وارد'])
        full_df['W_OUT'] = get_col(['SANIT', 'صرف', 'نضح'])

        # حساب KPIs مع معالجة nan
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Water Loss", f"{(full_df['W_IN'].sum()-full_df['W_OUT'].sum()):,.0f} m³")
        with c2: st.metric("KWH/LPG", f"{(full_df['ELEC'].sum()/full_df['LPG'].sum() if full_df['LPG'].sum()>0 else 0):.2f}")
        
        # الرسوم البيانية
        st.plotly_chart(px.line(full_df, x='DATE', y=['ELEC', 'LPG', 'W_IN', 'W_OUT'], markers=True), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(l['no_file'])
