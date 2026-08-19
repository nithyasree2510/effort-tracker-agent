# Effort Tracker Agent

Automatically reads GitHub PR and issue comments where engineers log their hours, and updates the Engineering Efforts Tracker Google Sheet — replacing the manual process of reading comments and typing hours into the sheet.

**Every time it runs:** the agent reads all comments from the start of the current month, extracts hours using AI, and rewrites the sheet with only the active repos and engineers for that month.

---

## What this replaces

Previously someone manually:
1. Read every PR and issue comment on GitHub
2. Identified hours logged by each engineer per repo
3. Added them up and typed them into the sheet

The agent does all of this automatically in one command.

---

## How engineers should log hours

Engineers write effort in any PR or issue comment. The AI understands any format:

```
Efforts: 5h
Effort - 1 day
BLE Log [spent : 3h]
Effort - half day
actual: 3.5h | planned: 4h
```

Hours should appear in the comment — the agent reads the full comment body. If no hours are mentioned, the comment is skipped automatically.

---

## Setup — do this once

### Step 1 — Download the project

Download and unzip the project folder, or clone it:

```bash
git clone <repo-url>
cd effort-tracker-agent
```

---

### Step 2 — Install Python

Make sure Python 3.11 or higher is installed:

```bash
python3 --version
```

---

### Step 3 — Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Then install:
```bash
python3 -m pip install -r requirements.txt
```

---

### Step 4 — Fill in the .env file

Open the `.env` file in the project folder and fill in all five values:

```
GEMINI_API_KEY=
GITHUB_TOKEN=
GOOGLE_SHEET_ID=
GOOGLE_CREDS_PATH=./credentials.json
GITHUB_ORG=
```

Each value is explained below.

---

### Step 5 — Get your Gemini API key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** → **Create API key**
3. Copy the key
4. Paste it as `GEMINI_API_KEY=` in `.env`

---

### Step 6 — Get your GitHub token

This token is **read-only** — the agent cannot modify, delete, or push anything to GitHub. It only reads comments.

1. Go to github.com → your profile picture → **Settings**
2. Scroll to the bottom of the left sidebar → **Developer Settings**
3. **Personal Access Tokens** → **Fine-grained tokens** → **Generate new token**
4. Set **Resource owner** to your organisation name
5. Set **Repository access** → **All repositories**
6. Under **Permissions**, set each of these to **Read only**:
   - Issues
   - Pull requests
   - Contents
   - Metadata
7. Click **Generate token**
8. Copy the token immediately — GitHub only shows it once
9. Paste it as `GITHUB_TOKEN=` in `.env`
10. Set `GITHUB_ORG=` to your organisation name exactly as it appears on GitHub

> If the token expires, generate a new one following the same steps and update `GITHUB_TOKEN` in `.env`.

---

### Step 7 — Set up Google Sheets access

#### 7a — Create a Google Cloud project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Name it `effort-tracker` → **Create**

#### 7b — Enable required APIs
1. Go to **APIs & Services** → **Enable APIs and Services**
2. Search **Google Sheets API** → **Enable**
3. Go back → search **Google Drive API** → **Enable**

#### 7c — Create a service account
1. Go to **IAM & Admin** → **Service Accounts**
2. Click **+ Create Service Account**
3. Name: `effort-tracker-agent` → **Create and Continue**
4. Role: select **Editor** → **Continue** → **Done**

#### 7d — Download credentials
1. Click on the service account you just created
2. Click the **Keys** tab
3. **Add Key** → **Create new key** → **JSON** → **Create**
4. A file downloads automatically
5. Rename it to `credentials.json`
6. Move it into the project folder (same folder as `run_agent.py`)

#### 7e — Share your Google Sheet with the service account
1. Open `credentials.json` in a text editor
2. Find the `"client_email"` field — copy that email address
3. Open your Engineering Efforts Tracker on Google Sheets
4. Click **Share** (top right)
5. Paste the email address
6. Set permission to **Editor**
7. Uncheck **Notify people**
8. Click **Share**

