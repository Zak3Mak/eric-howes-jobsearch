# Eric Howes: Job Search (private)

This repo holds Eric's job search pipeline: profile, work history, preferences, and a tracker. Everything here is generated from his own materials. Nothing is submitted without Eric reviewing it.

## Status (Nov 2026)
- `profile.md`, `workHistory.md`, `preferences.md`, `preferences.json`: filled in.
- `references.md`: private reference contacts (local only, gitignored).
- Open items to settle before any resume is generated are listed at the bottom of `workHistory.md`.

## Run it
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install playwright
python find_jobs.py --smoke-test   # one query; solve any captcha in the browser window
python find_jobs.py                # full sweep
```
Then ask Claude: "Run evaluate_and_generate." It scores each posting and drafts a tailored resume and cover letter. Eric reviews and submits manually.

## Rules (see guardrails.md)
- Claims come only from `workHistory.md`; hedged wording stays hedged.
- No sales-rep, door-to-door, or commission-based roles. Utah County or fully remote. $80,000 minimum.
- Eric's current employer is Vivint and the search is confidential: do not contact Vivint references or apply through Vivint-linked channels without his OK.
