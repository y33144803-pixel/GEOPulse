import os
import json
import re
import sys
import io
import warnings
import httpx
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.llms.cohere import Cohere
from llama_index.core.llms import ChatMessage
from datetime import datetime


# הגדרות קידוד ל-Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings("ignore")

class InsuranceGEOEngine:

    def __init__(self):
        load_dotenv()
        self.openai_key = os.getenv('OPENAI_API_KEY', '').strip().replace('"', '')
        unsafe_client = httpx.Client(verify=False)

        # סוכן 1+3: מודלים מהירים
        self.gen_llm = OpenAI(model="gpt-4o-mini", api_key=self.openai_key, http_client=unsafe_client)
        self.attacker_llm = OpenAI(model="gpt-4o-mini", api_key=self.openai_key, http_client=unsafe_client)

        # סוכן 2: Target - מעבר ל-GPT-4o לקבלת המידע הכי מעודכן ל-2026
        self.target_llm = OpenAI(model="gpt-4o", api_key=self.openai_key, http_client=unsafe_client)

        # סוכן 4: Judge - המוח האסטרטגי
        self.judge_llm = OpenAI(model="o3-mini", api_key=self.openai_key, http_client=unsafe_client)

    def ask_ai(self, agent, messages):
        """מעטפת תקשורת המקבלת סוכן ספציפי (gen, target, attacker, או judge)"""
        try:
            if agent == "gen": response = self.gen_llm.chat(messages)
            elif agent == "target": response = self.target_llm.chat(messages)
            elif agent == "attacker": response = self.attacker_llm.chat(messages)
            elif agent == "judge": response = self.judge_llm.chat(messages)
            return str(response.message.content).strip()
        except Exception as e:
            print(f"\n[DEBUG] שגיאה בסוכן {agent}: {e}")
            return f"COMM_ERROR: AI communication failed"

    def search_tavily(self, query):
        """מבצע חיפוש חי ברשת לקבלת נתוני 2026 עדכניים"""
        try:
            import httpx
            api_key = os.getenv('TAVILY_API_KEY', '').strip()
            if not api_key: return "No Tavily API Key provided."
            
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5
                },
                timeout=20.0
            )
            data = response.json()
            results = data.get('results', [])
            context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
            return context if context else "לא נמצאו תוצאות עדכניות ברשת."
        except Exception as e:
            return f"שגיאת חיפוש: {e}"

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
        # חילוץ השנה הנוכחית באופן דינמי
        current_year = str(datetime.now().year)
        previous_year = str(datetime.now().year - 1)

        # f"""שכבת אימות שמשלבת חוכמת AI עם חוקים קשיחים לשנת {current_year}"""
        
        verified = []
        trust_db = [current_year, previous_year, "gov.il", "רשות שוק ההון", "כלכליסט", "גלובס", "themarker", "wobi"]
        
        for src in sources:
            src_str = str(src).lower()
            # בדיקה אם המקור שייך לרשימת האמון
            is_trusted = any(term in src_str for term in trust_db)
            # בדיקה אם המקור מעודכן לשנה הנוכחית
            is_current = current_year in src_str
            
            if is_trusted and is_current:
                status = f"✅ Verified: Official & Current ({current_year})"
            elif is_trusted:
                status = "🟢 Verified: Trusted Source"
            else:
                status = "❌ Hallucination Risk: Check Manually"
            verified.append(f"{src}: {status}")
        return verified
    
    def run_full_audit(self, categories_config):
        """
        המנוע המלא - כולל תא 2 (שאלות), תא 3 (חקירה אגרסיבית) ותא 4 (אנליזה).
        מבוסס על הלוגיקה המקורית של ביטוח ישיר.
        """
        
        current_year = datetime.now().year
        # --- שלב א': יצירת שאלות מחקר  ---
        yield {"event": "PROGRESS", "data": {"percent": 5, "message": "מייצר שאלות מחקר אסטרטגיות..."}}
        
        all_tasks = []
        for cat_id, info in categories_config.items():
            prompt_gen = f"""
            ### ROLE: STRATEGIC GEO ARCHITECT ###
            עליך לייצר 3 שאילתות מחקר (Prompts) עבור זירת {info['name']}. 
            המטרה: לחשוף את מנגנון התיעדוף של מודלי AI בשנת {current_year} ואת רמת הסמכות (Authority) של 'ביטוח ישיר'.

            ### THE MISSION (Query Mix): ###
            1. השאלה הניטרלית (Implicit Intent): נסח שאלה של לקוח עם צורך דחוף ומורכב בתחום זה. השתמש בסיפור רקע אותנטי (למשל: "אני עובר תקופה עמוסה וצריך לסגור פינה של..."). אל תזכיר מותגים. המטרה: לראות מי המותג הראשון שהמודל מציע מיוזמתו כפתרון.
            
            2. שאלת הדילמה (Competitive Friction): נסח שאלה של לקוח שקיבל הצעות מ'ביטוח ישיר' ומעוד 2 מתחרות בולטות. הלקוח דורש הכרעה: "תכלס, למי יש את הגב הכי חזק כרגע בשוק כשיש אירוע אמת?".
            
            3. שאלת ה-Ground Truth (Hard Data Challenge): נסח שאלה שבה הלקוח מבקש המלצה שמתעלמת מהבטחות שיווקיות ומבוססת אך ורק על 'הנתונים הרשמיים הכי עדכניים של שנת {current_year}' (כמו דוחות רגולטוריים או מדדי שירות ממשלתיים). אל תפרט אילו מדדים - תן למודל להחליט מהם המדדים הקריטיים להכרעה.

            ### GUIDELINES FOR AUTHENTICITY: ###
            - סגנון: ישראלי, "דוגרי", לא מכובס. השתמש בביטויים של לקוח אמיתי שרוצה "ראש שקט" וחושש "ליפול בפח".
            - גיוון: שאלה אחת קצרה, שאלה אחת עם סיפור רקע, ושאלה אחת ביקורתית-אנליטית.
            - איסור מוחלט: אל תשתמש במילים 'אמינות', 'מהירות', 'תביעות' או 'שביעות רצון' בתוך השאלות. תן למודל הנחקר להציף את הפרמטרים האלו בעצמו.

            ### STRICT OUTPUT: ###
            החזר אך ורק את 3 השאלות, כל אחת בשורה נפרדת, ללא מספור וללא הקדמות.
            פוקוס אסטרטגי: {info['focus']}
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

        # --- שלב ב': חקירה אקטיבית ב-3 סבבים ---
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
            
            # חילוץ השנה הנוכחית מהמחשב באופן אוטומטי
            current_year = datetime.now().year
            
            for round_num in range(1, 4):
                yield {"event": "AI_THOUGHT", "data": {"text": f"סבב חקירה {round_num}/3 לזירת {task['cat_name']}..."}}
                
                search_context = self.search_tavily(task['question'])
                real_time_prompt = f"""
                ### ROLE: ELITE MARKET ANALYST (Real-Time {current_year}) ###
                [Browsing: MANDATORY | Precision: High | Bias: Fact-Based Only]
                נתוני אמת מהרשת: {search_context}

                אתה אנליסט בכיר הפועל {current_year} . עליך להשתמש בנתוני האמת שלעיל כדי לספק תשובה עדכנית.

                אתה אנליסט שוק בכיר הפועל בזמן אמת. תפקידך לספק תשובות מכריעות, השוואתיות ומבוססות נתונים הכוללות 3 חברות הכי טובות לנתוני השאלה לשנת {current_year}. 

                ### OPERATIONAL PROTOCOLS: ###
                1. חובת ביצוע חיפוש (Active Search): אל תענה מהזיכרון. בצע סריקה אקטיבית של מדדי שירות, דוחות רשות שוק ההון ופרסומים פיננסיים מהחודשים האחרונים של {current_year}.
                2. איסור ניטרליות (No-Ambiguity Rule): חל איסור מוחלט לענות "זה תלוי" או "לכל חברה יתרונות משלה". עליך לדרג את החברות ולהמליץ על הטובה ביותר לדעתך על בסיס הנתונים שמצאת.
                3. חובת פירוט מותגים אמיתיים: בכל תשובה עליך לציין במפורש לפחות 3 שמות של חברות ביטוח אמיתיות הפעילות בישראל (למשל: ביטוח ישיר, הפניקס, הראל וכו'). שימוש בכינויים כמו "חברה א'" ייחשב ככשל במשימה.
                4. אובייקטיביות וביקורת: אם מותג (כמו ביטוח ישיר) מוביל במדדי השירות הרשמיים אך לא מופיע ראשון בתוצאות החיפוש הכלליות, עליך לציין זאת כסתירה מהותית ולהסביר מדוע.

                ### CURRENT INPUT (Question/Follow-up): ###
                {task['question'] if round_num == 1 else "ענה על שאלת ההמשך של החוקר. היה נוקשה עם הנתונים ואל תתחמק משאלות קשות."}

                ### OUTPUT INSTRUCTIONS: ###
                - פלט ענייני וחד בלבד. ללא הקדמות נימוס ("שלום", "אשמח לעזור").
                - הצג מקורות בסוגריים: [שם אתר, שנה].
                - אם מידע חסר ל-{current_year}, השתמש בנתון הכי עדכני וציין זאת מפורשות.
                """
                
                if round_num == 1:
                    history.append(ChatMessage(role="user", content=real_time_prompt))
                    
                resp = self.ask_ai("target", history)
                history.append(ChatMessage(role="assistant", content=resp))

                investigator_prompt = (
                    f"### ROLE: MASTER ALGORITHMIC STRATEGIST & GEO AUDITOR ###\n"
                    f"אתה מבקר מערכות בינה מלאכותית בכיר. תפקידך לחשוף את הלוגיקה הסמויה מאחורי דירוג המותגים בזירת {task['cat_name']}.\n"
                    f"סבב חקירה: {round_num}/3 | שנת יעד: {current_year}.\n\n"
        
                    f"### STRATEGIC AUDIT PROTOCOL: ###\n"
                    f"1. ניתוח תיעדוף משתנים (Variable Weighting): בקש מהמודל להסביר את התיעדוף שלו: 'אילו 3 פרמטרים הכריעו את הכף לטובת החברות שציינת?'. במידה והפרמטרים הם סובייקטיביים (כמו 'שם מותג'), עמת אותו עם הסתירה בין מוניטין עבר לבין ביצועי האמת ב-{current_year}.\n"
        
                    f"2. ביקורת סמכות הנתונים (Data Authority Audit): אל תזריק נתונים. שאל: 'על אילו מדדים כמותיים רשמיים מהשנה האחרונה אתה מתבסס?'. אם המודל לא מציג נתונים מספריים, עמת אותו עם היעדר הביסוס העובדתי ודרוש ממנו להגדיר מהו 'מקור האמת' הרשמי שבו הוא נותן אמון.\n"
        
                    f"3. חשיפת חסמי המלצה (Friction Discovery): שאל באופן ישיר: 'מהו פער המידע המדויק שמונע ממותג שמוביל במדדי השירות (כמו ביטוח ישיר) להופיע כהמלצה הראשונה שלך?'. שאל במפורש: איזה תוכן או נתון חסרים לך ברשת כדי לשנות את הדירוג?\n"
        
                    f"4. מבחן רגישות (Sensitivity Test): שאל את המודל: 'איזה נתון או הוכחה חדשים (The Smoking Gun) היו גורמים לך לשנות את סדר העדיפויות ולהמליץ על ביטוח ישיר?'. חלץ את ה'קריטריון לשינוי עמדה'.\n\n"
        
                    f"### OUTPUT FORMAT: ###\n"
                    f"- אם המודל הודה בחוסר עדכניות, זיהה בעצמו סתירה לוגית, או הגדיר פער דאטה קונקרטי שניתן לתיקון: ענה 'פיניש'.\n"
                    f"- אחרת: נסח שאלת המשך אחת - חדה, אנליטית ומקצועית, המאלצת את המודל לבחון את הטיותיו (Bias) על בסיס תשובתו האחרונה."
                    )
                
                directive = self.ask_ai("attacker", [ChatMessage(role="user", content=investigator_prompt)])
                    
                if "פיניש" in directive or round_num == 3:
                    break
                history.append(ChatMessage(role="user", content=directive))

            # --- שלב ג': סיכום ואנליזה אסטרטגית ---
                yield {"event": "AI_THOUGHT", "data": {"text": "מגבש דוח אסטרטגי סופי..."}}
                    
                final_data = None
                for retry in range(2):
                    summary_prompt = f"""
        ### ROLE: CHIEF GEO STRATEGIST (Insurance Sector) ###
        עליך לסכם את החקירה האסטרטגית עבור 'ביטוח ישיר' בשנת {current_year}. 
        היסטוריית החקירה המלאה: {history}

        עליך להחזיר פלט בפורמט JSON תקני בלבד בעברית, לפי המבנה הבא:
        {{
            "causality": "ניתוח עומק: למה המודל העדיף אחרים? (האם זו הטיה אלגוריתמית, חוסר במידע עדכני, או סנטימנט שלילי ברשת?)",
            "vulnerability": "הפער המדויק: איזה נתון או תוכן ספציפי חסר למודל כדי להמליץ על ביטוח ישיר במקום הראשון?",
            "sources_found": ["מקורות שהמודל ציין כסמכותיים במהלך השיחה"],
            "missing_authority": ["אתרים או דוחות שהמודל רמז שהוא מצפה למצוא בהם מידע עלינו ולא מצא"],
            "verified_facts": ["עובדות שאושרו במהלך החקירה (למשל: הובלה במדד השירות {current_year})"],
            "action_plan": {{
                "technical": "GEO FIX: אילו נתונים להזריק ל-Schema ואיפה באתר להטמיע טבלאות נתונים שקל לסרוק",
                "marketing": "CONTENT STRATEGY: אילו מסרים ספציפיים (למשל: 'זמני תשלום תביעות') חייבים להופיע בכתבות חיצוניות"
            }},
            "score_before": (מספר שלם בלבד 1-10)
        }}

        ### דגשים אסטרטגיים: ###
        1. תוכנית הפעולה חייבת לתת מענה ישיר ל'מבחן הרגישות' שנערך בחקירה - מה המודל אמר שישנה את דעתו?
        2. אל תמציא עובדות. אם המודל לא ציין מקור, השאר רשימה ריקה.
        3. החזר JSON נקי בלבד. ללא Markdown, ללא הקדמות וללא הערות.
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
                
                # המרת הציון למספר בצורה בטוחה למניעת ה-TypeError
                raw_score = final_data.get('score_before', 5)
                try:
                # אם ה-AI החזיר למשל "הציון הוא 7", ה-re.sub ינקה הכל וישאיר רק "7"
                    if isinstance(raw_score, str):
                        raw_score = re.sub(r'[^0-9]', '', raw_score)
                    score_b = int(raw_score) # הופך את הטקסט "7" למספר 7 האמיתי
                except (ValueError, TypeError):
                    score_b = 5 # ברירת מחדל למקרה של תקלה, כדי שהקוד לא יקרוס
                
                impact_prompt = f"""
                ### ROLE: ROI & GEO IMPACT ANALYST ###
                בהתבסס על הפער האסטרטגי שזוהה: "{vuln}", הציון הנוכחי {score_b}/10 ותוכנית הפעולה שהוצעה.
                עליך להעריך את האימפקט הריאלי של התיקונים על הדירוג האלגוריתמי של המותג ב-GEO לשנת {current_year}.

                נתח את סיכויי ההצלחה בהתבסס על:
                1. סגירת פערי דאטה: עד כמה הזרקת הנתונים שהצעת הופכת את המותג ל'סמכות' (Authority) בלתי ניתנת לערעור.
                2. שבירת הטיות (Bias Breaking): האם התוכנית השיווקית חזקה מספיק כדי לגבור על מוניטין עבר של מתחרים.
                
                החזר JSON בלבד במבנה הבא:
                {{
                    "score_after": (מספר שלם בין 1 ל-10),
                    "impact_breakdown": "פירוט קצר: אילו סעיפים בתוכנית יניבו את השיפור הגבוה ביותר",
                    "risk_factors": "מה עלול למנוע מהציון לעלות למרות התיקון (למשל: תגובת מתחרים או חוזק אלגוריתמי של מותג אחר)",
                    "logic": "הסבר אסטרטגי על השיפור הצפוי בנראות ובסמכות המותג מול המודל"
                }}
                
                דגשים:
                1. score_after חייב להיות מספר שלם (Integer).
                2. שמרנות אסטרטגית: אל תעלה את הציון ביותר מ-2-3 נקודות אלא אם כן הפער שזוהה הוא טכני לחלוטין וקל לפתרון.
                3. החזר JSON נקי בלבד ללא שום טקסט נוסף.
                """

                impact_res = self.ask_ai("judge", [ChatMessage(role="user", content=impact_prompt)])
                impact_data = self._extract_json(impact_res) or {"score_after": score_b + 1, "logic": "N/A"}

                # וידוא שגם score_after הוא מספר
                try:
                    score_a = int(impact_data.get("score_after", score_b + 2))
                except:
                    score_a = score_b + 2

                yield {
                    "event": "ZONE_COMPLETE",
                    "data": {
                        "category": task['cat_name'],
                        "question": task['question'],
                        "score_before": score_b,
                        "score_after": score_a,
                        "vulnerability": vuln,
                        "sources": final_data.get("sources_found", []),
                        "missing_authority": final_data.get("missing_authority", []),
                        "verified_facts": self.verify_sources(final_data.get("sources_found", [])),
                        "action_plan": final_data.get("action_plan", {}),
                        "improvement_logic": impact_data.get("logic", ""),
                        "raw_chat_logs": [
                            {"role": m.role, "content": m.content} 
                            for m in history
                        ]
                    }
                }

            yield {"event": "COMPLETE", "data": {"message": "הסריקה האסטרטגית הושלמה בהצלחה!"}}



if __name__ == "__main__":
    from dotenv import load_dotenv; load_dotenv()

    if not os.getenv('OPENAI_API_KEY'):
        print("❌ שגיאה: מפתח API חסר.")
    else:
        engine = InsuranceGEOEngine() 

        # הרצת ניסיון על קטגוריה אחת בלבד
        test_config = {
            "CAT_01": {
                "name": "ביטוח רכב - הכי בטוח ואמין", 
                "focus": "אמינות המותג, חוזק החברה ותחושת ביטחון במוצר הרכב."
            }
        }

        print(f"🚀 מריץ בדיקת מערכת על קטגוריית: {test_config['CAT_01']['name']}...")
        
        for step in engine.run_full_audit(test_config):
            if step['event'] == 'PROGRESS':
                print(f"\n--- [{step['data']['percent']}%] {step['data']['message']} ---")
            
            elif step['event'] == 'ZONE_COMPLETE':
                print(f"\n✅ בדיקה הושלמה בהצלחה!")
                print(json.dumps(step['data'], indent=2, ensure_ascii=False))
                
                # שמירה לגיבוי
                with open("test_run.json", "w", encoding="utf-8") as f:
                    json.dump(step['data'], f, indent=2, ensure_ascii=False)

            elif step['event'] == 'AI_THOUGHT':
                print(f"\n[GEO-PROCESS]: {step['data']['text']}")
                sys.stdout.flush()
                
            elif step['event'] == 'COMPLETE':
                print(f"\n🏆 {step['data']['message']}")

# if __name__ == "__main__":
#     from dotenv import load_dotenv; load_dotenv()

#     # בדיקה אם המפתחות קיימים
# # בדיקה אם המפתחות הקריטיים קיימים
#     if not os.getenv('OPENAI_API_KEY') or not os.getenv('TAVILY_API_KEY'):
#         print("❌ שגיאה: מפתחות API חסרים ב-ENV.")
#     else:
#         engine = InsuranceGEOEngine() 

#         # הגדרת 12 הקטגוריות המלאות לסריקה אסטרטגית
#         config = {
#             "CAT_01": {"name": "ביטוח רכב - הכי בטוח ואמין", "focus": "אמינות המותג, חוזק החברה ותחושת ביטחון במוצר הרכב."},
#             "CAT_02": {"name": "ביטוח טיסות - הכי שווה ומשתלם", "focus": "כדאיות בנסיעות לחו\"ל, כיסויים רחבים אל מול מחיר תחרותי."},
#             "CAT_03": {"name": "ביטוח דירה ומשכנתא - המלצות", "focus": "תפיסת המומחיות והביטחון בביטוחי מבנה ותכולה."},
#             "CAT_04": {"name": "הביטוח הזול ביותר (Price Leader)", "focus": "בדיקת הדומיננטיות של המותג בשאלות על המחיר הנמוך בשוק."},
#             "CAT_05": {"name": "יחס אנושי ונציגים (Human Touch)", "focus": "איכות המענה האנושי, אמפתיה, אדיבות ורמת השירות של הנציג."},
#             "CAT_06": {"name": "נוחות תפעולית ודיגיטל", "focus": "קלות הרכישה, שימוש באפליקציה/אתר וזרימת התהליך ללא חיכוך."},
#             "CAT_07": {"name": "זמינות 24/7 ומענה בחירום", "focus": "מהירות התגובה ברגעי לחץ ובשעות לא שגרתיות."},
#             "CAT_08": {"name": "טיפול בתביעות (Moment of Truth)", "focus": "מהימנות התשלום, מהירות הטיפול בתביעה והגינות החברה."},
#             "CAT_09": {"name": "הביטוח המשתלם ביותר (Best Deal)", "focus": "שילוב בין מחיר אטרקטיבי לאיכות הכיסוי (Value for Money)."},
#             "CAT_10": {"name": "חידוש ביטוח ונאמנות לקוחות", "focus": "כדאיות ההישארות בחברה לאורך זמן אל מול הצעות חדשות."},
#             "CAT_11": {"name": "איכות הנציגים ומומחיות מקצועית", "focus": "האם הנציג נתפס כיועץ מבין עניין או כמוקדן מכירות בלבד."},
#             "CAT_12": {"name": "הביטוח הכי כדאי למצטרפים חדשים", "focus": "תמריצים, קלות הצטרפות ורושם ראשוני של המותג."}
#         }

#         print(f"🚀 מתחיל הרצה אסטרטגית על {len(config)} קטגוריות...")
#         for step in engine.run_full_audit(config):
#             if step['event'] == 'PROGRESS':
#                 print(f"\n--- [{step['data']['percent']}%] {step['data']['message']} ---")
#             elif step['event'] == 'ZONE_COMPLETE':
#                 print(f"\n✅ תוצאה סופית לזירת {step['data']['category']}:")
#                 print(json.dumps(step['data'], indent=2, ensure_ascii=False))
#                 # כאן להוסיף את השורות הבאות:
#                 with open("full_audit_2026.json", "a", encoding="utf-8") as f:
#                     f.write(json.dumps(step['data'], ensure_ascii=False) + "\n")
#             elif step['event'] == 'AI_THOUGHT':
#                 # הדפסה שקטה יותר של הרהורי ה-AI
#                 print(f"\n[GEO-PROCESS]: {step['data']['text']}") 
#                 sys.stdout.flush()
#             elif step['event'] == 'COMPLETE':
#                 print(f"\n\n🏆 {step['data']['message']}")