#### 7f — Get the Sheet ID
Look at your sheet's URL:
```
https://docs.google.com/spreadsheets/d/COPY_THIS_PART/edit
```
Copy only the ID between `/d/` and `/edit` — not the full URL.
Paste it as `GOOGLE_SHEET_ID=` in `.env`.

---

### Step 8 — Verify setup

Run this to confirm all five values are filled:

```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
keys = ['GEMINI_API_KEY','GITHUB_TOKEN','GOOGLE_SHEET_ID','GOOGLE_CREDS_PATH','GITHUB_ORG']
for k in keys:
    v = os.getenv(k)
    print(('✓' if v else '✗ MISSING') + '  ' + k)
"
```

All five must show ✓ before running the agent.

---

## Running the agent

Make sure the virtual environment is active:

```bash
source venv/bin/activate
```

Then run:

```bash
python3 run_agent.py
```

The agent will:
1. Connect to GitHub and fetch all PR and issue comments from the start of the current month
2. Send each comment to Gemini AI to extract planned and actual hours
3. Sum hours per engineer per repository
4. Rewrite the Engineering Efforts Tracker sheet with the results

Only repositories with logged hours appear in the sheet. Repos with no activity this month are automatically excluded.

**The sheet is rewritten fresh on every run** — it always reflects exactly what happened this month.

---

## What the sheet contains after each run

**Section 1 — Customer Burndown:**
One row per active repository. Columns show planned and actual hours per engineer, with BurnDown totals and an Overall row.

**Section 2 — Resource Burndown:**
One row per active engineer. Shows available hours (160h), planned hours (fill manually), and actual hours pulled automatically from Section 1.

> Planned hours and Target columns are left empty for the manager to fill in manually.

---

## Running automatically every month

To run the agent automatically on the first of each month, add a scheduled task:

**Mac/Linux (cron):**
```bash
crontab -e
# Add this line — runs at 9am on the 1st of every month:
0 9 1 * * cd /path/to/effort-tracker-agent && source venv/bin/activate && python3 run_agent.py
```

**Windows (Task Scheduler):**
Create a monthly task that runs `python3 run_agent.py` from the project folder.

---

## Troubleshooting

**"No comments found — sheet cleared, nothing written"**
Engineers may not have logged hours in comments yet this month, or the comments are in a format the agent does not recognise. Check that engineers are writing hours in PR or issue comments.

**"SpreadsheetNotFound"**
`GOOGLE_SHEET_ID` in `.env` may contain the full URL instead of just the ID. It should look like `1fG7QmI7wlx...` not `https://docs.google.com/...`

**"Bad credentials" from GitHub**
The GitHub token has expired. Generate a new one following Step 6 and update `GITHUB_TOKEN` in `.env`.

**Sheet shows wrong data or old repos still appear**
Run the agent again — it clears and rewrites the sheet completely on every run. Old data never carries over.

**Rate limit error from Gemini**
The agent automatically waits between Gemini calls to stay within limits. If you see this error, run the agent again and it will complete.

---

## Security notes

- `.env` and `credentials.json` are listed in `.gitignore` and will never be uploaded to GitHub accidentally
- The GitHub token is read-only — the agent cannot modify your repositories in any way
- The Google service account only has access to sheets you explicitly share with it
- No data is stored anywhere — the agent reads, processes, and writes in one run then exits

---

## File structure

```
effort-tracker-agent/
├── run_agent.py          ← entry point — run this
├── tools/
│   ├── github_tool.py    ← fetches PR and issue comments from GitHub
│   ├── parser.py         ← extracts hours from comments using Gemini AI
│   ├── aggregator.py     ← sums hours per engineer per repo
│   └── sheets_tool.py    ← rewrites the Google Sheet
├── requirements.txt      ← Python dependencies
├── .env                  ← credentials (never share this file)
├── credentials.json      ← Google service account key (never share this file)
└── .gitignore            ← ensures credentials stay private
```

---

## Handover notes

Built to automate the manual effort tracking process. The agent is fully self-contained — no database, no server, no ongoing maintenance required beyond renewing the GitHub token when it expires.

To point the agent at a different organisation or sheet in future, update `GITHUB_ORG` and `GOOGLE_SHEET_ID` in `.env` and share the new sheet with the service account email from `credentials.json`.