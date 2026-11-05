# Guardrails & Critical Rules

This file contains rules that apply across ALL tasks in the job search pipeline. Every task file references this document. These rules are non-negotiable.

---

## Pre-Authorized Pipeline Actions

The AI is pre-authorized to perform these actions without asking for confirmation each time:

- Reading any file in this project folder
- Writing or editing any file in this project folder (tracker.csv, JD files, materials, task files)
- Creating company subfolders under `Job_Applications/`
- Appending rows to `tracker.csv`
- Evaluating whether a job is a fit and updating its status accordingly
- Declining cookie banners, privacy popups, and notification prompts (always choose the most privacy-preserving option)

**Always require explicit confirmation for:**
- Submitting an application form (clicking Submit / Apply / Send). The AI stops before this step.
- Downloading any file
- Entering financial or identity information (the AI never enters bank, SSN, passport, ID numbers, or payment info)
- Creating new accounts (the AI never signs you up for anything)

---

## Absolute Rules

1. **NEVER fabricate or assume personal details.** All info comes from `profile.md`, `workHistory.md`, and `preferences.md`. If something isn't in those files, ASK the user.
2. **NEVER paste a resume body into a text field.** Always use PDF upload.
3. **NEVER leave placeholder fields** like `[Company Name]` or `[Insert Here]` in any final document.
4. **NEVER generate from memory, templates, or previously generated materials.** Every resume and cover letter starts from `workHistory.md` + the specific job description. Never reference, copy from, or base new materials on resumes or cover letters generated for other companies.
5. **All working files stay in the `Job_Applications/{CompanyName}/` folder.**
6. **Before generating a resume or cover letter,** read the job description first and ask about anything not in the source files.
7. **Every resume and cover letter must be unique** to the company and role — no copy-paste between applications.
8. **STOP before clicking Submit.** The user reviews and submits manually.
9. **Apply the location filter from `preferences.md`.** Disqualify roles that don't match the user's stated location/remote preferences.
10. **Apply the salary floor from `preferences.md`.** Disqualify roles clearly below the floor when the JD lists comp. Flag as `BORDERLINE FIT - HIGH COMP` if comp is at or above the high-comp threshold even when fit is otherwise borderline.

---

## Source Rules

- `profile.md`, `workHistory.md`, and `preferences.md` are the ONLY sources for generating materials and filling applications.
- NEVER fabricate, assume, or invent any detail. If it's not in those files, ASK.
- NEVER reference or copy from previously generated application materials.

---

## Tracker Rules

`Job_Applications/tracker.csv` is the single orchestration document. Every task reads it to know what to work on (filter by Status column) and updates it after completing work.

### Duplicate Company Rules
- **Same company + same role** → never add (true duplicate)
- **Same company already APPLIED / READY TO SUBMIT / INTERVIEW SCHEDULED** → skip
- **Same company + different role, not already applied** → OK to add

### CSV Column Mapping
```
Column 1:  Company             — Company name
Column 2:  Role                — Job title (NEVER overwrite with a status value)
Column 3:  Status              — Pipeline status (the ONLY column tasks update for status changes)
Column 4:  Platform            — Where the job was found (LinkedIn, Indeed, Greenhouse, etc.)
Column 5:  Date Applied        — Date the application was submitted
Column 6:  Tracking Status     — Response status (Confirmed / Rejected / Interview Scheduled [date]). "—" if no response.
Column 7:  URL                 — Direct link to the specific job posting or company careers page
Column 8:  Salary Range        — From the JD (e.g., "$150,000 - $180,000"). "—" if not listed.
Column 9:  Required Fit Match  — Required qualifications match % (e.g., "85%"). "—" until evaluated.
Column 10: Wanted Fit Match    — Preferred qualifications match % (e.g., "60%"). "—" until evaluated.
Column 11: Notes               — Free-text details, evaluation notes, context
```

**CRITICAL: When updating a row's status, ONLY change Column 3. NEVER overwrite Column 2 (Role).**

