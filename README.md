Step 1: Install Python requirements

You need Python 3.8+ installed. Then, in a terminal, run:

bash
pip install requests selenium webdriver-manager python-dotenv

You also need Google Chrome installed (free) — auto_fill_helper.py drives it directly.

Step 2: Put both files in the same folder

Make sure ai_ml_job_finder.py and auto_fill_helper.py are in the same directory. They share files (ai_ml_jobs.csv, seen_jobs.json) that get created automatically in that folder when you run them.

Step 3: Configure ai_ml_job_finder.py

Open the file and edit the settings near the top:

INCLUDE_KEYWORDS — add/remove terms relevant to the roles you want (e.g. add "reinforcement learning", "data engineer", a city name).
EXCLUDE_KEYWORDS — seniority terms to skip (already set to reasonable defaults like senior, staff, lead, etc.).
REQUIRE_JUNIOR_KEYWORD — leave False for broader results, or set to True if you only want postings that explicitly say "junior"/"graduate"/ "entry level" etc.

Step 4: Configure auto_fill_helper.py via your .env file

Your personal details now live in a .env file instead of the script itself, so they never accidentally get pushed to GitHub.

A .env file is already included — open it and fill in your real details:
   CANDIDATE_FIRST_NAME=
   CANDIDATE_LAST_NAME=
   CANDIDATE_FULL_NAME=
   CANDIDATE_EMAIL=
   CANDIDATE_PHONE=
   CANDIDATE_LINKEDIN=
   CANDIDATE_GITHUB=
   CV_PATH=
CV_PATH needs to be an absolute path to your CV PDF, e.g.:
Mac/Linux: /Users/yourname/Documents/CV.pdf
Windows: C:\Users\yourname\Documents\CV.pdf
.env.example is a blank template with no real data — that one is safe to commit to GitHub, so if you ever set this up on a new computer you know exactly which fields to fill in.
.env itself is listed in .gitignore (see Step 7 below) so git will never pick it up, even with git add ..
In auto_fill_helper.py, you can still adjust MAX_JOBS_PER_RUN — how many application pages to open per run (default 5 — keep this small since you review each one).
Step 5: Run them in order

Always run the finder first, then the helper:

bash
python ai_ml_job_finder.py
python auto_fill_helper.py

What happens:

ai_ml_job_finder.py fetches current listings, filters them, prints any new matches to your terminal, and appends them to ai_ml_jobs.csv. Run this as often as you like (e.g. once a day) — it only shows you jobs it hasn't shown you before.
auto_fill_helper.py reads the most recent rows from ai_ml_jobs.csv, opens each job's page in a new Chrome tab, tries to fill in your contact details and attach your resume, then pauses and waits for you to press Enter in the terminal before moving to the next job — giving you time to check the page, answer any custom questions, and click submit yourself.

Step 6: (Optional) Automate step 5 so you don't have to remember

All free, no server costs:

Mac/Linux (cron): run crontab -e and add a line to run the finder every morning at 8am:
 0 8 * * * /usr/bin/python3 /full/path/to/ai_ml_job_finder.py

Windows: use Task Scheduler to run ai_ml_job_finder.py daily.

Cloud (no computer needed): push the finder script to a GitHub repo and add a GitHub Actions workflow with a schedule: cron: trigger. Public repos get free scheduled Actions minutes. Note: only the finder script makes sense to run in the cloud — the helper opens a visible Chrome window for you to interact with, so run that one locally.

Troubleshooting:

"No module named selenium/requests/dotenv" → re-run pip install requests selenium webdriver-manager python-dotenv.
"Missing values in your .env file" → open .env and make sure every line has a value filled in after the =.
Chrome won't open / version mismatch → update Chrome to the latest version; webdriver-manager will fetch a matching driver automatically next run.
Resume not uploading → double check RESUME_PATH is an absolute path and the file actually exists there.
Few or no fields get pre-filled → normal for heavily custom forms (Workday, Greenhouse multi-step wizards). The helper matches common field naming patterns; unusual forms you'll fill by hand — the tab is already open and your resume file is ready to drag in.
A site blocks/flags automated browsing → close the tab and apply manually there. Some sites actively detect automation; this is exactly why the script never tries to auto-submit.