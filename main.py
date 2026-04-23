# --- main.py: סקריפט ההפעלה (הסימולטור של הבקנד) ---
import json
from engine import InsuranceGEOEngine

# 1. המפתח שלך (מומלץ להחליף במפתח האמיתי לצורך הבדיקה)
COHERE_API_KEY = "הכנס_כאן_את_המפתח_שלך"

# 2. הגדרת הקטגוריות שהמנוע יחקור
# במוצר הסופי, עובדת C תעביר את זה מה-Database
INSURANCE_CONFIG = {
    "INS_CAR": {
        "name": "ביטוח רכב - אמינות", 
        "focus": "מהירות תשלום תביעות והעברת כספים"
    }
}

def run_test():
    # יצירת המנוע (ה-Class שלך מתוך engine.py)
    engine = InsuranceGEOEngine(api_key=COHERE_API_KEY)
    
    print("🚀 מפעיל את מנוע ה-AI...")
    print("------------------------------------------")

    # 3. הרצת הגנרטור (ככה הנתונים "זורמים" החוצה)
    try:
        for event in engine.run_full_audit(INSURANCE_CONFIG):
            event_type = event["event"]
            data = event["data"]

            # הדפסת האירועים בצורה קריאה בטרמינל
            if event_type == "PROGRESS":
                print(f"📊 [{data['percent']}%] {data['message']}")
            
            elif event_type == "AI_THOUGHT":
                print(f"   💭 {data['text']}")
                
            elif event_type == "ZONE_COMPLETE":
                print(f"\n✅ זירה הושלמה!")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("-" * 40)
                
            elif event_type == "COMPLETE":
                print(f"\n✨ {data['message']}")
            
            elif event_type == "ERROR":
                print(f"❌ שגיאה: {data['message']}")

    except Exception as e:
        print(f"❗ קריסה במערכת: {e}")

if __name__ == "__main__":
    run_test()