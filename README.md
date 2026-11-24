# Job Scout & Custom Pitch Dashboard

A Python + Streamlit dashboard that filters out unpaid, senior, and mismatched job listings, scores fresher-friendly roles, and drafts tailored Wellfound & LinkedIn outreach notes.

## Features
- **Rule-Based Noise Filter:** Automatically drops listings containing excluded keywords (`unpaid`, `2+ years`, `senior`, `leetcode`), low stipends, or mismatched locations.
- **Role-Based Match Scoring:** Scores filtered jobs (1–10) for Manual QA, Founder's Office, or AI Operations tracks.
- **Custom Pitch Generator:** Generates copy-ready Wellfound application notes and LinkedIn DMs (uses OpenAI `gpt-4o-mini` when an API key is provided, or built-in Demo Mode).

## Deploy Free from iPad / Browser
1. Unzip and upload `app.py`, `requirements.txt`, `sample_jobs.csv`, and `README.md` to a public GitHub repo.
2. Deploy `app.py` on [share.streamlit.io](https://share.streamlit.io).
