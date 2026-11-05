# Evaluate & Generate — Fit Scoring + Resume + Cover Letter

## Purpose
For every job in `tracker.csv` with status **JD DOWNLOADED**: score the fit against `workHistory.md` and `preferences.md`, and — if the row is a GOOD FIT or BORDERLINE FIT — immediately generate a tailored resume and cover letter. One pass per job. Fit scoring and material generation run together so there's no waiting between steps.

## Files to Read
1. `guardrails.md` — Critical rules (read first)
2. `profile.md` — Name, contact info, EEO answers, work authorization
3. `workHistory.md` — Full career history (the source for all resume + cover letter content)
4. `preferences.md` — Target roles, salary floor, location, hard disqualifiers
5. `writingStyle.md` — Banned phrases, tone rules, AI-detection avoidance
6. `Job_Applications/tracker.csv` — Find all rows with status `JD DOWNLOADED`
7. For each row: `Job_Applications/{CompanyName}/Job_Description_{CompanyName}.txt`

## Files This Task Writes
- For each GOOD FIT / BORDERLINE FIT row:
  - `Job_Applications/{CompanyName}/{LastName}_{FirstName}_Resume_{CompanyName}.docx` + `.pdf`
  - `Job_Applications/{CompanyName}/{LastName}_{FirstName}_CoverLetter_{CompanyName}.docx` + `.pdf`
  - Appended `## FIT EVALUATION` block in the JD file
- Updated row in `tracker.csv` with new Status + Required/Wanted Fit Match %

---

## Scope — What This Task Does
- Picks up every tracker row with status **JD DOWNLOADED**
- Reads each JD file
- Scores fit against `workHistory.md` + `preferences.md`
- Updates status to GOOD FIT / BORDERLINE FIT / BORDERLINE FIT - HIGH COMP / DISQUALIFIED / MISSING JOB DESCRIPTION
- For GOOD FIT and BORDERLINE FIT: generates tailored resume + cover letter
- Updates the tracker status to MATERIALS READY / MATERIALS READY - BORDERLINE after materials are saved

## Scope — What This Task Does NOT Do
- Does NOT search for jobs (use `find_jobs.py`)
- Does NOT fill out application forms
- Does NOT click Submit on any application

---

## Combined Per-Row Process

For each row with status `JD DOWNLOADED`, run these steps in order:

### Step 1 — Verify the JD File Matches the Row

1. Read the tracker row's Company (Col 1) and Role (Col 2).
2. Read the JD file's header (first ~30 lines).
3. If the JD's company doesn't match the tracker's company, OR the JD's title obviously refers to a different role than the tracker's Role column:
   - Delete the wrong JD file (or rename to `_deleted_<date>_*.bak` if delete fails)
   - Set Status = **MISSING JOB DESCRIPTION**, Notes = `Wrong JD deleted (was: '<actual JD title>'); needs re-download`
   - Skip to next row
4. If the JD file is missing or fewer than ~1,500 characters of real content:
   - Delete the stub file
   - Set Status = **MISSING JOB DESCRIPTION**, Notes = `Stub JD deleted; needs re-download`
   - Skip to next row

### Step 2 — Location Check (Before Reading Full JD)
Apply the location filter from `preferences.md`:
- If `remote_ok = true` and the JD says fully remote / remote (US) / WFH → proceed
- If the role is in one of the user's `metro_cities` (or within the commute radius) → proceed
- Otherwise → Status = **DISQUALIFIED**, Notes = `Location: <city/state from JD> doesn't match preferences (remote_ok=<bool>, metro=<cities>)`. Move to next row.

### Step 3 — Hard Disqualifier Check
- Does the JD require a credential the user doesn't have (PhD, MD, JD, PE license, active security clearance — anything in `preferences.md`'s `hard_credentials_to_skip`)? If yes, and there's no "or equivalent experience" softener nearby → Status = **DISQUALIFIED**, Notes = `Missing required credential: <credential>`. Move on.
- Does the role match an `auto_skip_title_patterns` regex? → Status = **DISQUALIFIED**, Notes = `Title auto-skip: <pattern>`. Move on.

### Step 4 — Strip Prior Evaluations
If the JD file already has a `## FIT EVALUATION` block from a previous run, strip it before keyword counting. Otherwise your prior notes will inflate the score.

### Step 5 — Score the Fit

1. **List Required qualifications** from the JD (anything under "Required," "Must have," "Minimum qualifications," etc.). If not labeled, treat hard skills, years of experience, and credentials as Required.
2. **List Preferred qualifications** ("Preferred," "Nice to have," "Bonus").
3. For each Required item, check `workHistory.md`:
   - ✅ = Have it (cite the specific role/project from `workHistory.md`)
   - ⚠️ = Partial / transferable
   - ❌ = Don't have it
4. Same for Preferred.
5. Compute:
   - `Required match % = (✅ count) / (total Required) × 100`
   - `Preferred match % = (✅ count) / (total Preferred) × 100`

