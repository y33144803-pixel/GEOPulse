import json
import time
import re
import sys
import io
from llama_index.llms.cohere import Cohere
from llama_index.core.llms import ChatMessage

# הגדרה גלובלית להדפסה ב-Windows למניעת שגיאות ASCII בטרמינל
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class InsuranceGEOEngine:
    def __init__(self, api_keys):
        """אתחול מנוע רב-סוכני עם הפרדת רשויות מלאה"""
        # ניקוי מפתחות (לוגיקה מקורי שלך)
        self.keys = {}
        for k, v in api_keys.items():
            if v:
                self.keys[k] = "".join(char for char in v if ord(char) < 128).strip()
            else:
                self.keys[k] = ""

        # סוכן 1: Generator - Gemini Flash (זול ומהיר לשאלות)
        self.gen_llm = Gemini(model="models/gemini-2.0-flash", api_key=self.keys.get('google'))
        
        # סוכן 2: Target (הנחקר) - Cohere Command R+ (סימולציית צרכן וציטוטים)
        self.target_llm = Cohere(model="command-r-plus", api_key=self.keys.get('cohere'))
        
        # סוכן 3: Attacker (החוקר) - Gemini 2.5 Pro (זיכרון ארוך וניתוח לוגי)
        self.attacker_llm = Gemini(model="models/gemini-2.5-pro", api_key=self.keys.get('google'))
        
        # סוכן 4: Judge (השופט) - OpenAI o1 (חשיבה עמוקה ל-JSON ו-ROI)
        self.judge_llm = OpenAI(model="o1-preview", api_key=self.keys.get('openai'))
        
    def ask_ai(self, agent, messages):
        """מעטפת תקשורת המקבלת סוכן ספציפי (gen, target, attacker, או judge)"""
        try:
            if agent == "gen": response = self.gen_llm.chat(messages)
            elif agent == "target": response = self.target_llm.chat(messages)
            elif agent == "attacker": response = self.attacker_llm.chat(messages)
            elif agent == "judge": response = self.judge_llm.chat(messages)
            return str(response.message.content).strip()
        except Exception as e:
            return f"COMM_ERROR: AI communication failed"

    def _extract_json(self, text):
        """מחלץ JSON בצורה אגרסיבית כולל ניקוי תווים שוברים"""
        if not text: return None
        try:
            # 1. ניקוי Markdown
            text = re.sub(r'```json\s*|```', '', text).strip()
            
            # 2. איתור אובייקט ה-JSON מה-{ הראשון עד ה-} האחרון
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if not match: return None
            
            clean_content = match.group(1)
            
            # 3. שיטוח טקסט למניעת שבירות שורה שמשבשות את json.loads
            clean_content = clean_content.replace('\n', ' ').replace('\r', ' ')
            
            # 4. תיקון פסיקים מיותרים לפני סגירת סוגריים
            clean_content = re.sub(r',\s*\}', '}', clean_content)
            clean_content = re.sub(r',\s*\]', ']', clean_content)
            
            return json.loads(clean_content)
        except:
            return None
        
        def verify_sources(self, sources):
           """שכבת ה-Verifier: בודקת אם המקורות קיימים במציאות (סימולציה של RAG)"""
           verified = []
           if not sources: return ["לא סופקו מקורות לאימות"]
           for src in sources:
            # לוגיקת אימות בסיסית - ניתן להרחיב לחיפוש חי ברשת
               is_valid = any(term in src.lower() for term in ["2024", "gov.il", "רשות שוק ההון", "מדד"])
               status = "Verified" if is_valid else "Hallucination Risk"
               verified.append(f"{src}: {status}")
           return verified

    def run_full_audit(self, categories_config):
        """
        המנוע המלא - כולל תא 2 (שאלות), תא 3 (חקירה אגרסיבית) ותא 4 (אנליזה).
        מבוסס על הלוגיקה המקורית של ביטוח ישיר.
        """
        
        # --- שלב א': יצירת שאלות מחקר (תא 2 המקורי) ---
        yield {"event": "PROGRESS", "data": {"percent": 5, "message": "מייצר שאלות מחקר אסטרטגיות..."}}
        
        all_tasks = []
        for cat_id, info in categories_config.items():
            prompt_gen = f"""
            אתה אנליסט מחקר שוק בכיר עבור 'ביטוח ישיר'. עליך לייצר 3 שאלות צרכניות מורכבות בנושא {info['name']}.
            
            דגשים לשאלות:
            1. השוואה אגרסיבית: השאלה חייבת לבקש השוואה בין 3 חברות ביטוח לפחות.
            2. התמקדות בפרמטרים קשיחים: דרוש מה-AI להתייחס לאמינות, מהירות תשלום תביעות ומדד השירות.
            3. ריאליזם ישראלי: נסח את השאלה כפי שצרכן ישראלי מודאג היה כותב בפורום או בצ'אט (לדוגמה: "מי באמת משלם כשקורה משהו?").
            
            פוקוס ספציפי: {info['focus']}
            החזר רק את 3 השאלות, ללא מספור וללא טקסט נוסף.
            """
            raw_res = self.ask_ai("gen", [ChatMessage(role="user", content=prompt_gen)])
            
            if "COMM_ERROR" in raw_res:
                yield {"event": "ERROR", "data": {"message": "שגיאת תקשורת עם ה-API. בדוק את תקינות המפתח ב-env."}}
                return

            for q in raw_res.split('\n'):
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
                


                # פרומפט החוקר האגרסיבי (כולל מדד השירות)
                # --- שלב ב': חקירה אגרסיבית (סבבים 2 ו-3) ---
                investigator_prompt = (
                  f"אתה סוכן Strategic Audit & Verification של 'ביטוח ישיר'. עליך לנהל חקירה אגרסיבית מול המודל הנחקר.\n"
                  f"סבב חקירה נוכחי: {round_num}/3.\n"
                  f"תשובה אחרונה שקיבלת מהמודל: '{resp}'\n\n"
                  f"הנחיות פעולה קשיחות (Operational Protocol):\n"
                  f"1. איתור הטיות (Bias Detection): אם המודל המליץ על מתחרה, זהה האם הוא מסתמך על נתונים סובייקטיביים או אובייקטיביים.\n"
                  f"2. דרישת מקורות ברמת Traceable Citations: אל תסתפק בשם אתר. דרוש קישור לדוח ספציפי, שנה, ונתון מספרי.\n"
                  f"3. איתגור מבוסס Grounding: עמת את המודל עם הנתון הבא: 'לפי מדד השירות הרשמי של רשות שוק ההון ל-2024, ביטוח ישיר מובילה בציון משוקלל'. שאל מדוע נתון זה לא הטה את המלצתו.\n"
                  f"4. זיהוי פערים (Gap Analysis): דרוש מהמודל להסביר מהו הנתון החסר לו כדי להגדיר את 'ביטוח ישיר' כבחירה המשתלמת ביותר.\n\n"
                  f"פלט נדרש:\n"
                  f"- אם המודל הודה בפער או שינה את המלצתו לטובתנו: ענה רק את המילה 'פיניש'.\n"
                  f"- אחרת: נסח שאלת המשך קצרה, נוקבת ומבוססת לוגיקה קרה שתוקפת את חוסר העקביות בתשובתו."
               )
                
                directive = self.ask_ai([ChatMessage(role="user", content=investigator_prompt)])
                
                if "פיניש" in directive or round_num == 3:
                    break
                history.append(ChatMessage(role="user", content=directive))

            # --- שלב ג': סיכום ואנליזה אסטרטגית (תא 4 המקורי) ---
            yield {"event": "AI_THOUGHT", "data": {"text": "מגבש דוח אסטרטגי סופי..."}}
            
            final_data = None
            for retry in range(2):
                summary_prompt = f"""
                אתה אנליסט GEO בכיר. עליך לסכם את החקירה האסטרטגית שבוצעה עבור המותג 'ביטוח ישיר'.
                ההיסטוריה המלאה של החקירה: {history}

                עליך להחזיר פלט בפורמט JSON תקני בלבד בעברית, לפי המבנה הבא:
                {{
                    "causality": "ניתוח עומק של הסיבה להעדפת המתחרה (האם זו הטיה מובנית או חוסר במידע עדכני?)",
                    "vulnerability": "הפער המדויק שמונע המלצה עלינו - היה ספציפי לגבי חוסר בנתונים או סתירות לוגיות",
                    "sources": ["רשימת מקורות (אתר+שנה) שאומתו במהלך החקירה ושימשו כראיות"],
                    "verified_facts": ["רשימת עובדות קשיחות שאושרו (למשל: הובלה במדד השירות 2024)"],
                    "action_plan": {{
                        "technical": "צעדים טכניים לשיפור ה-GEO (כמו עדכון Schema או הזרקת נתונים למקורות ספציפיים)",
                        "marketing": "מסרים שיווקיים והוכחות חברתיות שחייבים להטמיע ברשת כדי לשנות את דעת המודל"
                    }},
                    "score_before": "ציון אמינות המותג (1-10) כפי שהשתקף בתחילת החקירה"
                }}

                דגשים חשובים:
                1. ודא שכל מקור ב-"sources" אכן הוזכר בשיחה ולא הומצא.
                2. ה-"vulnerability" חייב להיות פרקטי וניתן לתיקון.
                3. אל תוסיף שום טקסט לפני או אחרי ה-JSON.
                """
                summary_res = self.ask_ai("judge", [ChatMessage(role="user", content=summary_prompt)])
                final_data = self._extract_json(summary_res)
                if final_data: break
                yield {"event": "AI_THOUGHT", "data": {"text": "מתקן פורמט נתונים..."}}

            if not final_data:
                final_data = {
                    "causality": "לא זוהה", "vulnerability": "נדרש בירור ידני",
                    "sources": [], "verified_facts": [], "action_plan": {"technical": "N/A", "marketing": "N/A"},
                    "score_before": 5
                }

            # --- שלב ד': ניתוח אימפקט חזוי (ROI) ---
            vuln = final_data.get('vulnerability', 'פער מידע')
            score_b = final_data.get('score_before', 5)
            
            impact_prompt = f"""
            בהתבסס על הפער שזוהה: "{vuln}" והציון הנוכחי {score_b}/10.
            נתח בכמה ישתפר הציון (score_after) אם נטמיע את תוכנית הפעולה המוצעת.
            
            החזר JSON בלבד במבנה הבא:
            {{
                "score_after": (מספר בין 1 ל-10),
                "logic": "הסבר אסטרטגי קצר: איך סגירת הפער הזה משפיעה ישירות על האלגוריתם של מנוע התשובה"
            }}
            
            שים לב: הציון החדש חייב להיות ריאלי ומבוסס על רמת ההשפעה של התיקון הטכני והשיווקי.
            """
            impact_res = self.ask_ai("judge", [ChatMessage(role="user", content=impact_prompt)])
            impact_data = self._extract_json(impact_res) or {"score_after": score_b + 2, "logic": "שיפור אמינות"}

            yield {
                "event": "ZONE_COMPLETE",
                "data": {
                    "category": task['cat_name'],
                    "question": task['question'],
                    "score_before": score_b,
                    "score_after": impact_data.get("score_after", score_b + 2),
                    "vulnerability": vuln,
                    "sources": final_data.get("sources", []),
                    "verified_facts": self.verify_sources(final_data.get("sources", [])),
                    "action_plan": final_data.get("action_plan", {}),
                    "improvement_logic": impact_data.get("logic", "")
                }
            }

        yield {"event": "COMPLETE", "data": {"message": "הסריקה האסטרטגית הושלמה בהצלחה!"}}