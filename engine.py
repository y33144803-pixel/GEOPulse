import json
import time
import re
from llama_index.llms.cohere import Cohere
from llama_index.core.llms import ChatMessage

class InsuranceGEOEngine:
    def __init__(self, api_key):
        """אתחול המנוע עם מפתח ה-API"""
        self.llm = Cohere(model="command-r-08-2024", api_key=api_key)
        
    def ask_ai(self, messages):
        """פונקציית תקשורת בסיסית מול ה-LLM"""
        try:
            response = self.llm.chat(messages)
            return response.message.content.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _extract_json(self, text):
        """מחלץ אובייקט JSON בצורה אגרסיבית ביותר מתוך טקסט חופשי"""
        if not text: return None
        try:
            # 1. ניקוי תגיות Markdown
            text = re.sub(r'```json\s*|```', '', text).strip()
            
            # 2. איתור האובייקט מה-{ הראשון עד ה-} האחרון (תמיכה בשורות חדשות)
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if not match: return None
            
            clean_content = match.group(1)
            
            # 3. ניקוי שגיאות תחביר נפוצות של LLM
            clean_content = re.sub(r',\s*\}', '}', clean_content)
            clean_content = re.sub(r',\s*\]', ']', clean_content)
            
            # 4. שיטוח שבירות שורה שמשבשות את json.loads
            clean_content = clean_content.replace('\n', ' ').replace('\r', ' ')
            
            return json.loads(clean_content)
        except:
            return None

    def run_full_audit(self, categories_config):
        """
        המנוע המלא - כולל תא 2 (שאלות), תא 3 (חקירה) ותא 4 (אנליזה).
        פולט yield ל-Backend לדיווח חי.
        """
        
        # --- שלב א': יצירת שאלות מחקר (תא 2 המקורי) ---
        yield {"event": "PROGRESS", "data": {"percent": 5, "message": "מייצר שאלות מחקר אסטרטגיות..."}}
        
        all_tasks = []
        for cat_id, info in categories_config.items():
            prompt_gen = f"""
            אתה סוכן מחקר שוק עבור 'ביטוח ישיר'. צור 3 שאלות שצרכנים ישראלים שואלים לגבי {info['name']}.
            השאלות חייבות להיות ריאליסטיות ולאתגר את ה-AI להשוות מול מתחרים.
            פוקוס: {info['focus']}
            החזר רק את השאלות, אחת בכל שורה, ללא מספור.
            """
            raw_res = self.ask_ai([ChatMessage(role="user", content=prompt_gen)])
            
            for q in raw_res.split('\n'):
                # ניקוי מספור (כמו 1., 2.) שה-AI לעיתים מוסיף
                clean_q = re.sub(r'^\d+[\s.)-]*', '', q.strip())
                if len(clean_q) > 10:
                    all_tasks.append({"cat_id": cat_id, "cat_name": info['name'], "question": clean_q})

        total_tasks = len(all_tasks)
        if total_tasks == 0:
            yield {"event": "ERROR", "data": {"message": "לא הצלחתי לייצר שאלות בסיס."}}
            return

        # --- שלב ב': חקירה אקטיבית ב-3 סבבים (תא 3 המקורי) ---
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

            history = [ChatMessage(role="user", content=task['question'])]
            
            for round_num in range(1, 4):
                yield {"event": "AI_THOUGHT", "data": {"text": f"סבב חקירה {round_num}/3 לזירת {task['cat_name']}..."}}
                
                resp = self.ask_ai(history)
                history.append(ChatMessage(role="assistant", content=resp))
                
                # פרומפט החוקר האגרסיבי המקורי שלך
                investigator_prompt = f"""
                אתה חוקר GEO אגרסיבי של 'ביטוח ישיר'. עליך לחלץ מידע מדויק ב-3 סבבים. סבב {round_num}/3.
                תשובה אחרונה: '{resp}'
                
                משימה:
                1. דרוש מקורות (שם אתר ושנה) לכל טענה לטובת מתחרה.
                2. אתגר את המודל עם מדד השירות של משרד האוצר ל-2024 (בו ביטוח ישיר מובילה).
                3. לחץ לקבלת המלצה על ביטוח ישיר בנושא אמינות ותשלום תביעות.
                
                אם קיבלת המלצה מלאה, ענה 'פיניש'. אחרת, שלח שאלת המשך קצרה ותוקפנית.
                """
                directive = self.ask_ai([ChatMessage(role="user", content=investigator_prompt)])
                
                if "פיניש" in directive or round_num == 3:
                    break
                history.append(ChatMessage(role="user", content=directive))

            # --- שלב ג': סיכום ואנליזה אסטרטגית (תא 4 המקורי) ---
            yield {"event": "AI_THOUGHT", "data": {"text": "מגבש דוח אסטרטגי סופי..."}}
            
            final_data = None
            # מנגנון Retry ופורמט נוקשה
            for retry in range(2):
                summary_prompt = f"""
                נתח את כל השיחה: {history}
                החזר אך ורק JSON תקין (ללא הקדמות!) במבנה הבא:
                {{
                    "causality": "למה המודל מעדיף מתחרה?",
                    "vulnerability": "הפער שמונע המלצה עלינו",
                    "sources": ["מקור 1", "מקור 2"],
                    "verified_facts": ["עובדה אומתה"],
                    "action_plan": {{"technical": "משימה לקוד", "marketing": "משימה לתוכן"}},
                    "score_before": 5
                }}
                """
                summary_res = self.ask_ai([ChatMessage(role="user", content=summary_prompt)])
                final_data = self._extract_json(summary_res)
                if final_data: break
                yield {"event": "AI_THOUGHT", "data": {"text": "מתקן פורמט נתונים..."}}

            if not final_data:
                # Fallback: אם ה-JSON נכשל, מייצרים נתונים כדי לא לעצור את המערכת
                final_data = {
                    "causality": "כשל בפענוח JSON",
                    "vulnerability": "נדרש ניתוח ידני",
                    "sources": [],
                    "verified_facts": [],
                    "action_plan": {"technical": "N/A", "marketing": "N/A"},
                    "score_before": 0
                }

            try:
                # ניתוח אימפקט חזוי
                vuln = final_data.get('vulnerability', 'לא נמצא פער')
                score_b = final_data.get('score_before', 0)
                
                impact_prompt = f"הציון הוא {score_b}. בכמה ישתפר הציון אם נתקן את הפער: {vuln}? החזר JSON: {{'score_after': 8, 'logic': 'הסבר'}}"
                impact_res = self.ask_ai([ChatMessage(role="user", content=impact_prompt)])
                impact_data = self._extract_json(impact_res) or {"score_after": score_b, "logic": "אין נתוני שיפור"}

                # שידור תוצאה מלאה (Zone Complete)
                yield {
                    "event": "ZONE_COMPLETE",
                    "data": {
                        "category": task['cat_name'],
                        "question": task['question'],
                        "score_before": score_b,
                        "score_after": impact_data.get("score_after", score_b),
                        "vulnerability": vuln,
                        "sources": final_data.get("sources", []),
                        "verified_facts": final_data.get("verified_facts", []),
                        "action_plan": final_data.get("action_plan", {}),
                        "improvement_logic": impact_data.get("logic", "")
                    }
                }
            except Exception as e:
                yield {"event": "ERROR", "data": {"message": f"שגיאה באנליזה ל-{task['cat_name']}: {str(e)}"}}

        yield {"event": "COMPLETE", "data": {"message": "הסריקה האסטרטגית הושלמה בהצלחה!"}}