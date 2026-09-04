# OpportunityHub: Jobs Scrapper
> Your personal job opportunity aggregator! 🚀

Runs daily at 7:00 AM IST and emails a combined digest with direct apply links.

<!--START_SECTION:stats-->
## 📅 September 4, 2026 — Live Opportunities (8 Jobs)
**Last Updated:** 2026-09-04 09:08 AM UTC | **Status:** Live ✅

### Job Categories:
- 🔴 **Full Stack Developer**: 8 jobs
<!--END_SECTION:stats-->

### Current Opportunities:
<!--START_SECTION:workfetch-->
ROLE        - Full Stack Developer<br>
COMPANY     - Graviton Research Capital<br>
TITLE       - Software Engineer (C++)<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://boards.greenhouse.io/gravitonresearchcapital/jobs/4004920002?gh_jid=4004920002)
ROLE        - Full Stack Developer<br>
COMPANY     - Graviton Research Capital<br>
TITLE       - Software Engineer<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://boards.greenhouse.io/gravitonresearchcapital/jobs/5099344002?gh_jid=5099344002)
ROLE        - Full Stack Developer<br>
COMPANY     - Graviton Research Capital<br>
TITLE       - Software Engineer- Python<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://boards.greenhouse.io/gravitonresearchcapital/jobs/8147013002?gh_jid=8147013002)
ROLE        - Full Stack Developer<br>
COMPANY     - Graviton Research Capital<br>
TITLE       - Software Engineer (2027 Graduate)<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://boards.greenhouse.io/gravitonresearchcapital/jobs/8764240002?gh_jid=8764240002)
ROLE        - Full Stack Developer<br>
COMPANY     - NK Securities Research<br>
TITLE       - Software Developer <br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://job-boards.eu.greenhouse.io/nksecuritiesresearch/jobs/4470703101)
ROLE        - Full Stack Developer<br>
COMPANY     - NK Securities Research<br>
TITLE       - Software Developer - Platform<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://job-boards.eu.greenhouse.io/nksecuritiesresearch/jobs/4519747101)
ROLE        - Full Stack Developer<br>
COMPANY     - NK Securities Research<br>
TITLE       - AI Engineer<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurugram, Haryana, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://job-boards.eu.greenhouse.io/nksecuritiesresearch/jobs/4811652101)
ROLE        - Full Stack Developer<br>
COMPANY     - Sauce Labs<br>
TITLE       - Full-stack Software Engineer (python/go)<br>
DATE POSTED - <br>
ADDED AT    - 2026-09-04 02:38 PM IST<br>
LOCATION    - Gurgaon, India<br>
MATCH SCORE - 100%<br>
APPLY LINK  - [Apply](https://job-boards.greenhouse.io/saucelabs/jobs/8125664)
<!--END_SECTION:workfetch-->

## Resume Profile

Place your resume in the `resume/` folder as a `.pdf`, `.docx`, `.txt`, or `.md` file. Create `profile.json` with:

```powershell
.\.venv\Scripts\python.exe main.py --resume "resume\your-resume.pdf"
```

The generated `profile.json` contains extracted contact details, links, skills, experience, education, projects, certifications, summary, and the complete extracted resume text.

Jobs are collected from the configured company boards on Greenhouse, Lever, and Ashby, plus public searches on LinkedIn, Naukri, and Internshala. Only the requested role families with a profile match score of at least 90% are saved.

Optional Gemini verification uses the free-tier `gemini-2.5-flash-lite` model. Set your key only in the terminal environment, never in source files:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

You can choose another available model with `$env:GEMINI_MODEL`. Without a key, the local profile matcher still runs. Listings must match a configured Delhi NCR location and duplicate application URLs are removed.

## Daily Gmail Digest

The scraper sends one combined HTML digest to `ishu010.com@gmail.com` after each completed run. It contains only newly discovered 90%+ Delhi NCR matches, with direct **Open & apply** links.

For a local run, create a Gmail App Password (Google Account -> Security -> 2-Step Verification -> App passwords), then set it in the current PowerShell session:

```powershell
$env:GMAIL_APP_PASSWORD = "your-16-character-app-password"
$env:GMAIL_SENDER = "ishu010.com@gmail.com"
$env:GMAIL_RECIPIENT = "ishu010.com@gmail.com"
python main.py
```

Never put the app password in `main.py`, `README.md`, or Git. The included GitHub Actions workflow runs every day at 7:00 AM IST (01:30 UTC). For that automatic cloud run, add `GEMINI_API_KEY` and `GMAIL_APP_PASSWORD` as repository secrets under GitHub -> Settings -> Secrets and variables -> Actions. `GMAIL_SENDER` and `GMAIL_RECIPIENT` are already configured for this account.
