import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Utilities System", layout="wide")
st.title("Utilities Monthly Report System")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
prod_qty = st.number_input("Total Monthly Production (KG)", min_value=1.0, value=150000.0)

# ---------------- PDF FUNCTION ----------------
def generate_pdf(month, df, prod_qty):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "UTILITIES MONTHLY REPORT")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Month: {month}")

    y = height - 130
    c.setFont("Helvetica", 10)

    total_elec = df["ELEC"].sum()
    total_lpg = df["LPG"].sum()
    total_water = df["W_IN"].sum()
    water_loss = df["W_IN"].sum() - df["W_OUT"].sum()
    avg_daily_prod = prod_qty / 30

    lines = [
        f"Total Electricity: {total_elec:,.0f} kWh",
        f"Total LPG: {total_lpg:,.0f} kg",
        f"Total Water In: {total_water:,.1f} m3",
        f"Water Loss: {water_loss:,.1f} m3",
        "-" * 40,
        f"Electricity per KG: {(df['ELEC'].mean()/avg_daily_prod):.4f} kWh/kg",
        f"LPG per KG: {(df['LPG'].mean()/avg_daily_prod):.5f} kg/kg",
        f"Water per KG: {(df['W_IN'].mean()/avg_daily_prod*1000):.2f} L/kg"
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 18

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ---------------- MAIN ----------------
if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    dfs = []

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df["MONTH"] = sheet
        dfs.append(df)

    full_df = pd.concat(dfs, ignore_index=True)

    def find_col(keys):
        for col in full_df.columns:
            if any(k in col for k in keys):
                return pd.to_numeric(full_df[col], errors="coerce").fillna(0)
        return 0

    full_df["ELEC"] = find_col(["ELEC", "كهرب"])
    full_df["LPG"] = find_col(["LPG", "غاز"])
    full_df["W_IN"] = find_col(["WATER", "وارد"])
    full_df["W_OUT"] = find_col(["SANIT", "صرف"])

    months = full_df["MONTH"].unique().tolist()
    selected_month = st.selectbox("Select Month", months)

    df = full_df[full_df["MONTH"] == selected_month]

    st.subheader("Monthly Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Electricity", f"{df['ELEC'].sum():,.0f} kWh")
    c2.metric("LPG", f"{df['LPG'].sum():,.0f} kg")
    c3.metric("Water In", f"{df['W_IN'].sum():,.1f} m3")
    c4.metric("Water Loss", f"{(df['W_IN'].sum()-df['W_OUT'].sum()):,.1f} m3")

    st.plotly_chart(
        px.line(df, y=["ELEC", "LPG", "W_IN"], title="Daily Consumption"),
        use_container_width=True
    )

    pdf = generate_pdf(selected_month, df, prod_qty)
    st.download_button(
        "📄 Download Monthly PDF",
        data=pdf,
        file_name=f"{selected_month}_Utilities_Report.pdf",
        mime="application/pdf"
    )
else:
    st.info("Upload Excel file to start")
