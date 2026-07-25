import logging
from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd
import random
import time
import os
from datetime import datetime, timezone
import json
import re
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("opportunityhub")

# Target roles for scraping
TARGET_ROLES = [
    "full stack developer",
    "full stack engineer",
    "mern stack developer",
    "mern stack developer intern",
    "software engineer",
    "software developer",
    "nodejs developer",
    "backend developer",
]

# Target locations — only jobs from these cities will be captured
TARGET_LOCATIONS = [
    # ── Delhi NCR ──
    "new delhi",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "dwarka",
    "greater noida",
]

# ─────────────────────────── Time helpers ────────────────────────────

from datetime import timedelta

# Indian Standard Time = UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))


def _ist_now() -> datetime:
    """Returns current time in IST."""
    return datetime.now(IST)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ist_timestamp_str(dt: datetime | None = None) -> str:
    """Returns IST timestamp string like: 2026-04-23 09:56 PM IST"""
    dt = dt or _ist_now()
    if dt.tzinfo != IST:
        dt = dt.astimezone(IST)
    return dt.strftime("%Y-%m-%d %I:%M %p IST")


def utc_timestamp_str(dt: datetime | None = None) -> str:
    """Returns UTC timestamp string like: 2026-04-23 10:36 UTC"""
    dt = dt or _utc_now()
    if dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %I:%M %p UTC")


def get_target_date() -> str:
    """Returns today's date in IST (YYYY-MM-DD), overridable via TARGET_DATE env var."""
    env = os.getenv("TARGET_DATE")
    if env and len(env) == 10 and env[4] == "-" and env[7] == "-":
        return env
    return _ist_now().strftime("%Y-%m-%d")


def day_label_from_target_date(target_date: str) -> str:
    year, month, day = target_date.split("-")
    dt = datetime(int(year), int(month), int(day), tzinfo=IST)
    return dt.strftime("%B %#d, %Y") if os.name == "nt" else dt.strftime("%B %-d, %Y")


# ─────────────────────────── Filename helpers ────────────────────────

def output_hourly_csv_filename(target_date: str, now: datetime) -> str:
    """e.g. opportunities_2026_04_23_09_56_PM.csv (IST)"""
    ist = now.astimezone(IST)
    return f"opportunities_{target_date.replace('-', '_')}_{ist.strftime('%I_%M_%p')}.csv"


def output_hourly_txt_filename(target_date: str, now: datetime) -> str:
    """e.g. opportunities_2026_04_23_09_56_PM.txt (IST)"""
    ist = now.astimezone(IST)
    return f"opportunities_{target_date.replace('-', '_')}_{ist.strftime('%I_%M_%p')}.txt"


def role_to_slug(role: str) -> str:
    """Convert role name to folder/filename safe slug.
    e.g. 'Full Stack Developer' -> 'full_stack_developer'
    """
    return re.sub(r'[^a-z0-9]+', '_', role.lower()).strip('_')


def output_role_csv_path(role: str, target_date: str, now: datetime) -> str:
    """e.g. jobs/full_stack_developer/full_stack_developer_2026_04_23_09_56_PM.csv (IST)"""
    slug = role_to_slug(role)
    folder = os.path.join("jobs", slug)
    os.makedirs(folder, exist_ok=True)
    ist = now.astimezone(IST)
    filename = f"{slug}_{target_date.replace('-', '_')}_{ist.strftime('%I_%M_%p')}.csv"
    return os.path.join(folder, filename)


def output_role_txt_path(role: str, target_date: str, now: datetime) -> str:
    """e.g. jobs/full_stack_developer/full_stack_developer_2026_04_23_09_56_PM.txt (IST)"""
    slug = role_to_slug(role)
    folder = os.path.join("jobs", slug)
    os.makedirs(folder, exist_ok=True)
    ist = now.astimezone(IST)
    filename = f"{slug}_{target_date.replace('-', '_')}_{ist.strftime('%I_%M_%p')}.txt"
    return os.path.join(folder, filename)


# ─────────────────────── seen_jobs.json helpers ───────────────────────
# Format: { url_key: { "first_seen": "2026-04-23 14:00 UTC", "job": {...} } }

def extract_url_from_markdown_link(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"\((https?://[^)]+)\)", text)
    return m.group(1) if m else text


def _get_url_key(job: dict) -> str:
    link = str(job.get("Link", "") or "")
    url = extract_url_from_markdown_link(link).strip()
    if url:
        return url
    return f"{job.get('Company', '')}|{job.get('Title', '')}|{job.get('Location', '')}"


def load_seen_index(path: str = "seen_jobs.json") -> dict:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_seen_index(index: dict, path: str = "seen_jobs.json") -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        pass


