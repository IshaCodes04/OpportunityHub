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
    "full stack developer mern stack",
    "software engineer",
    "mern stack developer",
    "backend developer"
]

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp_str(dt: datetime | None = None) -> str:
    dt = dt or _utc_now()
    # Example: 2026-04-22 17:30 UTC
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def extract_url_from_markdown_link(text: str) -> str:
    """
    Extract URL from markdown like: [Apply](https://example.com)
    Returns original text if no URL is found.
    """
    if not text:
        return ""
    m = re.search(r"\((https?://[^)]+)\)", text)
    return m.group(1) if m else text


def load_seen_index(path: str = "seen_jobs.json") -> dict:
    """
    Persisted mapping: url -> first_seen_timestamp (UTC string).
    Committed in repo so hourly runs keep history.
    """
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


def add_added_at(jobs: list[dict], now: datetime | None = None, index_path: str = "seen_jobs.json") -> list[dict]:
    """
    Adds 'Added At' field to each job (first time we saw that job link).
    """
    now = now or _utc_now()
    now_str = utc_timestamp_str(now)
    seen = load_seen_index(index_path)

    for job in jobs:
        link = str(job.get("Link", "") or "")
        url_key = extract_url_from_markdown_link(link).strip()
        if not url_key:
            # fallback key
            url_key = f"{job.get('Company','')}|{job.get('Title','')}|{job.get('Location','')}"

        first_seen = seen.get(url_key)
        if not first_seen:
            seen[url_key] = now_str
            first_seen = now_str

        job["Added At"] = first_seen

    save_seen_index(seen, index_path)
    return jobs

def get_target_month() -> str:
    """
    Returns target month in 'YYYY-MM' format.
    Defaults to current UTC month, overridable via TARGET_MONTH env var.
    """
    env = os.getenv("TARGET_MONTH")
    if env and len(env) == 7 and env[4] == "-":
        return env
    return _utc_now().strftime("%Y-%m")


def get_target_date() -> str:
    """
    Returns target date in 'YYYY-MM-DD' format.
    Defaults to current UTC date, overridable via TARGET_DATE env var.
    """
    env = os.getenv("TARGET_DATE")
    if env and len(env) == 10 and env[4] == "-" and env[7] == "-":
        return env
    return _utc_now().strftime("%Y-%m-%d")


def month_label_from_target_month(target_month: str) -> str:
    # target_month: YYYY-MM
    year, month = target_month.split("-")
    dt = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
    return dt.strftime("%B %Y")


def day_label_from_target_date(target_date: str) -> str:
    # target_date: YYYY-MM-DD
    year, month, day = target_date.split("-")
    dt = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    # Example: April 22, 2026
    return dt.strftime("%B %-d, %Y") if os.name != "nt" else dt.strftime("%B %#d, %Y")


def output_daily_csv_filename(target_date: str) -> str:
    # opportunities_2026_04_22.csv
    return f"opportunities_{target_date.replace('-', '_')}.csv"


def output_daily_txt_filename(target_date: str) -> str:
    # opportunities_2026_04_22.txt
    return f"opportunities_{target_date.replace('-', '_')}.txt"


def output_csv_filename(target_month: str) -> str:
    # opportunities_2026_04.csv
    return f"opportunities_{target_month.replace('-', '_')}.csv"

def output_txt_filename(target_month: str) -> str:
    # opportunities_2026_04.txt
    return f"opportunities_{target_month.replace('-', '_')}.txt"


def cleanup_old_csv_files(keep: int = None) -> list[str]:
    """
    Keeps only the newest N CSVs matching opportunities_YYYY_MM_DD.csv in the repo root.
    Returns list of deleted filenames.
    """
    keep = keep or int(os.getenv("KEEP_CSV_FILES", "14"))
    prefix = "opportunities_"
    suffix = ".csv"

    candidates: list[tuple[str, str]] = []
    for name in os.listdir("."):
        if not (name.startswith(prefix) and name.endswith(suffix)):
            continue
        # opportunities_YYYY_MM_DD.csv -> YYYY_MM_DD
        key = name[len(prefix) : -len(suffix)]
        # basic validation
        if len(key) == 10 and key[4] == "_" and key[7] == "_":
            candidates.append((key, name))

    # Sort newest first (YYYY_MM lexicographic works)
    candidates.sort(key=lambda x: x[0], reverse=True)
    to_delete = candidates[keep:]

    deleted: list[str] = []
    for _, name in to_delete:
        try:
            os.remove(name)
            deleted.append(name)
        except Exception:
            continue
    return deleted


