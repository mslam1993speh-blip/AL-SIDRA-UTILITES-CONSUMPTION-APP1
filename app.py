import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة
st.set_page_config(page_title="نظام تحليل المرافق - سدرة", layout="wide")

st.title("📊 منظومة مراقبة استهلاك الطاقة والمرافق (2025)")
st.sidebar.header("لوحة التحكم")

# رفع الملف
uploaded_file = st.sidebar.file_uploader("ارفع ملف الإكسيل السنوي", type=['xlsx'])

if uploaded_file:
    # قراءة البيانات
    xl = pd.ExcelFile(uploaded_file)
    all_data = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df.rename(columns={'DAY': 'DATE'}, inplace=True)
        df = df[pd.to_numeric(df['DATE'], errors='coerce').notnull()]
        df['MONTH'] = sheet
        all_data.append(df)
    
    master_df = pd.concat(all_data, ignore_index=True)
    
    # تنظيف الأعمدة
    cols = ['ELECTRICITY (KWH)', 'LPG CONS (KG)', 'WATER CONS (M3)', 'SANITAION (M3)']
    for col in cols:
        if col in master_df.columns:
            master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)

    # عرض الإحصائيات السريعة (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الكهرباء", f"{master_df['ELECTRICITY (KWH)'].sum():,.0f} kWh")
    col2.metric("إجمالي الغاز (LPG)", f"{master_df['LPG CONS (KG)'].sum():,.0f} kg")
    col3.metric("إجمالي المياه", f"{master_df['WATER CONS (M3)'].sum():,.0f} m³")

    # رسم بياني تفاعلي
    st.subheader("📈 تحليل الاتجاهات الزمني")
    option = st.selectbox("اختر المعيار للتحليل", cols)
    fig = px.line(master_df, x='DATE', y=option, color='MONTH', title=f"تحليل استهلاك {option}")
    st.plotly_chart(fig, use_container_width=True)

    # مقارنة الأداء (Baseline)
    st.subheader("💡 مقارنة كفاءة التبريد (أيام الجمعة)")
    
    notes_col = next((c for c in master_df.columns if 'NOTE' in c or 'EVENT' in c), None)
    master_df['TYPE'] = master_df[notes_col].astype(str).str.upper().str.contains('FRIDAY|OFF').map({True:'Base Load (Cooling)', False:'Production Day'})
    
    fig2 = px.box(master_df, x='MONTH', y='ELECTRICITY (KWH)', color='TYPE', title="توزيع استهلاك الكهرباء بين الإنتاج والحمل الثابت")
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("الرجاء رفع ملف الإكسيل من القائمة الجانبية لتفعيل الداشبورد.")
