import os
import sys
import io
import json
from dotenv import load_dotenv
from engine import InsuranceGEOEngine

# תיקון עברית לטרמינל
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# טעינה מה-env
load_dotenv()

def run_test():
    # משיכת המפתח
    raw_key = os.getenv("COHERE_API_KEY")
    
    # בדיקה קריטית: האם המפתח מכיל עברית או טקסט ברירת מחדל?
    if not raw_key or "הכנס" in raw_key or "YOUR_API_KEY" in raw_key:
        print("❌ שגיאה: מפתח ה-API ב-env לא תקין!")
        print(f"ערך נוכחי שנמצא: {raw_key}")
        return

    # אתחול המנוע
    engine = InsuranceGEOEngine(raw_key)

    categories = {
        "car_reliability": {
            "name": "ביטוח רכב - אמינות",
            "focus": "אמינות תשלום תביעות, מהירות שירות, השוואה למתחרים"
        }
    }

    print("🚀 מפעיל את מנוע ה-AI...")
    print("-" * 42)

    for event in engine.run_full_audit(categories):
        event_type = event["event"]
        data = event["data"]

        if event_type == "PROGRESS":
            print(f"📊 [{data['percent']}%] {data['message']}")
            if "current_item" in data:
                print(f"   🔎 חוקר: {data['current_item']}")

        elif event_type == "AI_THOUGHT":
            print(f"   💭 {data['text']}")

        elif event_type == "ZONE_COMPLETE":
            print("\n✅ זירה הושלמה!")
            # ensure_ascii=False הוא קריטי להצגת עברית תקינה
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("-" * 40)

        elif event_type == "ERROR":
            print(f"❌ שגיאה: {data['message']}")

        elif event_type == "COMPLETE":
            print(f"\n✨ {data['message']}")

if __name__ == "__main__":
    run_test()