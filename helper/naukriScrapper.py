import os
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup

# Set ChromeDriver path
chrome_driver_path = r"/Users/arun/Downloads/chromedriver-mac-arm64/chromedriver"
os.environ["CHROME_DRIVER_PATH"] = chrome_driver_path

BASE_URL = "https://www.naukri.com"

def extract_job_details(page_source):
    """Extract job details from the page source using BeautifulSoup."""
    soup = BeautifulSoup(page_source, 'html.parser')
    jobs = []

    job_wrappers = soup.find_all('div', class_='srp-jobtuple-wrapper')
    for job in job_wrappers:
        try:
            title_tag = job.find('a', class_='title')
            title = title_tag.text.strip() if title_tag else None
            job_url = title_tag['href'] if title_tag else None
            if job_url and not job_url.startswith("http"):
                job_url = BASE_URL + job_url

            company_tag = job.find('a', class_='comp-name')
            company = company_tag.text.strip() if company_tag else None

            salary_tag = job.find('span', class_='sal-wrap')
            salary = salary_tag.text.strip() if salary_tag else "Not Disclosed"

            location_tag = job.find('span', class_='loc-wrap')
            location = location_tag.text.strip() if location_tag else None

            skills = [skill.text for skill in job.find_all('li', class_='tag-li')]

            jobs.append({
                'title': title,
                'company': company,
                'salary': salary,
                'location': location,
                'skills': skills,
                'url': job_url
            })
        except Exception as e:
            print(f"Error extracting job details: {e}")

    return jobs

def scrape_job_description(driver, url):
    """Scrape job description from the job detail page."""
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_description = soup.find('div', class_='styles_JDC__dang-inner-html__h0K4t')
        return job_description.get_text(separator="\n").strip() if job_description else "Job description not found."
    except Exception as e:
        print(f"Error scraping job description: {e}")
        return None

def save_to_csv(jobs, filename):
    """Save job details to a CSV file."""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["Title", "Company", "Salary", "Location", "Skills", "URL", "Description"])
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "Title": job['title'],
                    "Company": job['company'],
                    "Salary": job['salary'],
                    "Location": job['location'],
                    "Skills": ', '.join(job['skills']),
                    "URL": job['url'],
                    "Description": job.get('description', "N/A")
                })
        print(f"\n✅ Job details saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

# Setup Selenium driver
chrome_options = ChromeOptions()
# chrome_options.add_argument("--headless")  # Optional headless mode
service = ChromeService(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    base_search_url = "https://www.naukri.com/developer-engineer-it-jobs-in-chennai?k=developer%2C%20engineer%2C%20it&l=chennai&nignbevent_src=jobsearchDeskGNB&experience=0&jobAge=1"
    all_job_listings = []
    page = 1

    while True:
        paged_url = f"{base_search_url}&page={page}"
        print(f"\n🔄 Loading page {page}: {paged_url}")
        driver.get(paged_url)
        time.sleep(4)

        page_source = driver.page_source
        job_listings = extract_job_details(page_source)

        if not job_listings:
            print("🚫 No more job listings found. Ending scrape.")
            break

        for job in job_listings:
            if job['url']:
                job['description'] = scrape_job_description(driver, job['url'])
            else:
                job['description'] = "URL not available"
            all_job_listings.append(job)

        page += 1
        if page > 10:  # optional stop condition
            break

    # Save all listings to CSV
    save_to_csv(all_job_listings, "job_listings.csv")

finally:
    driver.quit()
    print("🧹 Driver closed.")