def cleanup_old_txt_files(keep: int = None) -> list[str]:
    """
    Keeps only the newest N TXTs matching opportunities_YYYY_MM_DD.txt in the repo root.
    Returns list of deleted filenames.
    """
    keep = keep or int(os.getenv("KEEP_TXT_FILES", os.getenv("KEEP_CSV_FILES", "14")))
    prefix = "opportunities_"
    suffix = ".txt"

    candidates: list[tuple[str, str]] = []
    for name in os.listdir("."):
        if not (name.startswith(prefix) and name.endswith(suffix)):
            continue
        key = name[len(prefix) : -len(suffix)]
        if len(key) == 10 and key[4] == "_" and key[7] == "_":
            candidates.append((key, name))

    candidates.sort(key=lambda x: x[0], reverse=True)
    to_delete = candidates[keep:]

    deleted: list[str] = []
    for _, name in to_delete:
        try:
            os.remove(name)
            deleted.append(name)
        except Exception:
            continue
    return deleted


def build_linkedin_search_url(job_title: str, location: str) -> str:
    # NOTE: geoId hardcoded for India; keep location string for UI only
    return (
        "https://www.linkedin.com/jobs/search/?"
        "f_E=1&origin=JOB_SEARCH_PAGE_JOB_FILTER&geoId=102713980&"
        f"keywords={job_title}&location={location}&refresh=true&sortBy=DD"
    )


def setup_chrome_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()

    # In GitHub Actions we install Chrome; locally Chrome is usually present.
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

    # Rotate user agents lightly (helps avoid identical fingerprints run-to-run)
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
    """
    Tries to click common "load more" buttons on LinkedIn jobs search.
    Returns True if a button was clicked, else False.
    """
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

def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None) -> list:
    # Sets the pages to scrape if not provided
    pages = pages or 3
    jobs = []

    driver = None
    try:
        driver = setup_chrome_driver()

        search_url = build_linkedin_search_url(job_title, location)
        logger.info("Navigating to: %s", search_url)
        driver.get(search_url)
        polite_sleep(2.0, 4.5)

        # Scroll/load content a few times (avoid brittle absolute XPaths)
        for i in range(pages):
            logger.info("Processing scroll batch %s/%s for '%s'", i + 1, pages, job_title)

            # incremental scrolling helps trigger lazy loading
            for _ in range(4):
                driver.execute_script("window.scrollBy(0, Math.floor(document.body.scrollHeight/4));")
                polite_sleep(0.8, 1.7)

            clicked = click_load_more_if_present(driver)
            if clicked:
                logger.info("Loaded more jobs (clicked button).")
            else:
                logger.info("No load-more button found/clickable.")

            polite_sleep(2.5, 5.5)

        page = driver.page_source or ""
        # crude bot-detection heuristic
        lowered = page.lower()
        if "unusual activity" in lowered or "verify" in lowered and "captcha" in lowered:
            logger.warning("LinkedIn likely blocked the scrape (captcha/unusual activity).")

        soup = BeautifulSoup(page, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        logger.info("Found %s job listings", len(job_listings))

        for idx, job in enumerate(job_listings, 1):
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
                    for keyword in ["intern", "apprentice", "trainee", "graduate"]
                )

                if is_relevant:
                    jobs.append(
                        {
                            "Role": job_title.title(),
                            "Company": job_company,
                            "Title": job_title_text,
                            "Location": job_location,
                            "Link": f"[Apply]({apply_link})",
                            "Date Posted": date_posted,
                        }
                    )
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


