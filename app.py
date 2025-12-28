import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. التنسيق البصري (ألوان فاقعة ومتباينة) ---
st.set_page_config(page_title="Sidra Intelligence", layout="wide")

st.markdown("""
    <style>
    /* تنسيق المؤشرات خلفية سوداء وإطار أخضر */
    [data-testid="stMetric"] {
        background-color: #000000;
        border: 3px solid #00FF00;
        padding: 20px;
        border-radius: 15px;
    }
    /* رقم المؤشر أحمر فاقع */
    [data-testid="stMetricValue"] {
        color: #FF0000 !important;
        font-size: 35px !important;
    }
    /* عنوان المؤشر أبيض */
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-size: 20px !important;
    }
    /* تنسيق حاوية التقرير الجذاب */
    .report-card {
        background-color: #ffffff;
        border: 10px double #000000;
        padding: 40px;
        color: #000000;
        font-family: 'Courier New', Courier, monospace;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = 'Arabic'
def toggle_lang(): st.session_state.lang = 'English' if st.session_state.lang == 'Arabic' else 'Arabic'

translations = {
    'Arabic': {
        'title': "📊 لوحة تحكم سدرة الذكية",
        'summary': "📋 مؤشرات الكفاءة والإنتاج",
        'baselines': "📉 خطوط الأساس (العطلات والجمع)",
        'gen_report': "📂 عرض التقرير الشهري الجذاب",
        'footer': "قسم الصيانة - وحدة المرافق"
    },
    'English': {
        'title': "📊 SIDRA SMART DASHBOARD",
        'summary': "📋 Efficiency KPIs",
        'baselines': "📉 Baselines Analysis",
        'gen_report': "📂 View Monthly Pro Report",
        'footer': "Maintenance Dept - Utilities"
    }
}
l = translations[st.session_state.lang]

# --- 2. القائمة الجانبية ---
with st.sidebar:
    try: st.image("al sidra new.jpg", use_container_width=True)
    except: st.title("SIDRA")
    st.button("Switch Language / تغيير اللغة", on_click=toggle_lang)
    uploaded_file = st.file_uploader("Upload Daily Excel", type=['xlsx'])
    prod_qty = st.number_input("Monthly Production (KG)", min_value=1.0, value=150000.0)

# --- 3. المعالجة والعرض ---
if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        df_list = [xl.parse(s).assign(MONTH=s) for s in xl.sheet_names]
        full_df = pd.concat(df_list, ignore_index=True)
        full_df.columns = [str(c).strip().upper() for c in full_df.columns]
        
        selected_month = st.selectbox("Select Month", list(full_df['MONTH'].unique()))
        df = full_df[full_df['MONTH'] == selected_month].copy()

        # تنظيف البيانات
        def clean(keys):
            col = next((c for c in df.columns if any(k in c for k in keys)), None)
            return pd.to_numeric(df[col], errors='coerce').fillna(0) if col else pd.Series([0.0]*len(df))

        df['E'] = clean(['ELEC', 'كهرباء'])
        df['L'] = clean(['LPG', 'غاز'])
        df['W'] = clean(['WATER REC', 'وارد'])
        df['S'] = clean(['SANIT', 'صرف'])

        # الحسابات
        avg_p = prod_qty / 30
        elec_kpi = (df['E'].mean() / avg_p) if avg_p > 0 else 0
        
        # خط الأساس الذكي (الجمعة + العطلات)
        df['DT'] = pd.to_datetime(df.get('DATE', df.index), errors='coerce')
        off_mask = (df['E'] < df['E'].mean() * 0.45) # أي يوم استهلاكه أقل من 45% من المعدل
        base_val = df[off_mask]['E'].mean() if off_mask.any() else df['E'].min()

        st.title(l['title'])
        
        # عرض المؤشرات بالألوان المتباينة
        st.subheader(l['summary'])
        c1, c2, c3 = st.columns(3)
        c1.metric("Electricity/KG", f"{elec_kpi:.3f} kWh")
        c2.metric("LPG Efficiency", f"{(df['L'].mean()/avg_p):.4f} kg")
        c3.metric("Water Loss", f"{(df['W'].sum()-df['S'].sum()):,.0f} m³")

        st.subheader(l['baselines'])
        b1, b2 = st.columns(2)
        b1.metric("Friday & Off Baseline", f"{base_val:,.1f} kWh")
        b2.metric("Daily Avg Water", f"{df['W'].mean():,.1f} m³")

        # رسم بياني متباين
        fig = px.line(df, y=['E', 'L'], title="Consumption Trends")
        fig.update_layout(template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True)

        # --- 4. التقرير الجذاب (HTML) ---
        st.markdown("---")
        if st.button(l['gen_report']):
            st.markdown(f"""
                <div class="report-card">
                    <h1 style="text-align:center; color:red; text-decoration: underline;">MONTHLY UTILITIES REPORT - AL SIDRA</h1>
                    <p style="font-size:18px;"><b>Selected Period:</b> {selected_month}</p>
                    <p style="font-size:18px;"><b>Target Production:</b> {prod_qty:,.0f} KG</p>
                    <hr style="border: 2px solid black;">
                    <table style="width:100%; border-collapse: collapse; font-size:20px;">
                        <tr style="background-color: black; color: white;">
                            <th style="padding:15px; border:2px solid black;">Metric Description</th>
                            <th style="padding:15px; border:2px solid black;">Analyzed Value</th>
                        </tr>
                        <tr>
                            <td style="padding:15px; border:1px solid black;">Energy Intensity (kWh/kg)</td>
                            <td style="padding:15px; border:1px solid black; color:red; font-weight:bold;">{elec_kpi:.3f}</td>
                        </tr>
                        <tr>
                            <td style="padding:15px; border:1px solid black;">Friday & Holiday Baseline</td>
                            <td style="padding:15px; border:1px solid black; color:green; font-weight:bold;">{base_val:,.1f} kWh</td>
                        </tr>
                        <tr>
                            <td style="padding:15px; border:1px solid black;">Total Monthly LPG</td>
                            <td style="padding:15px; border:1px solid black;">{df['L'].sum():,.0f} kg</td>
                        </tr>
                    </table>
                    <br>
                    <h3 style="text-align:right;">Maintenance Department Signature: _________________</h3>
                    <p style="text-align:center; color:blue;">(Press Ctrl+P to save this as a high-quality PDF)</p>
                </div>
            """, unsafe_allow_html=True)

    except Exception as e: st.error(f"Error: {e}")
else: st.info("Welcome! Please upload the Daily Report to generate insights.")
