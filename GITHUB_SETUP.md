# 🚀 OpportunityHub - GitHub Automation Setup Guide

## ✅ What's Automated

Your OpportunityHub project now has full GitHub automation:

1. **Hourly Job Scraping** - Automatically scrapes LinkedIn every hour
2. **README Updates** - Auto-updates README.md with latest April 2026 opportunities  
3. **CSV Generation** - Creates/updates `april_2026_opportunities.csv`
4. **Auto-Commit & Push** - All changes are automatically committed and pushed to GitHub

## 🔧 Setup Instructions

### Step 1: Push to GitHub
```bash
cd "c:\Users\Isha Singh\OneDrive\Desktop\OpportunityHub"
git init
git add .
git commit -m "Initial commit: OpportunityHub with GitHub Actions"
git remote add origin https://github.com/YOUR_USERNAME/OpportunityHub.git
git branch -M main
git push -u origin main
```

### Step 2: GitHub Actions Will Automatically:
- ✅ Run every hour (Configurable via `.github/workflows/scrape-jobs.yml`)
- ✅ Scrape LinkedIn for jobs
- ✅ Update README.md
- ✅ Update CSV file
- ✅ Commit and push changes

### Step 3: Monitor Runs
Go to your GitHub repository → **Actions** tab to see workflow runs

## 📊 Files Structure

```
OpportunityHub/
├── main.py                          # Main scraper script
├── README.md                        # Auto-updated job table
├── april_2026_opportunities.csv     # Auto-generated CSV
├── requirements.txt                 # Dependencies
├── .github/
│   └── workflows/
│       └── scrape-jobs.yml         # GitHub Actions workflow
└── .gitignore                      # Git ignore rules
```

## ⏰ Customizing Schedule

Edit `.github/workflows/scrape-jobs.yml` to change frequency:

```yaml
on:
  schedule:
    # Current: Every hour
    - cron: '0 * * * *'
    # To run every 30 minutes, use:
    # - cron: '*/30 * * * *'
    # To run every day at 9 AM UTC:
    # - cron: '0 9 * * *'
```

## 🔑 Required Permissions

GitHub Actions uses `secrets.GITHUB_TOKEN` automatically (no additional setup needed)

## 📝 Notes

- First run may take 5-10 minutes due to LinkedIn rate limiting
- Jobs are filtered for April 2026 only
- CSV file contains 57 opportunities
- README displays live job opportunities with apply links

## ✨ Features

- 🎯 Auto-updates every hour
- 📊 CSV export for Excel/Analysis
- 🔗 Direct LinkedIn apply links
- 📅 Date filtering (April 2026)
- 🚀 4 target roles covered:
  - Full Stack Developer (MERN)
  - Software Engineer
  - MERN Stack Developer
  - Backend Developer

---

**Enjoy automated job hunting!** 🎉