### Status Values
- **POTENTIAL** — Lead identified, needs JD download
- **JD DOWNLOADED** — Job description saved, needs fit evaluation
- **JD DOWNLOADED - GOOD FIT** — Passed qualification, ready for materials
- **JD DOWNLOADED - BORDERLINE FIT** — Borderline match, materials still generated
- **JD DOWNLOADED - BORDERLINE FIT - HIGH COMP** — Borderline but salary at/above high-comp threshold
- **MATERIALS READY** — Resume + cover letter generated, ready to apply
- **MATERIALS READY - BORDERLINE** — Materials done, user reviews fit before applying
- **READY TO SUBMIT** — Application 100% filled, tab open on Submit page
- **FORM IN PROGRESS** — Partially filled, notes describe what remains
- **NEEDS ACCOUNT** — Login/account creation required (user creates account)
- **APPLIED** — Submitted
- **REJECTED** — Rejection received
- **INTERVIEW SCHEDULED** — Interview confirmed
- **CLOSED** — Job no longer available
- **STALE** — Job older than 7 days when discovered
- **DISQUALIFIED** — Role doesn't meet criteria (location, comp, missing credentials, out-of-scope). Reason recorded in Notes.
- **MISSING JOB DESCRIPTION** — JD file missing, stub, or describes a different role. Delete the bad JD file before setting this status.
- **NEEDS INFO** — Missing information from the user

**Never write the bare status `BLOCKED`.** Always pick a descriptive replacement (DISQUALIFIED with reason, MISSING JOB DESCRIPTION, NEEDS INFO).

---

## URL Rules

Every URL written to the tracker's URL column must be a direct link to the specific job posting OR the company's own careers/ATS page.

### NEVER write these URL types
- Aggregator search URLs (`indeed.com/jobs?q=...`, `linkedin.com/jobs/search/?keywords=...`, `glassdoor.com/job-listing/...`)
- LinkedIn **company** page URLs (`linkedin.com/company/...`) — these aren't job postings
- Fabricated or guessed URLs
- Browser-internal error URLs (`chrome-error://`, `about:`, `data:`, `javascript:`)

### ALWAYS use these URL types
- Direct ATS URLs (Greenhouse, Lever, Ashby, Workday, Jobvite, iCIMS, SmartRecruiters, Eightfold)
- Company careers pages (`company.com/careers`) as a fallback
- LinkedIn direct job-view URLs (`linkedin.com/jobs/view/XXXXXXXXXX/`)

---

## File Management and Naming

### Folder Structure
```
ai-job-search-starter/
  Job_Applications/
    tracker.csv
    {CompanyName}/
      Job_Description_{CompanyName}.txt
      {LastName}_{FirstName}_Resume_{CompanyName}.docx
      {LastName}_{FirstName}_Resume_{CompanyName}.pdf
      {LastName}_{FirstName}_CoverLetter_{CompanyName}.docx
      {LastName}_{FirstName}_CoverLetter_{CompanyName}.pdf
```

### Naming Convention
- `{CompanyName}` uses PascalCase with no spaces: `ModusCreate`, `PennantServices`
- `{LastName}_{FirstName}` is pulled from `profile.md`
- Always create both `.docx` (source) and `.pdf` (for upload)

---

## DOCX Generation — Hard Rules

Some PDF converters (LibreOffice in particular) render docx floating elements twice, producing a duplicate-text bug. To avoid this:

- **NO TextBox / floating elements.** Never use `TextBox`, `FrameProperties`, `textWrapping`, or anchored drawing containers.
- **NO multi-column section layouts.** All content flows in a single column.
- **Use borderless `Table` for side-by-side layouts** instead of floating text boxes.
- **NO document headers that repeat resume content** (page-region headers must not contain name, title, or body content).

After converting `.docx` → `.pdf`, open the PDF and verify the first paragraph isn't duplicated. If the name appears twice on the same line, rebuild the DOCX using only Tables and inline Paragraphs.

---

## Skip Roles Older Than 7 Days

If a job posting is more than 7 days old, mark `STALE` and move on. Application timing matters; older postings have lower response rates.
