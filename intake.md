# Intake — First-Run Profile Builder

## Purpose
Walk the user through populating `profile.md`, `workHistory.md`, `preferences.md`, and `preferences.json` so the rest of the pipeline (`find_jobs.py`, `evaluate_and_generate.md`) has everything it needs.

Run this once before any other task. If the user has already filled in the templates manually, skip to verification.

## Files This Task Writes
- `profile.md`
- `workHistory.md`
- `preferences.md`
- `preferences.json`

## Files This Task Reads
- `guardrails.md` (read first — applies to every task)
- Any resume file the user uploads (PDF or DOCX in the project folder)

---

## Step-by-Step Flow

### Step 1: Check if Setup is Already Done
Check whether `profile.md` and `workHistory.md` still contain `[REPLACE` placeholders.

- **All placeholders gone** → Skip to Step 7 (verification).
- **Some or all placeholders present** → Continue to Step 2.

### Step 2: Greet and Ask How They Want to Provide Info
Use the AskUserQuestion tool with these options:

> "How would you like to set up your profile?"
> - **Upload a resume** — Drop a resume PDF/DOCX in the folder and I'll parse it and ask follow-ups for anything missing
> - **Answer questions** — I'll ask you about each section one piece at a time
> - **Already filled in the templates** — Skip to verification

### Step 3: Resume-Upload Path
If they chose to upload a resume:
1. Ask them to drop the resume in the project folder (or confirm the path).
2. Read the resume file (PDF via `pdftotext` or DOCX via Python `python-docx`).
3. Extract everything you can into a working draft of `profile.md` and `workHistory.md`.
4. Identify what's missing or ambiguous (e.g., EEO answers, current employment status, work authorization, salary expectations, target titles).
5. Ask the user — one focused batch at a time, using AskUserQuestion where multiple choice fits — to fill the gaps.
6. Move to Step 5.

### Step 4: Q&A Path
If they chose the interactive path, walk them through these sections in order, grouping related questions together:

**Batch 1 — Contact & Authorization**
- Full name
- Email
- Phone
- City + state/country
- LinkedIn URL
- Country of work authorization
- Visa sponsorship needed?

**Batch 2 — EEO (optional, can answer "prefer not to say")**
- Gender
- Race/ethnicity
- Veteran status
- Disability status

**Batch 3 — Compensation & Timing**
- Target salary or range
- Minimum acceptable salary
- Currently employed? Available start date?
- Open to equity / commission?

**Batch 4 — Job Targets**
- 3-10 exact job titles they want to be matched against
- Any boolean queries they want included (optional)
- Industries to target, industries to avoid
- Hard disqualifiers (PhD-only roles, security clearance, etc.)

**Batch 5 — Location**
- Primary city/state
- Open to remote? Open to hybrid? Maximum commute radius
- Other acceptable metros

**Batch 6 — Work History (do this last; it's the longest)**
- For each role going back ~10-15 years:
  - Title, company, dates, location
  - 2-4 sentence scope paragraph
  - 4-8 key accomplishments with specific metrics
  - Notable projects
- Education (degrees, schools, years, honors)
- 3-7 differentiators (headline-worthy facts with numbers)

Save progress after each batch — don't wait until the end. If the user steps away mid-intake, they can resume.

### Step 5: Write the Files
Once the data is gathered:
1. Write `profile.md` — fill in every `[REPLACE]` placeholder.
2. Write `workHistory.md` — full role-by-role build, written in the format the template specifies.
3. Write `preferences.md` — target roles, location rules, salary, hard disqualifiers, soft preferences.
4. Write `preferences.json` — machine-readable mirror of `preferences.md` for `find_jobs.py`. Use the existing keys (`target_titles`, `boolean_queries`, `location`, `compensation`, `skill_keywords`, `hard_credentials_to_skip`, `auto_skip_title_patterns`).

### Step 6: Confirm with the User
Show the user the populated files and ask:

> "I've drafted your profile, work history, and preferences. Want me to: (a) walk through each file with you so you can edit anything, or (b) you'll review them yourself when you have time?"

### Step 7: Verification
Run these checks and report results:
- Does `profile.md` still contain any `[REPLACE]` text? If yes, list which fields.
- Does `workHistory.md` still contain any `[REPLACE]` or `[REPLACE WITH YOUR SUMMARY]` text? If yes, list which sections.
- Does `preferences.json` have at least 3 target titles, a location, a min salary, and at least 5 skill keywords?
- Does `preferences.md` and `preferences.json` agree (same titles, same salary floor, same location)?

If any check fails, ask the user to fix the gap before proceeding to job search.

### Step 8: Next Step
Once setup is complete, tell the user:

> "You're ready. Next, run `python find_jobs.py --smoke-test` to make sure job search works, then run `python find_jobs.py` for a full sweep. After it finishes, I'll run `evaluate_and_generate.md` to score the new jobs and build resumes + cover letters for the good fits."

---

## Notes
- This task uses **only** information the user provides directly. Never fabricate work history, employers, projects, or metrics.
- If the user says "I don't remember the exact number," ask if they want to leave it blank or use a range. Don't invent.
- Save partial progress after each batch so a long intake can be paused and resumed.
