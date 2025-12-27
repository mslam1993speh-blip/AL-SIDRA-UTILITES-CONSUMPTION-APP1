# --- القائمة الجانبية (الشعار والمدخلات) ---
with st.sidebar:
    # عرض اللوجو بحجم مثالي ومنسق
    try:
        # استخدام ملفك المرفوع "al sidra new.jpg"
        st.image("al sidra new.jpg", use_container_width=True)
    except:
        # في حال عدم وجود الملف، يستخدم الرابط كبديل احتياطي
        st.markdown(f'''
            <div style="text-align: center;">
                <img src="https://raw.githubusercontent.com/mslam1993speh-blip/al-sidra-utilites-consumption-app1/main/logo.png" 
                     style="width: 180px; height: auto; object-fit: contain; margin-bottom: 20px;">
            </div>
        ''', unsafe_allow_html=True)
    
    st.button(l['lang_btn'], on_click=toggle_lang)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload DAILY REPORT 2025", type=['xlsx'])
    
    st.subheader("📦 Production Data")
    prod_qty = st.number_input("Chicken Production (KG)", min_value=1.0, value=150000.0)
    
    st.markdown("---")
    # عبارة الحقوق في الأسفل
    st.markdown(f"<div style='text-align:center; color:#888; font-size:12px; font-weight:bold;'>{l['footer']}</div>", unsafe_allow_html=True)
