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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

        # Check if README.md exists
        if not os.path.exists('README.md'):
            print("⚠ README.md not found. Creating one...")
            with open('README.md', 'w') as f:
                f.write("# Work Fetch: Jobs Scraper\n\n")
                f.write("<!--START_SECTION:workfetch-->\n")
                f.write("No jobs yet\n")
                f.write("<!--END_SECTION:workfetch-->\n")

        # Read existing README.md
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Find markers
        start = readme_content.find('<!--START_SECTION:workfetch-->')
        end = readme_content.find('<!--END_SECTION:workfetch-->')

        if start == -1 or end == -1:
            print("⚠ Markers not found in README.md. Adding them...")
            readme_content += "\n<!--START_SECTION:workfetch-->\n"
            readme_content += "No jobs yet\n"
            readme_content += "<!--END_SECTION:workfetch-->\n"
            start = readme_content.find('<!--START_SECTION:workfetch-->')
            end = readme_content.find('<!--END_SECTION:workfetch-->')

        # Create new README content
        markdown_table = df.to_markdown(index=False) if len(df) > 0 else "No jobs found"
        new_readme_content = (
            f"{readme_content[:start]}"
            f"<!--START_SECTION:workfetch-->\n"
            f"{markdown_table}\n"
            f"{readme_content[end:]}"
        )

        # Write updated README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_readme_content)

        print(f"✅ Successfully saved {len(data)} jobs to README.md")

    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")

if __name__ == "__main__":
    job_title = "Software Engineer"
    location = "India"

    print("=" * 60)
    print("🚀 WORK FETCH - LinkedIn Jobs Scraper")
    print("=" * 60)
    print(f"🔍 Starting scraper for: {job_title} in {location}")
    print("⏳ This may take 5-10 minutes (LinkedIn blocks requests)...\n")

    try:
        jobs = scrape_linkedin_jobs(job_title, location)
        
        if jobs:
            print(f"\n✅ Found {len(jobs)} relevant jobs!")
            save_job_data(jobs)
            print("📝 Data saved to README.md")
            print("=" * 60)
        else:
            print("\n❌ No jobs found. Try different search terms.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        print("=" * 60)