def save_job_data(data: list, target_date: str) -> None:
    """
    Save job data to README.md file.

    Args:
        data: A list containing job data dictionaries.

    Returns:
        None
    """
    if not data:
        logger.warning("No data to save")
        return

    try:
        # Sort jobs by latest date posted
        data = sorted(data, key=lambda x: x.get("Date Posted", ""), reverse=True)

        # Create a pandas DataFrame from the job data list
        df = pd.DataFrame(data)

        # Drop duplicate links to be clean
        if 'Link' in df.columns:
            df = df.drop_duplicates(subset=["Link"])

        def _render_job_blocks(rows: list[dict]) -> str:
            """
            Renders each job in fixed template with a blank line between jobs.
            """
            blocks: list[str] = []
            for r in rows:
                blocks.append(
                    "\n".join(
                        [
                            f"ROLE - {r.get('Role', '')}",
                            f"COMPANY - {r.get('Company', '')}",
                            f"TITLE - {r.get('Title', '')}",
                            f"DATE POSTED - {r.get('Date Posted', '')}",
                            f"ADDED AT - {r.get('Added At', '')}",
                            f"LOCATION - {r.get('Location', '')}",
                            f"APPLY LINK - {r.get('Link', '')}",
                        ]
                    )
                )
            return "\n\n".join(blocks) + ("\n" if blocks else "")

        # Read existing README.md
        if not os.path.exists('README.md'):
            logger.warning("README.md not found. Skipping README update.")
            return

        with open('README.md', 'r', encoding='utf-8', errors='ignore') as f:
            readme_content = f.read()

        # Update stats
        total_jobs = len(df)
        current_date = _utc_now().strftime("%Y-%m-%d %H:%M UTC")
        day_label = day_label_from_target_date(target_date)
        
        roles_emoji = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫"]
        stats_md = f"## 📅 {day_label} Opportunities ({total_jobs} Jobs)\n"
        stats_md += f"**Last Updated:** {current_date} | **Status:** Live ✅\n\n"
        stats_md += "### Job Categories:\n"
        
        if 'Role' in df.columns:
            role_counts = df['Role'].value_counts()
            for i, (role, count) in enumerate(role_counts.items()):
                emoji = roles_emoji[i % len(roles_emoji)]
                stats_md += f"- {emoji} **{role}**: {count} jobs\n"

        stats_start = readme_content.find('<!--START_SECTION:stats-->')
        stats_end = readme_content.find('<!--END_SECTION:stats-->')

        if stats_start != -1 and stats_end != -1:
            readme_content = (
                readme_content[:stats_start + len('<!--START_SECTION:stats-->\n')]
                + stats_md
                + readme_content[stats_end:]
            )

        # Find markers for table
        start = readme_content.find('<!--START_SECTION:workfetch-->')
        end = readme_content.find('<!--END_SECTION:workfetch-->')

        if start == -1 or end == -1:
            logger.warning("Table markers not found in README.md")
            return

        # Create fixed-format blocks (instead of markdown table)
        job_blocks = _render_job_blocks(df.to_dict(orient="records")) if len(df) > 0 else "No jobs found\n"
        
        # Create new README content
        new_readme_content = (
            f"{readme_content[:start]}"
            f"<!--START_SECTION:workfetch-->\n{job_blocks}"
            f"{readme_content[end:]}"
        )

        # Write updated README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_readme_content)

        logger.info("Successfully updated README.md with %s jobs", len(data))

    except Exception as e:
        logger.exception("Error saving data: %s", str(e))


def filter_jobs_by_date(jobs: list, target_date: str) -> list:
    """
    Filter jobs by target date (YYYY-MM-DD).

    Args:
        jobs: List of job dictionaries
        target_date: Target date in format "YYYY-MM-DD"

    Returns:
        Filtered list of jobs
    """
    filtered = []
    for job in jobs:
        date_posted = job.get("Date Posted", "")
        if date_posted.startswith(target_date):
            filtered.append(job)
    return filtered


def save_to_csv(data: list, filename: str) -> None:
    """
    Save job data to a real comma-separated CSV file (for Excel/CSV tools).

    Args:
        data: List of job dictionaries
        filename: Output CSV filename

    Returns:
        None
    """
    if not data:
        logger.warning("No data to save")
        return

    try:
        df = pd.DataFrame(data)
        # Normalize column order if present
        preferred = ["Role", "Company", "Title", "Location", "Link", "Date Posted", "Added At"]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        df = df[cols]
        # Quote all fields so commas inside values don't break the CSV
        df.to_csv(filename, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL)
        logger.info("Successfully saved %s jobs to %s", len(data), filename)
    except Exception as e:
        logger.exception("Error saving CSV: %s", str(e))


def parse_job_blocks(text: str) -> list[dict]:
    """
    Parse block-formatted jobs (ROLE/COMPANY/TITLE/DATE POSTED/LOCATION/APPLY LINK)
    separated by blank lines into list[dict].
    """
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    jobs: list[dict] = []
    for b in blocks:
        job: dict = {}
        for line in b.splitlines():
            if " - " not in line:
                continue
            key, val = line.split(" - ", 1)
            key = key.strip().upper()
            val = val.strip()
            if key == "ROLE":
                job["Role"] = val
            elif key == "COMPANY":
                job["Company"] = val
            elif key == "TITLE":
                job["Title"] = val
            elif key == "DATE POSTED":
                job["Date Posted"] = val
            elif key == "ADDED AT":
                job["Added At"] = val
            elif key == "LOCATION":
                job["Location"] = val
            elif key == "APPLY LINK":
                job["Link"] = val
        if job:
            jobs.append(job)
    return jobs


