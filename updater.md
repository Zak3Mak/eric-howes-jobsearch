# Updater — Check Messages & Update Tracker

## Purpose
Check Gmail and LinkedIn for job search responses, then update the tracker with status changes and new leads.

## Files to Read
1. **guardrails.md** — Critical rules (read first)
2. **profile.md** — For reference when interpreting messages
3. **Job_Applications/tracker.csv** — Current application statuses

## Scope — What This Task Does
- Checks Gmail for: confirmation emails, rejection emails, interview invites, recruiter outreach
- Checks LinkedIn for: messages, notifications, job alerts, recruiter InMails
- Updates tracker.csv statuses based on findings (e.g., APPLIED → REJECTED, adds interview details)
- Adds new job leads from alerts/recruiters/messages to the tracker with status **POTENTIAL**
- Presents a status briefing when complete

## Scope — What This Task Does NOT Do
- Does NOT search for jobs on job boards
- Does NOT evaluate fit or qualification
- Does NOT generate resumes or cover letters
- Does NOT fill out application forms

## Step-by-Step Process

### Step 1: Read the Tracker
- Read `Job_Applications/tracker.csv`
- Note all current statuses to know what to look for

### Step 2: Check Gmail
Open Gmail in Chrome and search for job-related emails since the last run. Look for:

- **Confirmation emails** → Update Tracking Status (column 6) to "Confirmed". Update Status (column 3) to APPLIED if not already.
- **Rejection emails** → Update Tracking Status (column 6) to "Rejected". Update Status (column 3) to REJECTED. Add rejection details to Notes (column 11).
- **Interview invites** → Update Tracking Status (column 6) to "Interview Scheduled [date/time]" (include the actual date and time from the email). Update Status (column 3) to INTERVIEW SCHEDULED. Add interview details (format, contact, link) to Notes (column 11).
- **Recruiter outreach** → Add new row with Status RECRUITER OUTREACH
- **Job alert emails** → Add new rows with Status POTENTIAL

### Step 3: Check LinkedIn
Open LinkedIn in Chrome and check:

- **Messages/InMails** — Recruiter outreach, interview scheduling. Update Tracking Status (column 6) the same way as Gmail.
- **Notifications** — Application updates, profile views by recruiters. If a notification confirms receipt, set Tracking Status to "Confirmed".
- **Job Alerts** — New job recommendations matching saved searches
- For each new lead found: add to tracker with status **POTENTIAL** and source info in Notes (column 11)

### Step 4: Update tracker.csv
For each status change, update the row in tracker.csv:
- **Column 3 (Status)** — Pipeline status update (APPLIED, REJECTED, INTERVIEW SCHEDULED, etc.)
- **Column 6 (Tracking Status)** — Response tracking: "Confirmed", "Rejected", or "Interview Scheduled [date/time]"
- **Column 11 (Notes)** — Add details about the response (rejection reason, interview format/link, etc.)
- **CRITICAL: NEVER overwrite Column 2 (Role) with a status value.**

For each new lead, append a new row with the 11 columns in order:
- Company name (column 1)
- Role title if known (column 2)
- Status: POTENTIAL (column 3)
- Platform: where it was found (column 4)
- Date Applied: leave blank (column 5)
- Tracking Status: "—" (column 6)
- URL: if available (column 7)
- Salary Range: "—" (column 8)
- Required Fit Match: "—" (column 9)
- Wanted Fit Match: "—" (column 10)
- Notes: source details, alert type, any relevant context (column 11)

### Step 5: Present Status Briefing
After all updates, present a summary:
1. How many applications are currently out (APPLIED status count)
2. Any new rejections
3. Any interview invites or scheduled interviews
4. Any recruiter outreach
5. New POTENTIAL leads added
6. Any action items you need to handle manually

## Output
- Updated tracker.csv with all status changes and new leads
- Status briefing presented in chat

## Notes
- This task requires Chrome browser access. Make sure your Chrome connector is connected before running.
- You can run this task whenever you want a status check — it's read-heavy and only writes changes it actually finds.
- If your email or LinkedIn isn't connected via a browser, run this manually instead: open Gmail and LinkedIn yourself, then tell the AI what you found so it can update the tracker.
