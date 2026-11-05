# AI Job Search Starter

A minimal, AI-powered job search pipeline. Find roles, score fit, and generate tailored resumes + cover letters — all driven by a single tracker CSV.

## What's in the box

| File | What it is |
|---|---|
| `CLAUDE.md` | Orchestration guide the AI reads on every session start |
| `intake.md` | Interactive first-run task — builds your profile from a resume or Q&A |
| `find_jobs.py` | Manual job-discovery script (Google Jobs sweep) |
| `evaluate_and_generate.md` | Single combined task — scores fit AND writes resume + cover letter |
| `updater.md` | Check Gmail + LinkedIn for responses, update tracker, surface new leads |
| `guardrails.md` | Pipeline rules (tracker schema, URL rules, DOCX hard rules, status values) |
| `writingStyle.md` | Banned AI phrases, tone rules, AI-detection avoidance |
| `profile.md` | Your contact info, EEO answers, work auth (filled by intake) |
| `workHistory.md` | Your career history — the ONLY source for resume/cover letter content |
| `preferences.md` | Target roles, location, salary floor, hard disqualifiers (human-readable) |
| `preferences.json` | Same data as preferences.md, but machine-readable for find_jobs.py |
| `Job_Applications/tracker.csv` | The orchestration document — one row per job |
| `scripts/sync_preferences.py` | Helper to refresh preferences.json after editing preferences.md |

## Setup (one time)

### 1. Install dependencies

```bash
pip install playwright
playwright install chromium
```

### 2. Run intake

Open this folder in your AI assistant of choice (Cowork, Claude Code, Cursor, etc.) and say:

> "Run the intake task."

The AI will read `intake.md` and walk you through one of:
- Uploading a resume PDF/DOCX, parsing it, and filling the templates for you
- Answering questions interactively (batch by batch)
- Skipping straight to verification if you've already filled the templates by hand

By the end, these files will be populated:
- `profile.md` — your name, contact, EEO, work auth, salary expectations
- `workHistory.md` — your full career history with metrics, projects, and differentiators
- `preferences.md` and `preferences.json` — target titles, location, salary floor, hard skips

### 3. Verify

The intake task ends with a verification step. If anything still says `[REPLACE]`, fix it before moving on.

## Daily usage

### Find new jobs

```bash
python find_jobs.py --smoke-test    # one query, sanity check
python find_jobs.py                 # full sweep
```

Headed Chromium opens. If Google shows a captcha, solve it in the browser window and the script resumes automatically. New rows get appended to `tracker.csv` with status `JD DOWNLOADED` (or `DISQUALIFIED` if they fail the conservative pre-filter — location, salary floor, hard-credential gate, or no relevant skill keywords).

### Score fit + generate materials

Ask your AI:

> "Run evaluate_and_generate."

For every `JD DOWNLOADED` row, the task:
1. Verifies the JD file matches the row (deletes mis-matched JDs and flags the row for re-download)
2. Re-checks the location and hard-credential gates against `preferences.md`
3. Scores Required and Preferred qualifications against `workHistory.md`
4. Appends a `## FIT EVALUATION` block to the JD file
5. Updates the row's Status, Required/Wanted Fit %, Salary, and Notes
6. **If GOOD FIT or BORDERLINE FIT:** generates a tailored resume and cover letter, validates them, and flips the status to `MATERIALS READY` (or `MATERIALS READY - BORDERLINE`)

Fit scoring and material generation run together — one pass per job. Everything fresh from `workHistory.md` + the JD. Never copy-paste between applications.

### Review and submit

Open the company folder under `Job_Applications/{CompanyName}/`. Review the resume PDF and cover letter PDF. The AI never clicks Submit — that step is always yours.

## Pipeline at a glance

```
intake.md (first run)
   ↓ writes
profile.md, workHistory.md, preferences.md, preferences.json
   ↓ feeds
find_jobs.py  →  Job_Applications/tracker.csv (status: JD DOWNLOADED)
   ↓ feeds
evaluate_and_generate.md
   ├─ GOOD FIT / BORDERLINE      →  Resume + Cover Letter  →  MATERIALS READY
   ├─ BORDERLINE - HIGH COMP     →  Resume + Cover Letter  →  MATERIALS READY - BORDERLINE
   ├─ DISQUALIFIED                →  Reason in Notes
   └─ MISSING JOB DESCRIPTION    →  Delete bad JD, needs re-download
```

## Hard rules (from `guardrails.md`)

- **Never fabricate** anything. All resume + cover letter content comes from `workHistory.md`. If a JD requires something not in `workHistory.md`, the AI asks rather than invents.
- **Every resume and cover letter is fresh** from `workHistory.md` + the JD. Never copy-paste between applications.
- **Single-column DOCX layouts only.** No TextBox, no floating elements, no multi-column sections — these cause a duplicate-text bug in LibreOffice's PDF converter. Use borderless Tables for any side-by-side layout.
- **The AI stops before Submit.** You review every application before sending.
- **No financial info, no IDs, no passwords, no account creation.** The AI declines to enter those even if asked.

### Check your messages

Ask your AI:

> "Run the updater."

The task opens Gmail and LinkedIn in Chrome, scans for responses since the last run, updates tracker statuses (rejections, interview invites, confirmations), and surfaces any new leads as POTENTIAL rows. Requires Chrome browser access — if you're using Cowork or a browser-connected AI, it works out of the box.

## What this starter does NOT include

This is a basic version. It deliberately leaves out:
- ATS API direct integration (Greenhouse, Lever, Workday APIs)
- LinkedIn searches (requires login state — the updater scans messages but doesn't search job listings)
- Automated application form filling (only resume + cover letter generation)
- Scheduled runs (run scripts and tasks manually for now)

If you want any of those, the task files are written so an AI can extend them. Start with `intake.md` and `evaluate_and_generate.md` as the template.

## Troubleshooting

**`find_jobs.py` says "preferences.json still has REPLACE placeholders":**
Run the intake task first, or edit `preferences.json` by hand.

**Resume PDF has duplicate text side-by-side:**
The DOCX was generated with a floating TextBox or multi-column layout. See `guardrails.md` § DOCX Generation — Hard Rules. Rebuild using only Tables and inline Paragraphs.

**JD file describes a different role than the tracker row:**
The AI will detect this in `evaluate_and_generate.md` Step 1, delete the wrong JD, and mark the row `MISSING JOB DESCRIPTION`. Re-run `find_jobs.py` (or grab the JD manually).

**AI keeps using "leveraged" / "spearheaded" / "results-driven":**
Open `writingStyle.md`, add the offending phrase to the banned list if it's missing, and re-run.