### Step 6 — Decide Status

Read these salary thresholds from `preferences.md`:
- `min_salary_usd` — anything clearly below this when comp is listed is auto-DQ
- `high_comp_threshold_usd` — at or above this, marginal fits get HIGH COMP flag

Decision rules:
- **Required ≥ 80% AND Preferred ≥ 50%** → Status = **JD DOWNLOADED - GOOD FIT**
- **Required 60–79% OR Preferred 30–49%, AND salary ≥ `high_comp_threshold_usd`** → Status = **JD DOWNLOADED - BORDERLINE FIT - HIGH COMP**
- **Required 60–79% OR Preferred 30–49%** → Status = **JD DOWNLOADED - BORDERLINE FIT**
- **Required < 60%** → Status = **DISQUALIFIED** with reason
- **Missing non-substitutable credential** → Status = **DISQUALIFIED**
- **Salary listed and below `min_salary_usd`** → Status = **DISQUALIFIED** with reason
- **Job posted > 7 days ago** → Status = **STALE**

### Step 7 — Write the Evidence Block to the JD File

Append this block to the JD file (`Job_Description_{CompanyName}.txt`). Every row that gets GOOD FIT / BORDERLINE / DISQUALIFIED needs this block populated:

```
## FIT EVALUATION
### JD ↔ Row Match
- Tracker Role: <Col 2 value>
- JD Title: <from JD header>
- Match: yes / no

### Location
- JD location: <signal>
- Preferences: remote_ok=<bool>, metro_cities=<list>
- Decision: pass / fail (with reason)

### Required Qualifications
- "<quoted Required item ≤15 words>" — ✅/⚠️/❌ — <workHistory.md citation or gap>
- (repeat for every Required item)

### Preferred Qualifications
- "<quoted Preferred item>" — ✅/⚠️/❌ — <citation or gap>

### Match Math
- Required: X / Y = NN%
- Preferred: X / Y = NN%

### Recommendation
- Status: <STATUS>
- One-sentence reason

### Key Strengths for This Role
- 2–4 bullets from workHistory.md

### Key Gaps
- 0–4 bullets, plain English
```

### Step 8 — Update the Tracker

Update ONLY Column 3 (Status), Column 9 (Required Fit Match), Column 10 (Wanted Fit Match), and Column 11 (Notes). NEVER overwrite Column 2 (Role).

- Required Fit Match = `NN%`
- Wanted Fit Match = `NN%`
- Notes = short summary (1-2 sentences)
- If Salary Range (Col 8) was `—` and the JD lists comp explicitly, fill it in. Don't guess.

### Step 9 — If GOOD FIT / BORDERLINE FIT / BORDERLINE FIT - HIGH COMP, Generate Materials

Skip this step for DISQUALIFIED / MISSING JOB DESCRIPTION / STALE.

#### 9a — Resume

Generate a tailored resume from `workHistory.md` + the JD.

**Tailoring process** (do this every time, fresh from `workHistory.md`):
1. Read the JD carefully. Identify the 5-7 most important keywords.
2. Map every Required and Preferred qualification to a specific role / project / metric in `workHistory.md`. Pull from ALL roles, not just the most recent.
3. Write the Professional Summary in 3–5 sentences, third person. Open with a positioning statement: category of leader, depth, what makes the user distinctly valuable for THIS role. Mirror the JD's exact tool / platform names. End with a sentence that connects the user to this company's specific challenge.
4. Write each role's scope paragraph to emphasize the angle most relevant to THIS JD. Same facts, different emphasis. Never copy-paste a scope paragraph from a prior resume.
5. Write bullets that directly address JD requirements. Every bullet must connect to something the JD asks for. Vary bullet length intentionally — short and long mixed.
6. Use the user's exact tool names from `workHistory.md`; use the JD's exact terminology where it differs from generic versions.
7. For BORDERLINE roles: identify the gap, find the closest proxy experience, and lead with it. Don't hide the gap, but don't call it out either.
8. **If a JD requirement has no match in `workHistory.md`,** do NOT invent or stretch. Flag it: "The JD requires X. I don't see a direct match. Closest proxy is Y — proceed with proxy, or should I ask?"

**Length:**
- Target **2 full pages.** If the draft is short, expand using JD-relevant content from `workHistory.md`. Don't pad with generic filler.
- 3 pages only when the seniority / technical depth genuinely warrants it. Never exceed 3 pages.

**Structure (in order):**
1. Header — Name (from `profile.md`), target job title, contact line
2. Professional Summary — 3-5 sentences, third person
3. Professional Experience — most relevant role first (default reverse-chronological, but relevance beats recency)
4. Education

**Anti-patterns to avoid** — see `writingStyle.md` for the full banned list. Quick reminder: no "results-driven," no "leveraged," no "spearheaded," no "passionate about," no generic openers, no first-person summary.

