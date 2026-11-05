# AI Job Search Pipeline — Onboarding Guide

Welcome. This is an AI-powered job search pipeline that automates the tedious parts: finding relevant job postings, scoring your fit, and generating tailored resumes and cover letters — all driven by a single tracker CSV.

This guide helps your AI assistant (Claude, Cursor, etc.) walk you through setup. If you're using Claude Cowork or Claude Code, share this folder and say **"Run the intake task"** to get started. The AI will read this guide and walk you through the rest.

---

## What This Pipeline Does

| Step | How it runs | What it produces |
|------|-------------|-----------------|
| **Intake** | AI-guided, one time | Populates your profile, work history, and preferences |
| **Find jobs** | `python find_jobs.py` (you run it) | Appends new JD rows to the tracker |
| **Evaluate + generate** | Ask your AI | Scores fit, writes resume + cover letter for each match |
| **Update tracker** | Ask your AI | Checks Gmail + LinkedIn, updates statuses, surfaces leads |

---

## Step 1: Intake (First Run Only)

Before anything else, your AI needs to know about you. The intake task walks you through three options:

1. **Upload a resume** — drop your existing resume PDF or DOCX in this folder. The AI parses it and fills in the templates, then asks follow-up questions for anything missing.
2. **Answer questions** — the AI asks batch by batch (contact info, work history, job targets, etc.).
3. **Fill templates by hand** — edit `profile.md`, `workHistory.md`, and `preferences.md` directly, then ask the AI to verify.

By the end of intake, these four files will be populated:

- `profile.md` — your name, contact, EEO answers, work auth, salary expectations
- `workHistory.md` — your complete career history with metrics, projects, differentiators
- `preferences.md` — target job titles, location rules, salary floor, hard disqualifiers
- `preferences.json` — machine-readable mirror of preferences.md for `find_jobs.py`

**To start intake**, open this folder in your AI and say: `"Run the intake task."`

---

## Step 2: Install Dependencies

`find_jobs.py` uses Playwright to scrape Google Jobs. Install it once:

```bash
pip install playwright
playwright install chromium
```

---

## Step 3: Find Jobs

Run the script manually whenever you want a fresh batch of postings:

```bash
python find_jobs.py --smoke-test   # one query, sanity check (run this first)
python find_jobs.py                 # full sweep of all your target titles
```

A headed Chromium browser opens. If Google shows a captcha, solve it in the window — the script polls every 5 seconds and resumes automatically.

New rows land in `Job_Applications/tracker.csv` with status `JD DOWNLOADED` (or `DISQUALIFIED` if they fail the pre-filter: wrong location, below salary floor, hard-credential gate, or no relevant skill keywords).

---

## Step 4: Score Fit + Generate Materials

Ask your AI:

> "Run evaluate_and_generate."

For every `JD DOWNLOADED` row, the task:

1. Verifies the JD file matches the tracker row
2. Re-checks location and hard-credential gates against `preferences.md`
3. Scores Required and Preferred qualifications against `workHistory.md`
4. Appends a `## FIT EVALUATION` block to the JD file with the full evidence trail
5. Updates the row's Status, fit %, salary, and notes in `tracker.csv`
6. **For GOOD FIT or BORDERLINE FIT rows:** generates a tailored resume + cover letter, validates the PDFs, and flips the status to `MATERIALS READY`

Everything is generated fresh from `workHistory.md` + the JD. Nothing is copy-pasted between applications.

---

## Step 5: Review and Submit

Open `Job_Applications/{CompanyName}/`. You'll find:

- `{LastName}_{FirstName}_Resume_{CompanyName}.pdf`
- `{LastName}_{FirstName}_CoverLetter_{CompanyName}.pdf`
- `CoverLetter_Notes_{CompanyName}.txt` — flags any assumptions the AI made and the 3 sentences most at risk of sounding AI-generated

Review both documents. The AI never clicks Submit — that step is always yours.

---

## Step 6: Check Messages + Update Tracker (Optional but Useful)

Ask your AI:

> "Run the updater."

The updater opens Gmail and LinkedIn, scans for responses since the last run, and updates your tracker automatically:

- Confirmation emails → marks APPLIED rows as Confirmed
- Rejection emails → flips status to REJECTED with details
- Interview invites → flips status to INTERVIEW SCHEDULED with date/time
- Recruiter outreach + job alert leads → adds POTENTIAL rows for future evaluation

Requires Chrome browser access (Claude in Chrome connector, or equivalent).

---

## How the Tracker Works

`Job_Applications/tracker.csv` is the single orchestration document. Every task reads it to know what to work on and writes back when it's done.

| Status | Meaning |
|--------|---------|
| `JD DOWNLOADED` | Waiting for fit evaluation |
| `MATERIALS READY` | Resume + cover letter done, ready to apply |
| `MATERIALS READY - BORDERLINE` | Materials done, review fit before applying |
| `APPLIED` | You submitted the application |
| `REJECTED` | Rejection received |
| `INTERVIEW SCHEDULED` | Interview confirmed |
| `DISQUALIFIED` | Failed auto-filters (reason in Notes) |
| `POTENTIAL` | Lead from Gmail / LinkedIn alerts — needs JD download |

Full status list in `guardrails.md`.

---

## Key Rules (Non-Negotiable)

- **Nothing is fabricated.** Every resume claim comes from `workHistory.md`. If the JD requires something not in your history, the AI asks you rather than inventing.
- **Every resume and cover letter is fresh** from `workHistory.md` + the JD. Never reused across applications.
- **Single-column DOCX layouts only.** TextBox and multi-column sections cause a duplicate-text bug in LibreOffice's PDF converter.
- **The AI stops before Submit.** You review and click Submit yourself.
- **No financial info, no IDs, no passwords, no account creation.** The AI declines these even if asked.

---

## Asking Your AI to Extend the Pipeline

The task files are written so an AI can add new steps by following the same pattern. If you want something the starter doesn't include — scheduled runs, automated form filling, ATS API integration — tell your AI: "Read `intake.md` and `evaluate_and_generate.md` as examples, then build a new task for [X]."

---

## Troubleshooting

**`find_jobs.py` says "preferences.json still has REPLACE placeholders"**
→ Run the intake task first, or edit `preferences.json` directly.

**Resume PDF has duplicate text side-by-side**
→ The DOCX was generated with a floating TextBox. See `guardrails.md` § DOCX Generation. Rebuild using only Tables and inline Paragraphs.

**JD file describes a different role than the tracker row**
→ `evaluate_and_generate.md` Step 1 detects this, deletes the wrong JD, and marks the row `MISSING JOB DESCRIPTION`. Re-run `find_jobs.py` or grab the JD manually.

**AI keeps using "leveraged" / "spearheaded" / "results-driven"**
→ Add the offending phrase to the banned list in `writingStyle.md` and re-run.

**The updater says it can't find Chrome or browser access**
→ Make sure your Chrome connector is connected. If you're not using a browser-connected AI tool, run the updater step manually: check your email and LinkedIn yourself, then tell the AI what you found so it can update the tracker.