def add_new_jobs_to_seen(
    jobs: list[dict],
    now: datetime,
    index_path: str = "seen_jobs.json"
) -> list[dict]:
    """
    Adds new (unseen) jobs to seen_jobs.json with full job data.
    Returns only the NEWLY added jobs from this run.
    """
    now_str = ist_timestamp_str(now)
    seen = load_seen_index(index_path)
    new_jobs = []

    for job in jobs:
        url_key = _get_url_key(job)
        if url_key not in seen:
            job["Added At"] = now_str
            seen[url_key] = {
                "first_seen": now_str,
                "job": dict(job)
            }
            new_jobs.append(job)
        else:
            entry = seen[url_key]
            # Migrate old format (string timestamp only)
            if isinstance(entry, str):
                job["Added At"] = entry
                seen[url_key] = {
                    "first_seen": entry,
                    "job": dict(job)
                }
            else:
                job["Added At"] = entry.get("first_seen", now_str)
                # Update job data in case fields changed, keep first_seen
                seen[url_key]["job"] = dict(job)

    save_seen_index(seen, index_path)
    return new_jobs


def get_todays_all_jobs(target_date: str, index_path: str = "seen_jobs.json") -> list[dict]:
    """
    Returns ALL unique jobs first seen on target_date from seen_jobs.json.
    This gives the cumulative list for the whole day.
    """
    seen = load_seen_index(index_path)
    todays_jobs = []

    for url_key, entry in seen.items():
        if isinstance(entry, dict):
            first_seen = entry.get("first_seen", "")
            if first_seen.startswith(target_date):
                job = entry.get("job", {})
                if job:
                    todays_jobs.append(job)
        # Old string format: we don't have job data, skip

    return todays_jobs


# ─────────────────────────── Chrome setup ────────────────────────────

def setup_chrome_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()

    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    options = [
        "--window-size=1200,1200",
        "--ignore-certificate-errors",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--lang=en-US",
    ]

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

    for option in options:
        chrome_options.add_argument(option)

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(45)
    return driver


