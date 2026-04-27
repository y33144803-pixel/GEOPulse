import streamlit as st
import json
from engine import InsuranceGEOEngine # מוודא שהקובץ המקורי שלך נקרא כך

st.set_page_config(page_title="GEO Strategy Engine", layout="wide")

st.title("🛡️ מנוע ניתוח אסטרטגי - GEO 2026")
st.subheader("גלה מה מודלי AI חושבים על המותג שלך")

# תפריט צד להגדרות
with st.sidebar:
    st.header("הגדרות סריקה")
    target_category = st.selectbox("בחר זירת פעילות:", [
        "ביטוח רכב", "ביטוח נסיעות", "ביטוח דירה", "שירות לקוחות"
    ])
    focus_area = st.text_input("מיקוד אסטרטגי:", "אמינות ומהירות תשלום תביעות")
    run_button = st.button("הפעל סריקה אסטרטגית 🚀")

if run_button:
    engine = InsuranceGEOEngine()
    
    # יצירת הקונפיגורציה להרצה
    config = {
        "CAT_USER": {"name": target_category, "focus": focus_area}
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    logs_area = st.expander("לוג חקירה בזמן אמת (AI Thought Process)", expanded=True)

    # הרצת המנוע ועדכון הממשק
    for step in engine.run_full_audit(config):
        if step['event'] == 'PROGRESS':
            progress_bar.progress(step['data']['percent'] / 100)
            status_text.write(f"**סטטוס:** {step['data']['message']}")
        
        elif step['event'] == 'AI_THOUGHT':
            logs_area.write(f"🤖 {step['data']['text']}")
        
        elif step['event'] == 'ZONE_COMPLETE':
            data = step['data']
            st.success(f"הסריקה לזירת {data['category']} הושלמה!")
            
            # הצגת תוצאות בלוח מחוונים
            col1, col2, col3 = st.columns(3)
            col1.metric("ציון נוכחי (לפני)", f"{data['score_before']}/10")
            col2.metric("ציון חזוי (אחרי תיקון)", f"{data['score_after']}/10")
            col3.info(f"פער מרכזי: {data['vulnerability']}")

            st.divider()
            
            # תוכנית פעולה
            st.subheader("📋 תוכנית פעולה אסטרטגית")
            c1, c2 = st.columns(2)
            with c1:
                st.warning("עבודה טכנית (GEO Fix)")
                st.write(data['action_plan']['technical'])
            with c2:
                st.warning("עבודה שיווקית (Content)")
                st.write(data['action_plan']['marketing'])

            # מקורות ועובדות
            st.subheader("🧐 מקורות ועובדות שאומתו")
            st.write(data['verified_facts'])