**Formatting (DOCX):**
- Arial throughout
- Body 10pt, color `#1A1A2E` (deep navy, not pure black)
- Accent blue `#2563EB` for the target title line, section divider rules, and company names in role headers
- Medium gray `#6B7280` for contact line, locations, dates
- Single-column layout — NEVER use `TextBox`, floating elements, or multi-column section. Use borderless `Table` for any side-by-side effect (see `guardrails.md` DOCX rules).
- Italic scope paragraph after every role title
- Tab stop at `pos=9360` for right-aligned dates (US Letter width)
- Margins: top/bottom 0.5", left/right 0.75"

**Filename:** `{LastName}_{FirstName}_Resume_{CompanyName}.docx` and `.pdf`, saved to `Job_Applications/{CompanyName}/`.

#### 9b — Cover Letter

Generate a tailored cover letter from `workHistory.md` + the JD.

**Hard constraints:**
- **250 words max** in the body. Count them.
- **3 paragraphs only.** No headers, no bullets, no lists inside the body.
- **Zero dashes of any kind.** No em dashes, no hyphens as pauses. If you'd use a dash, rewrite.
- **Never open with "I"** as the first word. Never open by naming the company or job title.
- **Use contractions throughout:** I've, I'm, that's, it's, they're.
- **Vary sentence length deliberately** — mix 5-word sentences with 20-word ones.
- **Start at least one sentence with "And" or "But"** for natural rhythm.
- **Use the company name no more than once** in the body.
- **Include ONE specific micro-story** from `workHistory.md` — a real project, a turning point, a specific decision. Something only the user would know.
- **Anchor every claim to a specific number** from `workHistory.md`. No invented metrics.
- **Mirror one piece of JD language** naturally.
- **End with a confident, direct next step.** No "thank you for your time," no "I look forward to hearing from you."

**Structure:**
- Header (name, contact line, blue accent rule under contact — matches resume header)
- Date
- Hiring Manager
- Company Name
- Re: <exact job title>
- 3 body paragraphs:
  - Paragraph 1: direct statement of specific value, or sharp observation connecting the user's experience to the company's problem
  - Paragraph 2: evidence anchored to specific numbers from `workHistory.md`, includes the micro-story
  - Paragraph 3: bridge and close — "Why this role?" + "Why me?" implicit answers, confident next step
- Sincerely, {Full Name}

**Formatting (DOCX):**
- Arial 11pt, color `#1A1A2E`
- 1-inch margins all around
- Same single-column / no-TextBox / no-multi-column rules as the resume
- Header block (name + contact line) styled identically to the resume header for visual consistency

**Filename:** `{LastName}_{FirstName}_CoverLetter_{CompanyName}.docx` and `.pdf`, saved to `Job_Applications/{CompanyName}/`.

**Post-generation flagging:**
After writing, save a `CoverLetter_Notes_{CompanyName}.txt` in the same folder containing:
1. Any assumption made about the user's experience that they should verify
2. The 3 sentences most at risk of sounding AI-written (so the user can hand-rewrite them in their own voice)

### Step 10 — Convert DOCX → PDF and Validate

For both resume and cover letter:
1. Convert `.docx` → `.pdf` (LibreOffice in headless mode works in sandboxed environments).
2. Open the PDF and verify:
   - No duplicate text side-by-side (the floating-element bug — if it appears, rebuild using Tables only and re-convert)
   - Colors render correctly (blue accent line, navy text, gray contact line)
   - Dates stay right-aligned, no content cut off at margins
   - The cover letter PDF has no placeholders left ([Company Name], [Date], [Job Title])

If anything fails, fix it in the `.docx` and reconvert before continuing.

### Step 11 — Final Tracker Update

After BOTH the resume and cover letter PDFs pass validation, update the tracker:
- If status was GOOD FIT → set Status = **MATERIALS READY**
- If status was BORDERLINE FIT → set Status = **MATERIALS READY - BORDERLINE**
- If status was BORDERLINE FIT - HIGH COMP → set Status = **MATERIALS READY - BORDERLINE** (user reviews fit + comp before deciding to apply)

NEVER mark `MATERIALS READY` if either file failed validation. Leave the status at GOOD FIT / BORDERLINE and note the failure in the Notes column.

---

## Output Summary
At the end of the run, present the user with:
- Count of rows processed
- Count by new status: GOOD FIT, BORDERLINE FIT, BORDERLINE - HIGH COMP, DISQUALIFIED, MISSING JOB DESCRIPTION, STALE
- Count of resume + cover letter pairs generated
- Any rows that need user attention (NEEDS INFO, flagged assumptions, validation failures)

---

## Notes
- This task replaces the separate "evaluate fit" and "generate materials" steps. They're combined here so each job gets evaluated and (if it passes) tailored in one pass.
- Every resume and cover letter is fresh from `workHistory.md` + the JD. NEVER reuse content across companies.
- If `workHistory.md` is missing details a strong resume needs, pause and ask the user before generating.
