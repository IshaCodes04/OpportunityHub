import logging
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
import chromedriver_autoinstaller  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd
import random
import time
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Target roles for scraping
TARGET_ROLES = [
    "full stack developer mern stack",
    "software engineer",
    "mern stack developer",
    "backend developer",
    "frontend developer",
    "data scientist",
    "devops",
    "ai engineer"
]

# Target month for filtering
TARGET_MONTH = "2026-04"  # April 2026

def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None) -> list:
    # Sets the pages to scrape if not provided
    pages = pages or 3
    jobs = []

    try:
        chromedriver_autoinstaller.install()

        chrome_options = webdriver.ChromeOptions()
        options = [
            "--window-size=1200,1200",
            "--ignore-certificate-errors",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ]

        for option in options:
            chrome_options.add_argument(option)

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        # Navigate to the LinkedIn job search page
        search_url = f"https://www.linkedin.com/jobs/search/?f_E=1&origin=JOB_SEARCH_PAGE_JOB_FILTER&geoId=102713980&keywords={job_title}&location={location}&refresh=true&sortBy=DD"
        print(f"📍 Navigating to: {search_url}")
        driver.get(search_url)

        # Scroll through pages
        for i in range(pages):
            print(f"📜 Processing page {i+1}/{pages}...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "/html/body/div[1]/div/main/section[2]/button")
                    )
                )
                element.click()
                print(f"✓ Loaded more jobs...")
            except Exception:
                print(f"ℹ No more jobs to load")

            time.sleep(random.choice(list(range(3, 7))))

        # Scrape the job postings
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        print(f"🔍 Found {len(job_listings)} job listings")

        for idx, job in enumerate(job_listings, 1):
            try:
                # Extract job details safely
                title_elem = job.find("h3", class_="base-search-card__title")
                company_elem = job.find("h4", class_="base-search-card__subtitle")
                location_elem = job.find("span", class_="job-search-card__location")
                link_elem = job.find("a", class_="base-card__full-link")
                date_elem = job.find("time")

                if not all([title_elem, company_elem, location_elem, link_elem, date_elem]):
                    print(f"⚠ Skipping job {idx}: Missing required fields")
                    continue

                job_title_text = title_elem.text.strip()
                job_company = company_elem.text.strip()
                job_location = location_elem.text.strip()
                apply_link = link_elem.get("href", "#")
                date_posted = date_elem.get("datetime", "N/A")

                # Check if it's an internship/trainee position
                is_relevant = any(keyword.lower() in job_title_text.lower() 
                                for keyword in ['intern', 'apprentice', 'trainee', 'graduate'])

                if is_relevant:
                    jobs.append({
                        "Role": job_title.title(),
                        "Company": job_company,
                        "Title": job_title_text,
                        "Location": job_location,
                        "Link": f"[Apply]({apply_link})",
                        "Date Posted": date_posted
                    })
                    print(f"✓ Job {idx}: {job_title_text[:40]}... at {job_company}")

            except Exception as e:
                print(f"⚠ Error processing job {idx}: {str(e)}")
                continue

        driver.quit()

    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        try:
            driver.quit()
        except:
            pass

    return jobs


def save_job_data(data: list) -> None:
    """
    Save job data to README.md file.

    Args:
        data: A list containing job data dictionaries.

    Returns:
        None
    """
    if not data:
        print("⚠ No data to save")
        return

    try:
        # Sort jobs by latest date posted
        data = sorted(data, key=lambda x: x.get("Date Posted", ""), reverse=True)

        # Create a pandas DataFrame from the job data list
        df = pd.DataFrame(data)

        # Drop duplicate links to be clean
        if 'Link' in df.columns:
            df = df.drop_duplicates(subset=["Link"])

        # Read existing README.md
        if not os.path.exists('README.md'):
            print("⚠ README.md not found. Creating one...")
            return

        with open('README.md', 'r', encoding='utf-8', errors='ignore') as f:
            readme_content = f.read()

        # Update stats
        total_jobs = len(df)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        
        roles_emoji = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫"]
        stats_md = f"## 📅 April 2026 Opportunities ({total_jobs} Jobs)\n"
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
            print("⚠ Table markers not found in README.md")
            return

        # Create markdown table
        markdown_table = df.to_markdown(index=False) if len(df) > 0 else "No jobs found"
        
        # Create new README content
        new_readme_content = (
            f"{readme_content[:start]}"
            f"<!--START_SECTION:workfetch-->\n{markdown_table}\n"
            f"{readme_content[end:]}"
        )

        # Write updated README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_readme_content)

        print(f"✅ Successfully updated README.md with {len(data)} jobs")

    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")


def filter_jobs_by_date(jobs: list, target_month: str) -> list:
    """
    Filter jobs by target month.

    Args:
        jobs: List of job dictionaries
        target_month: Target month in format "YYYY-MM"

    Returns:
        Filtered list of jobs
    """
    filtered = []
    for job in jobs:
        date_posted = job.get("Date Posted", "")
        if date_posted.startswith(target_month):
            filtered.append(job)
    return filtered


def save_to_csv(data: list, filename: str = "april_2026_opportunities.csv") -> None:
    """
    Save job data to CSV file.

    Args:
        data: List of job dictionaries
        filename: Output CSV filename

    Returns:
        None
    """
    if not data:
        print("⚠ No data to save")
        return

    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Successfully saved {len(data)} jobs to {filename}")
    except Exception as e:
        print(f"❌ Error saving CSV: {str(e)}")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 OPPORTUNITYHUB - April 2026 Job Opportunities Scraper")
    print("=" * 70)
    print(f"📅 Target Month: April 2026")
    print(f"🎯 Target Roles: {', '.join(TARGET_ROLES)}")
    print("⏳ This may take 10-20 minutes (LinkedIn rate limiting)...\n")

    all_jobs = []
    location = "India"

    try:
        # Scrape jobs for each target role
        for idx, role in enumerate(TARGET_ROLES, 1):
            print(f"\n[{idx}/{len(TARGET_ROLES)}] 🔍 Scraping for: {role}")
            print("-" * 70)
            
            jobs = scrape_linkedin_jobs(role, location, pages=3)
            
            if jobs:
                print(f"✓ Found {len(jobs)} jobs for '{role}'")
                all_jobs.extend(jobs)
                time.sleep(random.randint(5, 10))  # Rate limiting
            else:
                print(f"✗ No jobs found for '{role}'")

        print("\n" + "=" * 70)
        print(f"📊 Total jobs found: {len(all_jobs)}")

        if all_jobs:
            # Filter for April 2026
            april_jobs = filter_jobs_by_date(all_jobs, TARGET_MONTH)
            print(f"📅 Jobs from {TARGET_MONTH}: {len(april_jobs)}")

            if april_jobs:
                # Sort by date (newest first)
                april_jobs = sorted(april_jobs, key=lambda x: x.get("Date Posted", ""), reverse=True)
                
                # Save to CSV
                save_to_csv(april_jobs)
                
                # Also save to README
                save_job_data(april_jobs)
                
                print("\n✨ Job opportunities summary:")
                for job in april_jobs:
                    print(f"  • {job['Title']} at {job['Company']} ({job['Date Posted']})")
                    
            else:
                print(f"\n⚠ No jobs found for {TARGET_MONTH}")
        else:
            print("\n❌ No jobs found in any search.")

        print("=" * 70)
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        print("=" * 70)
