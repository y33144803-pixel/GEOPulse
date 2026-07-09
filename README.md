# 🛡️ GEO Strategy Engine 2026

A strategic analysis engine that examines how AI models (ChatGPT and similar) "think" about a given insurance brand across different categories (car insurance, travel insurance, home insurance, customer service, etc.), and generates a strategic action plan to improve the brand's visibility and authority in AI engines (GEO - Generative Engine Optimization).

The tool runs 4 different "AI agents" in sequence for each category:
1. **Generator** – produces 3 authentic research questions that a real customer would ask.
2. **Target** – simulates an end user and checks what ChatGPT (GPT-4o) actually answers.
3. **Attacker** – aggressively probes the answer to expose gaps and weaknesses.
4. **Judge** – analyzes the entire conversation and produces a score, gaps, an action plan, and an impact (ROI) assessment.

Results are displayed in an interactive **Streamlit** interface with a real-time investigation log.

---

## 📋 Prerequisites

- Python 3.10 or higher
- An OpenAI API key (required) — with access to the `gpt-4o-mini`, `gpt-4o`, and `o3-mini` models
- A Tavily API key (optional — for live web search of up-to-date data)

---

## ⚙️ Installation

1. **Clone/download the project** to a local folder, making sure `app.py` and `engine.py` are **in the same folder**.

2. **Install required libraries:**
   ```bash
   pip install streamlit python-dotenv httpx llama-index-llms-openai llama-index-llms-cohere
   ```

3. **Create a `.env` file** in the same folder, with your keys:
   ```
   OPENAI_API_KEY="sk-..."
   TAVILY_API_KEY="tvly-..."
   ```
   > `TAVILY_API_KEY` is not required. Without it, the live web search step is simply skipped and the engine continues to run.

---

## 🚀 Running the App

### Via the graphical interface (recommended)

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

In the interface you can:
- Select **one or several categories** at once (from 12 predefined categories)
- Set a free-text **strategic focus**
- Click **"Run Strategic Scan 🚀"** and follow progress in real time
- Check **"Show full conversation transcripts"** if you want to see the full internal dialogue between the agents (debug mode)

The run button is automatically disabled if `OPENAI_API_KEY` is missing, to prevent failed runs.

### Via the command line (quick system check)

`engine.py` also includes a standalone run block for a quick test on a single category, without the UI:

```bash
python engine.py
```

Output is printed to the terminal and also saved to a `test_run.json` file.

> At the bottom of `engine.py` there's a commented-out block (`# if __name__ ...`) that runs **all 12 categories** in sequence and saves all results to a `full_audit_2026.json` file. You can "unlock" it (remove the `#`) if you want a full automatic scan from the terminal — but note this is a long, API-call-heavy run.

---

## 📊 What You Get for Each Category

For every selected category, the engine produces:

| Field | Description |
|---|---|
| **Question tested** | One of the 3 automatically generated questions that was tested against ChatGPT |
| **Current / predicted score** | A 1–10 score of the brand's visibility/authority before and after applying the fixes |
| **Key gap (Vulnerability)** | The main strategic weakness identified |
| **Action plan** | Technical (GEO) recommendations and content/marketing recommendations |
| **Verified sources & facts** | List of sources with a verification status (trusted / current / hallucination risk) |
| **Authority gaps** | Reports/data the AI "expected" to find but didn't |
| **Improvement logic** | Strategic explanation of why the score is expected to rise |
| **Full conversation transcript** | (Optional, debug mode) the entire raw conversation between the agents |

---

## 🗂️ Project Structure

```
.
├── app.py          # Streamlit interface
├── engine.py       # Analysis engine (4 AI agents + scoring & verification logic)
├── .env            # API keys (do not share / commit to Git!)
└── README.md
```

---

## ⚠️ Important Notes

- **API costs**: each category runs 3 questions × up to 3 investigation rounds each, meaning dozens of calls to OpenAI (including the relatively expensive `o3-mini` and `gpt-4o`). Start with a single category to confirm everything works before running several categories at once.
- **SSL verification**: the engine currently uses `httpx.Client(verify=False)`, meaning SSL certificate verification is disabled for API calls. This is useful for working around local network/proxy issues, but it's recommended to remove this setting before running in a production environment.
- **Do not commit your `.env` file** to a public Git repository — it contains your API keys.
- If `TAVILY_API_KEY` is not set, the engine will keep working but without live web data search.

---

## 🛠️ Troubleshooting

| Issue | Possible cause |
|---|---|
| "Run Strategic Scan" button is disabled | `OPENAI_API_KEY` is missing from `.env` |
| `COMM_ERROR` message in the log | Communication issue with OpenAI — check your API key, model access permissions, and internet connection |
| Scores are always "5" and gap is "manual review needed" | The AI returned malformed JSON; the engine falls back to a default after 3 correction attempts |
| `ModuleNotFoundError` | Make sure you've installed all packages listed in the Installation section above |
