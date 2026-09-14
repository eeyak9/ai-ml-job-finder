import csv
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

load_dotenv()

CANDIDATE = {
    "first_name": os.environ.get("CANDIDATE_FIRST_NAME", ""),
    "last_name": os.environ.get("CANDIDATE_LAST_NAME", ""),
    "full_name": os.environ.get("CANDIDATE_FULL_NAME", ""),
    "email": os.environ.get("CANDIDATE_EMAIL", ""),
    "phone": os.environ.get("CANDIDATE_PHONE", ""),
    "linkedin": os.environ.get("CANDIDATE_LINKEDIN", ""),
    "github": os.environ.get("CANDIDATE_GITHUB", ""),
}

CV_PATH = os.environ.get("CV_PATH", "")

INPUT_CSV = "ai_ml_jobs.csv"

REQUIRED_ENV_VARS = [
    "CANDIDATE_FIRST_NAME", "CANDIDATE_LAST_NAME", "CANDIDATE_FULL_NAME","CANDIDATE_EMAIL", 
    "CANDIDATE_PHONE", "CANDIDATE_LINKEDIN", "CANDIDATE_GITHUB", "CV_PATH",
]

def check_env():
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print("Missing values in your .env file: " + ", ".join(missing))
        raise SystemExit(1)

MAX_JOBS_PER_RUN = 5

# ---------------------------------------------------------------------------
# FIELD_MATCHING
# ---------------------------------------------------------------------------

TEXT_FIELD_RULES = [
    (["first_name", "firstname", "first-name"], CANDIDATE["first_name"]),
    (["last_name", "lastname", "last-name", "surname"], CANDIDATE["last_name"]),
    (["full_name", "fullname", "your name", "candidate name"], CANDIDATE["full_name"]),
    (["email"], CANDIDATE["email"]),
    (["phone", "mobile", "telephone"], CANDIDATE["phone"]),
    (["linkedin"], CANDIDATE["linkedin"]),
    (["Github", "GITHUB", "github"], CANDIDATE["github"]),
]
 
CV_FIELD_HINTS = ["resume", "cv", "curriculum"]

APPLY_BUTTON_TEXTS = [
    "apply now", "apply for this job", "apply here", "quick apply",
    "apply for this position", "apply",

]
 
def build_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=service, options=options)

def field_signature(el):
    """Combine attributes that usually hint at a field's purpose."""
    attrs = []
    for attr in ("name", "id", "placeholder", "aria-label"):
        try:
            val = el.get_attribute(attr) or ""
            attrs.append(val.lower())
        except Exception:
            pass
    return " ".join(attrs)

def find_apply_element(driver):
    """Look for a visible link/button whose text matches common 'Apply'
    wording. Returns the element, or None if nothing looked like one."""
    candidates = driver.find_elements(By.XPATH, "//a | //button")
    for el in candidates:
        try:
            if not el.is_displayed():
                continue
            text = (el.text or el.get_attribute("value") or "").strip().lower()
        except Exception:
            continue
        if not text:
            continue
        for kw in APPLY_BUTTON_TEXTS:
            if text == kw or text.startswith(kw):
                return el
    return None
 
def click_apply_and_wait(driver, timeout=10):
    """Clicks an 'Apply' button/link if found, then waits for either a new
    tab to open or the page to navigate, and switches focus to it.
    Returns True if an Apply element was found and clicked."""
    before_handles = set(driver.window_handles)
    before_url = driver.current_url
 
    el = find_apply_element(driver)
    if not el:
        return False
 
    try:
        el.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", el)
        except Exception:
            return False
 
    end_time = time.time() + timeout
    while time.time() < end_time:
        after_handles = set(driver.window_handles)
        new_handles = after_handles - before_handles
        if new_handles:
            driver.switch_to.window(list(new_handles)[0])
            return True
        if driver.current_url != before_url:
            return True
        time.sleep(0.5)
    return True

def try_fill_text_fields(driver):
    filled = 0
    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type]), input[type='email'], input[type='tel'], textarea")
    for el in inputs:
        sig = field_signature(el)
        if not sig:
            continue
        for hints, value in TEXT_FIELD_RULES:
            if any(h in sig for h in hints):
                try:
                    el.clear()
                    el.send_keys(value)
                    filled += 1
                except Exception:
                    pass
                break
    return filled

def try_upload_CV(driver):
    if not os.path.isfile(CV_PATH):
        print(f" ! CV file not found at {CV_PATH}, skipping upload.")
        return False
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    for el in file_inputs:
        sig = field_signature(el)
        if any(h in sig for h in CV_FIELD_HINTS) or len(file_inputs) == 1:
            try:
                el.send_keys(CV_PATH)
                return True
            except Exception:
                pass
    return False

def load_jobs(csv_path, limit):
    jobs = []
    if not os.path.exists(csv_path):
        print(f"Could not find {csv_path}. Run ai_ml_job_finder.py first.")
        return jobs
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("url"):
                jobs.append(row)
    return jobs

def remove_job_from_csv(csv_path, job_url):
    if not os.path.exists(csv_path):
        return
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        remaining = [row for row in reader if row.get("url") != job_url]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(remaining)


def main():
    check_env()
    all_jobs = load_jobs(INPUT_CSV, MAX_JOBS_PER_RUN)
    if not all_jobs:
        print("No jobs to process.")
        return

    jobs = all_jobs[:MAX_JOBS_PER_RUN]
    remaining_after = len(all_jobs) - len(jobs)
    print(f"Opening {len(jobs)} application pages. Review and submit each one manually.")
    driver = build_driver()
 
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}] {job['title']} @ {job['company']}")
        print(f"  URL: {job['url']}")
        driver.execute_script(f"window.open('{job['url']}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(3)  # let the page load before trying to find fields

        clicked = click_apply_and_wait(driver)
        if clicked:
            time.sleep(3)  # let the application form finish loading
            print("  Clicked 'Apply' and moved to the application form.")
        else:
            print("  No separate 'Apply' button detected - treating this "
                  "page as the application form itself.")
 
        filled = try_fill_text_fields(driver)
        uploaded = try_upload_CV(driver)
        print(f"  Pre-filled {filled} text field(s). CV attached: {uploaded}.")
        print("  -> Review the page carefully, answer any custom questions, "
              "then submit it yourself.")
 
        while True:
            cmd = input(
                "  Press Enter to move to the next job, or type 'r' + Enter "
                "to re-scan and fill again (e.g. after you've clicked "
                "'Next' to a further step in the form)... "
            ).strip().lower()
            if cmd == "r":
                filled = try_fill_text_fields(driver)
                uploaded = try_upload_CV(driver)
                print(f"  Re-scanned page: pre-filled {filled} field(s). "
                      f"Resume attached: {uploaded}.")
                continue
            break

        remove_job_from_csv(INPUT_CSV, job["url"])
        print("   Removed from queue")
 
    print("\nAll done for this run. Close the browser window when ready.")
 
 
if __name__ == "__main__":
    main()