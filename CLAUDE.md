# AI Job Search Starter — Orchestration Guide

This is what the AI reads on every session start. It explains the pipeline, the files, and the rules.

## On Session Start

1. **Confirm folder access.** Request access to this folder if not already mounted.
2. **Check `profile.md` and `workHistory.md` for `[REPLACE]` placeholders.**
   - If placeholders still exist → recommend running the intake task (`intake.md`) before anything else. Stop here.
   - If everything's populated → continue.
3. **Read `Job_Applications/tracker.csv`** — the single orchestration document. Count rows by status and give the user a quick state-of-the-pipeline summary: how many `JD DOWNLOADED` rows waiting for evaluation, how many `MATERIALS READY` waiting for user review, how many recent `APPLIED` / `REJECTED` / `INTERVIEW SCHEDULED`.

## File Map

### Setup files (filled by the user / intake task)
- `profile.md` — Contact info, EEO answers, work authorization, salary expectations
- `workHistory.md` — Full career history, education, technical skills, differentiators
- `preferences.md` — Target roles, location, salary floor, hard disqualifiers (human-readable)
- `preferences.json` — Same data as preferences.md, machine-readable for `find_jobs.py`

### Reference files (read by every task)
- `guardrails.md` — Pipeline rules: tracker schema, status values, URL rules, DOCX rules, naming
- `writingStyle.md` — Banned AI phrases, tone rules, AI-detection avoidance

### Task files (one per pipeline step)
- `intake.md` — Interactive first-run profile builder
- `evaluate_and_generate.md` — Combined: fit scoring + resume + cover letter (one pass per job)
- `updater.md` — Check Gmail + LinkedIn for responses, update tracker statuses, add POTENTIAL leads

### Scripts
- `find_jobs.py` — Manual Google Jobs sweeper (run by the user, not by the AI)
- `scripts/sync_preferences.py` — Helper script for preferences.md ↔ preferences.json

### Tracker
- `Job_Applications/tracker.csv` — One row per job, status drives what each task works on
- `Job_Applications/{CompanyName}/` — Per-company folders with JD + resume + cover letter

## Pipeline Flow

```
intake.md (first run, once)
   ↓ writes profile.md, workHistory.md, preferences.md, preferences.json

find_jobs.py (manual)                     updater.md (run anytime)
   ↓ appends JD DOWNLOADED rows              ↓ checks Gmail + LinkedIn
                                             ↓ updates statuses, adds POTENTIAL leads

evaluate_and_generate.md
   For each JD DOWNLOADED row:
     1. Verify JD file matches the row (else MISSING JOB DESCRIPTION)
     2. Location + hard-credential gates
     3. Score Required + Preferred against workHistory.md
     4. Decide: GOOD FIT / BORDERLINE / BORDERLINE - HIGH COMP / DISQUALIFIED
     5. If passing: generate resume + cover letter, validate PDFs
     6. Set MATERIALS READY (or MATERIALS READY - BORDERLINE)

(User reviews materials and submits manually)
```

## Core Rules

- **Every task starts by reading `guardrails.md` and `writingStyle.md`.**
- **The tracker is the single orchestration document.** Each task reads it to know what to work on (filter by Status) and updates it after completing work.
- **Every resume and cover letter starts fresh from `workHistory.md` + the JD.** Never reference, copy from, or base new materials on resumes or cover letters generated for other companies.
- **Never fabricate anything.** All facts come from `profile.md`, `workHistory.md`, `preferences.md`. If a JD asks for something not in the source files, ASK the user — don't invent.
- **Single-column DOCX layouts only.** No TextBox, no floating elements, no multi-column sections (these cause the duplicate-text PDF bug). Use borderless Tables for any side-by-side effect.
- **STOP before clicking Submit.** The user always reviews and submits manually.
- **The AI never:**
  - Creates accounts
  - Enters financial information, SSN, passport, ID, or payment info
  - Downloads files without explicit user confirmation
  - Modifies sharing permissions

## Task Invocation

The user typically says things like:
- "Run intake" → `intake.md`
- "Score the new JDs and build materials" → `evaluate_and_generate.md`
- "Check my messages / update the tracker" → `updater.md`
- "Show me the tracker status" → read `tracker.csv` and summarize by status

The task files are written so an AI can extend the pipeline. If the user wants something new (automated form filling, scheduled runs, etc.), they can ask the AI to add a task following the same pattern.

## Status Values

See `guardrails.md` for the full list. Quick reference of the pipeline-active statuses:
- `JD DOWNLOADED` → waiting for `evaluate_and_generate.md`
- `JD DOWNLOADED - GOOD FIT` / `BORDERLINE FIT` / `BORDERLINE FIT - HIGH COMP` → ready for materials
- `MATERIALS READY` / `MATERIALS READY - BORDERLINE` → user reviews + submits
- `DISQUALIFIED` (with reason in Notes) — automated decision
- `MISSING JOB DESCRIPTION` — JD file was bad / mismatched; needs re-download
- `STALE` — posting older than 7 days

Never write the bare status `BLOCKED`. Use a descriptive replacement (`DISQUALIFIED` with reason, `MISSING JOB DESCRIPTION`, `NEEDS INFO`).