def migrate_block_csv_to_txt_and_real_csv(
    block_csv_path: str,
    txt_path: str,
    real_csv_path: str,
) -> None:
    """
    If an old .csv was written in block-format, convert it to:
    - .txt (same block-format)
    - real CSV (comma-separated)
    """
    if not os.path.exists(block_csv_path):
        return
    with open(block_csv_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    jobs = parse_job_blocks(content)
    if not jobs:
        return
    # keep the original block content as txt
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content if content.endswith("\n") else content + "\n")
    save_to_csv(jobs, real_csv_path)


def save_to_txt(data: list, filename: str) -> None:
    """
    Save job data to a human-readable TXT using fixed template.
    """
    if not data:
        logger.warning("No data to save")
        return

    try:
        # newest first
        data = sorted(data, key=lambda x: x.get("Date Posted", ""), reverse=True)
        blocks: list[str] = []
        for job in data:
            blocks.append(
                "\n".join(
                    [
                        f"ROLE - {job.get('Role', '')}",
                        f"COMPANY - {job.get('Company', '')}",
                        f"TITLE - {job.get('Title', '')}",
                        f"DATE POSTED - {job.get('Date Posted', '')}",
                        f"ADDED AT - {job.get('Added At', '')}",
                        f"LOCATION - {job.get('Location', '')}",
                        f"APPLY LINK - {job.get('Link', '')}",
                    ]
                )
            )
        content = "\n\n".join(blocks) + "\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Successfully saved %s jobs to %s", len(data), filename)
    except Exception as e:
        logger.exception("Error saving TXT: %s", str(e))

if __name__ == "__main__":
    target_date = get_target_date()
    day_label = day_label_from_target_date(target_date)
    csv_file = output_daily_csv_filename(target_date)
    txt_file = output_daily_txt_filename(target_date)

    print("=" * 70)
    print(f"OPPORTUNITYHUB - {day_label} Job Opportunities Scraper")
    print("=" * 70)
    print(f"Target Date: {target_date} ({day_label})")
    print(f"Target Roles: {', '.join(TARGET_ROLES)}")
    print("This may take 10-20 minutes (LinkedIn rate limiting)...\n")

    all_jobs = []
    location = "India"

    try:
        # Scrape jobs for each target role
        for idx, role in enumerate(TARGET_ROLES, 1):
            print(f"\n[{idx}/{len(TARGET_ROLES)}] Scraping for: {role}")
            print("-" * 70)
            
            jobs = scrape_linkedin_jobs(role, location, pages=3)
            
            if jobs:
                print(f"✓ Found {len(jobs)} jobs for '{role}'")
                all_jobs.extend(jobs)
                time.sleep(random.randint(8, 15))  # Rate limiting
            else:
                print(f"✗ No jobs found for '{role}'")

        print("\n" + "=" * 70)
        print(f"\nTotal jobs found: {len(all_jobs)}")

        if all_jobs:
            filtered_jobs = filter_jobs_by_date(all_jobs, target_date)
            print(f"📅 Jobs from {target_date}: {len(filtered_jobs)}")

            if filtered_jobs:
                # Sort by date (newest first)
                filtered_jobs = sorted(filtered_jobs, key=lambda x: x.get("Date Posted", ""), reverse=True)
                # Attach "Added At" timestamp (first time seen) and persist it
                filtered_jobs = add_added_at(filtered_jobs)
                
                # Save to CSV
                save_to_csv(filtered_jobs, csv_file)

                # Save to TXT (requested fixed template)
                save_to_txt(filtered_jobs, txt_file)

                # One-time safety: if legacy block-format was stored in a .csv, migrate it.
                # (Helps avoid CSVLint / Excel errors.)
                try:
                    migrate_block_csv_to_txt_and_real_csv(
                        "april_2026_opportunities.csv",
                        "april_2026_opportunities.txt",
                        "opportunities_2026_04.csv",
                    )
                except Exception:
                    pass

                # Repo size hygiene: keep only last N monthly CSVs
                deleted = cleanup_old_csv_files()
                if deleted:
                    logger.info("Cleaned up old CSVs: %s", ", ".join(deleted))
                deleted_txt = cleanup_old_txt_files()
                if deleted_txt:
                    logger.info("Cleaned up old TXTs: %s", ", ".join(deleted_txt))
                
                # Also save to README
                save_job_data(filtered_jobs, target_date)
                
                print("\n✨ Job opportunities summary:")
                for job in filtered_jobs:
                    print(f"  • {job['Title']} at {job['Company']} ({job['Date Posted']})")
                    
            else:
                print(f"\n⚠ No jobs found for {target_month}")
        else:
            print("\n❌ No jobs found in any search.")

        print("=" * 70)
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        print("=" * 70)
