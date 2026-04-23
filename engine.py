import json
import time
import re
from llama_index.llms.cohere import Cohere
from llama_index.core.llms import ChatMessage

class InsuranceGEOEngine:
    def __init__(self, api_key):
        """אתחול מנוע ה-AI - לב המוצר"""
        self.llm = Cohere(model="command-r-08-2024", api_key=api_key)
        
    def ask_ai(self, messages):
        """פונקציית עזר לתקשורת מול המודל"""
        try:
            response = self.llm.chat(messages)
            return response.message.content.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _extract_json(self, text):
        """מחלץ JSON בצורה אגרסיבית כולל ניקוי Markdown ושאריות טקסט"""
        try:
            # ניקוי תגיות Markdown של JSON אם קיימות
            text = re.sub(r'```json\s*|```', '', text).strip()
            
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                return None
            
            clean_content = text[start:end]
            # ניקוי שגיאות נפוצות של LLM כמו פסיק מיותר לפני סגירת סוגריים
            clean_content = re.sub(r',\s*}', '}', clean_content)
            clean_content = re.sub(r',\s*]', ']', clean_content)
            
            return json.loads(clean_content)
        except:
            return None

    def run_full_audit(self, categories_config):
        """
        הפונקציה המרכזית כ-Generator. 
        משדרת אירועים בלייב ל-Backend/Frontend.
        """
        
        # --- שלב א': יצירת שאלות מחקר ---
        yield {"event": "PROGRESS", "data": {"percent": 5, "message": "מייצר שאלות מחקר ריאליסטיות..."}}
        
        all_tasks = []
        for cat_id, info in categories_config.items():
            prompt_gen = f"צור 3 שאלות צרכניות קצרות בעברית לגבי {info['name']}. פוקוס: {info['focus']}. החזר רק את השאלות, ללא מספור או טקסט נוסף."
            raw_res = self.ask_ai([ChatMessage(role="user", content=prompt_gen)])
            
            for q in raw_res.split('\n'):
                # ניקוי תווים מיותרים ומספור שה-AI עלול להוסיף
                clean_q = re.sub(r'^\d+[\s.)-]*', '', q.strip())
                if len(clean_q) > 10:
                    all_tasks.append({"cat_id": cat_id, "cat_name": info['name'], "question": clean_q})

        total_tasks = len(all_tasks)
        if total_tasks == 0:
            yield {"event": "ERROR", "data": {"message": "לא הצלחתי לייצר שאלות מחקר."}}
            return

        # --- שלב ב' + ג': חקירה ואנליזה אסטרטגית ---
        for i, task in enumerate(all_tasks):
            current_pct = int((i / total_tasks) * 90) + 5
            yield {
                "event": "PROGRESS", 
                "data": {
                    "percent": current_pct,
                    "message": f"חוקר זירה: {task['cat_name']}",
                    "current_item": task['question']
                }
            }

            # לוגיקת החקירה (3 סבבים)
            history = [ChatMessage(role="user", content=task['question'])]
            for round_num in range(1, 4):
                yield {"event": "AI_THOUGHT", "data": {"text": f"חוקר סבב {round_num}/3 לזירת {task['cat_name']}..."}}
                
                resp = self.ask_ai(history)
                history.append(ChatMessage(role="assistant", content=resp))
                
                investigator_prompt = f"""
                אתה חוקר GEO אגרסיבי של 'ביטוח ישיר'. עליך לחלץ מידע מדויק.
                זהו סבב מספר {round_num} מתוך 3.
                תשובה אחרונה שקיבלת מהמודל: '{resp}'
                
                הנחיות:
                1. אם צוין מתחרה, דרוש שם אתר ושנה של המקור.
                2. אתגר את המודל עם מדד השירות של משרד האוצר ל-2024.
                3. לחץ לקבלת תשובה חד משמעית לגבי אמינות תשלום התביעות של ביטוח ישיר.
                
                אם קיבלת המלצה מלאה, ענה 'פיניש'. אחרת, שלח שאלת המשך קצרה ותוקפנית.
                """
                directive = self.ask_ai([ChatMessage(role="user", content=investigator_prompt)])
                
                if "פיניש" in directive or round_num == 3:
                    break
                history.append(ChatMessage(role="user", content=directive))

            # --- שלב הסיכום עם Retry פנימי ל-JSON ---
            yield {"event": "AI_THOUGHT", "data": {"text": "מגבש דוח אסטרטגי וסיכום נתונים..."}}
            
            data = None
            for retry in range(2): # ניסיון שני אם הראשון נכשל
                summary_prompt = f"""
                נתח את החקירה: {history}
                החזר אך ורק JSON תקין (ללא טקסט נוסף!).
                מבנה נדרש:
                {{
                    "causality": "...",
                    "vulnerability": "...",
                    "sources": [],
                    "verified_facts": [],
                    "action_plan": {{"technical": "...", "marketing": "..."}},
                    "score_before": 5
                }}
                """
                summary_res = self.ask_ai([ChatMessage(role="user", content=summary_prompt)])
                data = self._extract_json(summary_res)
                if data: break
                yield {"event": "AI_THOUGHT", "data": {"text": "מנסה לתקן פורמט נתונים..."}}

            if not data:
                yield {"event": "ERROR", "data": {"message": f"כשל בפענוח נתוני זירת {task['cat_name']}"}}
                continue

            try:
                # חישוב אימפקט חזוי
                vulnerability = data.get('vulnerability', 'לא נמצא פער')
                score_before = data.get('score_before', 0)
                
                impact_prompt = f"הציון הנוכחי הוא {score_before}. בכמה ישתפר אם נתקן את: {vulnerability}? החזר JSON: {{'score_after': 8, 'logic': 'הסבר'}}"
                impact_res = self.ask_ai([ChatMessage(role="user", content=impact_prompt)])
                impact_data = self._extract_json(impact_res) or {"score_after": score_before, "logic": "לא ניתן לחשב"}

                # שידור התוצאה המלאה של הזירה
                yield {
                    "event": "ZONE_COMPLETE",
                    "data": {
                        "category": task['cat_name'],
                        "question": task['question'],
                        "score_before": score_before,
                        "score_after": impact_data.get("score_after", score_before),
                        "vulnerability": vulnerability,
                        "sources": data.get("sources", []),
                        "verified_facts": data.get("verified_facts", []),
                        "action_plan": data.get("action_plan", {}),
                        "improvement_logic": impact_data.get("logic", "")
                    }
                }
            except Exception as e:
                yield {"event": "ERROR", "data": {"message": f"שגיאה בניתוח סופי של {task['cat_name']}: {str(e)}"}}

        yield {"event": "COMPLETE", "data": {"message": "הסריקה האסטרטגית הושלמה בהצלחה!"}}