def polite_sleep(min_s: float = 1.5, max_s: float = 4.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def click_load_more_if_present(driver: webdriver.Chrome) -> bool:
    selectors = [
        (By.CSS_SELECTOR, "button.infinite-scroller__show-more-button"),
        (By.CSS_SELECTOR, "button.show-more-less-html__button"),
        (By.XPATH, "//button[contains(., 'Show more') or contains(., 'See more jobs')]"),
    ]
    for by, value in selectors:
        try:
            btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((by, value)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            polite_sleep(0.4, 1.0)
            btn.click()
            return True
        except Exception:
            continue
    return False


# ─────────────────────────── Scraper ─────────────────────────────────

def build_linkedin_search_url(job_title: str, location: str) -> str:
    return (
        "https://www.linkedin.com/jobs/search/?"
        "f_E=1&origin=JOB_SEARCH_PAGE_JOB_FILTER&geoId=102713980&"
        "f_TPR=r2592000&"  # Last 30 days (30d = 2592000 seconds)
        f"keywords={job_title}&location={location}&refresh=true&sortBy=DD"
    )


def scrape_linkedin_jobs(job_title: str, location: str, pages: int = 5) -> list:
    jobs = []
    driver = None
    try:
        driver = setup_chrome_driver()
        search_url = build_linkedin_search_url(job_title, location)
        logger.info("Navigating to: %s", search_url)
        driver.get(search_url)
        polite_sleep(2.0, 4.5)

        for i in range(pages):
            logger.info("Scroll batch %s/%s for '%s'", i + 1, pages, job_title)
            for _ in range(4):
                driver.execute_script("window.scrollBy(0, Math.floor(document.body.scrollHeight/4));")
                polite_sleep(0.8, 1.7)
            clicked = click_load_more_if_present(driver)
            logger.info("Load-more clicked: %s", clicked)
            polite_sleep(2.5, 5.5)

        page = driver.page_source or ""
        lowered = page.lower()
        if "unusual activity" in lowered or ("verify" in lowered and "captcha" in lowered):
            logger.warning("LinkedIn likely blocked the scrape (captcha/unusual activity).")

        soup = BeautifulSoup(page, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )
        logger.info("Found %s raw listings for '%s'", len(job_listings), job_title)

        for job in job_listings:
            try:
                title_elem = job.find("h3", class_="base-search-card__title")
                company_elem = job.find("h4", class_="base-search-card__subtitle")
                location_elem = job.find("span", class_="job-search-card__location")
                link_elem = job.find("a", class_="base-card__full-link")
                date_elem = job.find("time")

                if not all([title_elem, company_elem, location_elem, link_elem, date_elem]):
                    continue

                job_title_text = title_elem.text.strip()
                job_company = company_elem.text.strip()
                job_location = location_elem.text.strip()
                apply_link = link_elem.get("href", "#")
                date_posted = date_elem.get("datetime", "N/A")

                is_relevant = any(
                    keyword in job_title_text.lower()
                    for keyword in [
                        "intern", "apprentice", "trainee", "graduate",
                        "fresher", "junior", "entry level", "entry-level"
                    ]
                )

                is_target_city = any(
                    loc in job_location.lower()
                    for loc in TARGET_LOCATIONS
                )

                if is_relevant and is_target_city:
                    jobs.append({
                        "Role": job_title.title(),
                        "Company": job_company,
                        "Title": job_title_text,
                        "Location": job_location,
                        "Link": f"[Apply]({apply_link})",
                        "Date Posted": date_posted,
                    })
            except Exception:
                continue

    except Exception as e:
        logger.exception("Error during scraping: %s", str(e))
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass

    return jobs


# ─────────────────────────── Save helpers ────────────────────────────

def save_to_csv(data: list, filename: str) -> None:
    """Save job list to a proper CSV file (comma-separated, Excel-friendly)."""
    if not data:
        logger.warning("No data to save to CSV: %s", filename)
        return
    try:
        df = pd.DataFrame(data)
        preferred = ["Role", "Company", "Title", "Location", "Link", "Date Posted", "Added At"]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        df = df[cols]
        df.to_csv(filename, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL)
        logger.info("Saved %s jobs → %s", len(data), filename)
    except Exception as e:
        logger.exception("Error saving CSV %s: %s", filename, str(e))


def save_to_txt(data: list, filename: str) -> None:
    """Save job list to human-readable block-format TXT."""
    if not data:
        logger.warning("No data to save to TXT: %s", filename)
        return
    try:
        data = sorted(data, key=lambda x: x.get("Date Posted", ""), reverse=True)
        blocks = []
        for job in data:
            blocks.append("\n".join([
                f"ROLE        - {job.get('Role', '')}",
                f"COMPANY     - {job.get('Company', '')}",
                f"TITLE       - {job.get('Title', '')}",
                f"DATE POSTED - {job.get('Date Posted', '')}",
                f"ADDED AT    - {job.get('Added At', '')}",
                f"LOCATION    - {job.get('Location', '')}",
                f"APPLY LINK  - {job.get('Link', '')}",
            ]))
        content = "\n\n".join(blocks) + "\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Saved %s jobs → %s", len(data), filename)
    except Exception as e:
        logger.exception("Error saving TXT %s: %s", filename, str(e))


def _render_job_blocks(rows: list[dict]) -> str:
    """Render jobs in fixed block format for README."""
    blocks = []
    for r in rows:
        blocks.append("\n".join([
            f"ROLE        - {r.get('Role', '')}",
            f"COMPANY     - {r.get('Company', '')}",
            f"TITLE       - {r.get('Title', '')}",
            f"DATE POSTED - {r.get('Date Posted', '')}",
            f"ADDED AT    - {r.get('Added At', '')}",
            f"LOCATION    - {r.get('Location', '')}",
            f"APPLY LINK  - {r.get('Link', '')}",
        ]))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def update_readme(all_today_jobs: list, target_date: str, now: datetime) -> None:
    """
    Update README.md with ALL cumulative jobs for today.
    Stats section shows totals; job listing section shows all jobs sorted newest first.
    """
    if not os.path.exists("README.md"):
        logger.warning("README.md not found. Skipping.")
        return

    try:
        with open("README.md", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Sort jobs: newest Date Posted first, then by Added At
        jobs_sorted = sorted(
            all_today_jobs,
            key=lambda x: (x.get("Date Posted", ""), x.get("Added At", "")),
            reverse=True
        )

        df = pd.DataFrame(jobs_sorted) if jobs_sorted else pd.DataFrame()

        day_label = day_label_from_target_date(target_date)
        current_time = utc_timestamp_str(now)
        total_jobs = len(jobs_sorted)

        # ── Stats section ──
        roles_emoji = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫"]
        stats_md = f"## 📅 {day_label} — Live Opportunities ({total_jobs} Jobs)\n"
        stats_md += f"**Last Updated:** {current_time} | **Status:** Live ✅\n\n"
        stats_md += "### Job Categories:\n"

        if not df.empty and "Role" in df.columns:
            role_counts = df["Role"].value_counts()
            for i, (role, count) in enumerate(role_counts.items()):
                emoji = roles_emoji[i % len(roles_emoji)]
                stats_md += f"- {emoji} **{role}**: {count} jobs\n"

        stats_start = content.find("<!--START_SECTION:stats-->")
        stats_end = content.find("<!--END_SECTION:stats-->")
        if stats_start != -1 and stats_end != -1:
            content = (
                content[:stats_start + len("<!--START_SECTION:stats-->\n")]
                + stats_md
                + content[stats_end:]
            )

        # ── Jobs listing section ──
        start = content.find("<!--START_SECTION:workfetch-->")
        end = content.find("<!--END_SECTION:workfetch-->")
        if start == -1 or end == -1:
            logger.warning("Workfetch markers not found in README.md")
            return

        job_blocks = _render_job_blocks(jobs_sorted) if jobs_sorted else "No jobs found yet today.\n"

        new_content = (
            content[:start]
            + f"<!--START_SECTION:workfetch-->\n{job_blocks}"
            + content[end:]
        )

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info("README.md updated with %s cumulative jobs for %s", total_jobs, target_date)

    except Exception as e:
        logger.exception("Error updating README: %s", str(e))


# ─────────────────────────── Main ────────────────────────────────────

if __name__ == "__main__":
    now = _ist_now()          # ← IST time used everywhere
    target_date = get_target_date()
    day_label = day_label_from_target_date(target_date)
    run_time_str = ist_timestamp_str(now)  # e.g. 2026-04-23 09:56 PM IST
    time_label = now.strftime("%I:%M %p")  # e.g. 09:56 PM

    print("=" * 70)
    print(f"  OPPORTUNITYHUB — {day_label} Job Scraper")
    print(f"  Run Time (UTC) : {run_time_str}")
    print(f"  Roles          : {len(TARGET_ROLES)} roles to scrape")
    print(f"  Output         : jobs/<role>/<role>_{target_date.replace('-','_')}_{now.strftime('%H_%M')}.csv")
    print("=" * 70)
    print("  This may take 10–20 minutes (LinkedIn rate limiting)...")
    print()

    all_scraped: list[dict] = []
    location = "India"
    role_results: dict[str, list[dict]] = {}  # role -> jobs found this run

    # ── Step 1: Scrape each role → save to its own folder immediately ──
    for idx, role in enumerate(TARGET_ROLES, 1):
        print(f"[{idx}/{len(TARGET_ROLES)}] Scraping: '{role}'")
        print("-" * 70)

        jobs = scrape_linkedin_jobs(role, location)

        if jobs:
            # Stamp Added At for this run
            for job in jobs:
                job["Added At"] = run_time_str

            # Sort newest first
            jobs_sorted = sorted(jobs, key=lambda x: x.get("Date Posted", ""), reverse=True)

            # Save role-specific CSV + TXT
            role_csv = output_role_csv_path(role, target_date, now)
            role_txt = output_role_txt_path(role, target_date, now)
            save_to_csv(jobs_sorted, role_csv)
            save_to_txt(jobs_sorted, role_txt)

            print(f"  ✓ {len(jobs)} jobs found")
            print(f"  📁 Saved → {role_csv}")

            role_results[role] = jobs_sorted
            all_scraped.extend(jobs)
        else:
            print(f"  ✗ No matching jobs found for '{role}'")
            role_results[role] = []

        if idx < len(TARGET_ROLES):
            wait = random.randint(8, 15)
            print(f"  ⏳ Waiting {wait}s...\n")
            time.sleep(wait)

    # ── Step 2: Dedup — add new jobs to seen_jobs.json ──
    print("\n" + "=" * 70)
    print(f"  Total scraped this run : {len(all_scraped)}")
    new_jobs = add_new_jobs_to_seen(all_scraped, now)
    print(f"  🆕 New unique jobs     : {len(new_jobs)}")

    # ── Step 3: Cumulative daily README update ──
    all_today_jobs = get_todays_all_jobs(target_date)
    print(f"  📊 Total jobs today    : {len(all_today_jobs)}")
    update_readme(all_today_jobs, target_date, now)

    # ── Step 4: Summary per role ──
    print("\n" + "=" * 70)
    print("  📋 Per-Role Summary:")
    print("-" * 70)
    for role, jobs in role_results.items():
        slug = role_to_slug(role)
        folder = f"jobs/{slug}/"
        print(f"  {'✓' if jobs else '✗'} {role.title():<35} {len(jobs):>3} jobs  →  {folder}")

    print("\n" + "=" * 70)
    print(f"  ✅ Done! {len(all_today_jobs)} total jobs for {day_label} in README.")
    print(f"  ⏰ Run completed at {run_time_str}")
    print("=" * 70)
