import json
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Job Scout & Pitch Dashboard", layout="wide")

# Clean Slate & Cobalt professional dashboard styling
st.markdown(
    """
    <style>
    .stApp { background-color: #f8fafc; color: #0f172a; }
    .hero-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 22px 26px;
        border-radius: 12px;
        margin-bottom: 18px;
    }
    .hero-box h1 { margin: 0 0 6px 0; font-size: 1.75rem; color: #ffffff; }
    .hero-box p { margin: 0; color: #cbd5e1; font-size: 0.98rem; }
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }
    .badge-high {
        background: #dcfce7; color: #166534; padding: 3px 9px;
        border-radius: 999px; font-size: 0.8rem; font-weight: 700;
    }
    .badge-mid {
        background: #fef3c7; color: #92400e; padding: 3px 9px;
        border-radius: 999px; font-size: 0.8rem; font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-box">
        <h1>Job Scout &amp; Custom Pitch Dashboard</h1>
        <p>Filter out unpaid or senior job noise with Python, score fresher-friendly matches, and generate tailored Wellfound &amp; LinkedIn outreach notes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar controls
st.sidebar.header("Filter Settings")
target_track = st.sidebar.selectbox(
    "Target Track",
    ["Manual QA / App Testing", "Founder's Office / Growth", "AI Operations"],
)
remote_only = st.sidebar.checkbox("Remote / Kolkata Only", value=True)
min_stipend = st.sidebar.number_input("Minimum Monthly Pay (INR)", min_value=0, value=10000, step=2500)
blocked_words_raw = st.sidebar.text_input(
    "Auto-Exclude Keywords (comma-separated)",
    value="unpaid, 2+ years, 3+ years, 5+ years, senior, leetcode",
)
default_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, "secrets") else ""
api_key = st.sidebar.text_input("OpenAI API Key (optional)", value=default_key, type="password")
st.sidebar.caption("Runs in Demo Mode automatically when no API key is entered.")

# Helper: Score and draft custom pitch
def score_and_pitch(row: pd.Series, track: str, key: str) -> dict:
    title = str(row["title"])
    company = str(row["company"])
    desc = str(row["description"])

    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            prompt = (
                "Return ONLY valid JSON with keys: score (integer 1-10), "
                "wellfound_note (2 concise sentences tailored to the job for a final-year B.Tech CSE AIML student), "
                "linkedin_dm (1 short 25-word DM). "
                f"Track: {track}. Role: {title} at {company}. Description: {desc}"
            )
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            raw = res.choices[0].message.content.strip().strip("`json").strip("`")
            return json.loads(raw)
        except Exception:
            pass

    text = f"{title} {desc}".lower()
    score = 6
    if any(k in text for k in ["qa", "testing", "test case", "bug", "manual"]) and "QA" in track:
        score += 3
    elif any(k in text for k in ["founder", "growth", "operations", "ai"]) and "Founder" in track:
        score += 3
    elif any(k in text for k in ["ai", "automation", "python", "streamlit"]) and "AI" in track:
        score += 3
    if any(k in text for k in ["fresher", "intern", "0-1", "final year"]):
        score += 1
    score = min(score, 10)

    wellfound_note = (
        f"Hi {company} team — I'm a final-year B.Tech CSE (AI & ML) student with hands-on experience "
        f"testing AI pipelines (VOICESCRIBE) and building live Python/Streamlit tools. "
        f"I'd love to support your {title} role and am happy to complete a quick 2-hour sample task."
    )
    linkedin_dm = (
        f"Hi! Just applied for {title} at {company}. Built and tested live Python/AI tools in college "
        f"and would love to contribute right away—open to a quick trial task?"
    )
    return {"score": score, "wellfound_note": wellfound_note, "linkedin_dm": linkedin_dm}

# Load CSV or built-in sample jobs
uploaded = st.file_uploader("Upload Jobs CSV (title, company, location, stipend_inr, description, apply_url)", type=["csv"])
df = pd.read_csv(uploaded) if uploaded else pd.read_csv("sample_jobs.csv")

# Python Rule Engine: Filter out noise before scoring
blocked_words = [w.strip().lower() for w in blocked_words_raw.split(",") if w.strip()]

def is_valid_job(row: pd.Series) -> bool:
    combined = f"{row['title']} {row['description']}".lower()
    if any(re.search(rf"\b{re.escape(w)}\b", combined) or w in combined for w in blocked_words):
        return False
    if int(row.get("stipend_inr", 0)) < min_stipend:
        return False
    if remote_only:
        loc = str(row.get("location", "")).lower()
        if not any(k in loc for k in ["remote", "kolkata", "work from home"]):
            return False
    return True

filtered_df = df[df.apply(is_valid_job, axis=1)].copy()
blocked_count = len(df) - len(filtered_df)

if len(filtered_df) > 0:
    enriched = [score_and_pitch(r, target_track, api_key) for _, r in filtered_df.iterrows()]
    filtered_df["Match"] = [int(e.get("score", 7)) for e in enriched]
    filtered_df["Wellfound Note"] = [e.get("wellfound_note", "") for e in enriched]
    filtered_df["LinkedIn DM"] = [e.get("linkedin_dm", "") for e in enriched]
    filtered_df = filtered_df.sort_values(by="Match", ascending=False)

# KPI Row
k1, k2, k3 = st.columns(3)
k1.metric("Total Jobs Scanned", len(df))
k2.metric("Qualified Matches", len(filtered_df))
k3.metric("Filtered Out (Noise)", blocked_count)

if len(filtered_df) == 0:
    st.warning("No jobs matched your strict filters. Try lowering the minimum stipend or adjusting excluded keywords.")
else:
    for _, row in filtered_df.iterrows():
        badge_cls = "badge-high" if row["Match"] >= 8 else "badge-mid"
        st.markdown(
            f"""
            <div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:1.08rem;">{row['title']} &mdash; {row['company']}</strong>
                    <span class="{badge_cls}">Match {row['Match']}/10</span>
                </div>
                <div style="color:#475569; font-size:0.9rem; margin:4px 0 8px 0;">
                    {row['location']} &bull; ₹{int(row['stipend_inr']):,}/mo &bull;
                    <a href="{row['apply_url']}" target="_blank">Open Job Link</a>
                </div>
                <div style="font-size:0.92rem; color:#1e293b;">{row['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"View Custom Pitch for {row['company']}"):
            st.caption("Wellfound Application Note")
            st.code(row["Wellfound Note"], language=None)
            st.caption("LinkedIn Founder DM")
            st.code(row["LinkedIn DM"], language=None)

    st.download_button(
        "Download Shortlisted Jobs CSV",
        filtered_df.to_csv(index=False),
        "shortlisted_jobs.csv",
        "text/csv",
    )
