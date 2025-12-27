import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="Sidra Utilities Dashboard", layout="wide")

# تنسيق العنوان
st.markdown("<h1 style='text-align: center; color: #2E7D32;'>📊 نظام مراقبة وتحليل مرافق سدرة - 2025</h1>", unsafe_allow_html=True)
st.markdown("---")

# القائمة الجانبية للتحكم
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    uploaded_file = st.file_uploader("ارفع ملف DAILY REPORT 2025", type=['xlsx'])
    st.info("قم برفع ملف الإكسيل لظهور التقارير تلقائياً")

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
    
    # تنظيف الأرقام (تأكد أن أسماء الأعمدة مطابقة لملفك)
    cols = {'ELECTRICITY (KWH)': 'الكهرباء', 'LPG CONS (KG)': 'الغاز', 'WATER CONS (M3)': 'المياه'}
    for eng_col, arb_col in cols.items():
        if eng_col in df.columns:
            df[eng_col] = pd.to_numeric(df[eng_col], errors='coerce').fillna(0)

    # --- القسم الأول: مؤشرات الأداء الرئيسية (KPIs) ---
    st.subheader("📌 مؤشرات الاستهلاك الإجمالية")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric("إجمالي الكهرباء (kWh)", f"{df['ELECTRICITY (KWH)'].sum():,.0f}", delta="سنوي")
    with kpi2:
        st.metric("إجمالي الغاز (kg)", f"{df['LPG CONS (KG)'].sum():,.0f}", delta_color="inverse")
    with kpi3:
        st.metric("إجمالي المياه (m³)", f"{df['WATER CONS (M3)'].sum():,.0f}")

    st.markdown("---")

    # --- القسم الثاني: التقارير والرسوم البيانية ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 توجه الاستهلاك الشهري")
        monthly_data = df.groupby('MONTH')['ELECTRICITY (KWH)'].sum().reset_index()
        fig_line = px.line(df, x='DATE', y='ELECTRICITY (KWH)', color='MONTH', title="الاستهلاك اليومي لكل شهر")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.subheader("📊 توزيع الاستهلاك حسب المرفق")
        totals = [df['ELECTRICITY (KWH)'].sum(), df['LPG CONS (KG)'].sum(), df['WATER CONS (M3)'].sum()]
        fig_pie = px.pie(values=totals, names=['الكهرباء', 'الغاز', 'المياه'], hole=0.4, title="نسبة الاستهلاك العام")
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- القسم الثالث: جدول التقارير المفصل ---
    st.subheader("📋 تقرير البيانات التفصيلي")
    st.dataframe(df[['MONTH', 'DATE', 'ELECTRICITY (KWH)', 'LPG CONS (KG)', 'WATER CONS (M3)']], use_container_width=True)

else:
    # رسالة ترحيبية في حال عدم وجود ملف
    st.warning("⚠️ بانتظار رفع ملف البيانات من القائمة الجانبية لتوليد التقارير...")
