# TODO: Update OpportunityHub Scraper (April → July 2026)

## Steps:

- [x] Read and understand all files
- [x] 1. **main.py** — Add `f_TPR=r2592000` (last 30 days) filter to LinkedIn search URL in `build_linkedin_search_url()`
- [x] 2. **main.py** — Increase pages from 3 to 5 in `scrape_linkedin_jobs()` for better coverage
- [x] 3. **main.py** — Fix missing `utc_timestamp_str()` function (pre-existing bug fix)
- [x] 4. **main.py** — Remove hardcoded `pages=3` from main block (now uses default 5)
- [x] 5. ✅ **All done!** Next GitHub Actions run will scrape July 2026 jobs automatically
