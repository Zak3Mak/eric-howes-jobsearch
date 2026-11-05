#!/usr/bin/env python3
"""
find_jobs.py — Google Jobs sweeper (basic / starter version).

Reads target titles, location, salary floor, and skill keywords from
`preferences.json`. For each title, runs a Google Jobs search, scrolls the
results to load the full set, extracts each JD, runs a conservative
qualification pre-filter, and appends rows to `Job_Applications/tracker.csv`
with status `JD DOWNLOADED` (or `DISQUALIFIED` if the pre-filter rejects).

Usage:
  python find_jobs.py                 # full sweep
  python find_jobs.py --smoke-test    # one query, fast sanity check
  python find_jobs.py --no-headed     # headless (captchas will block)

Captcha handling: headed Chromium opens. If Google shows a captcha, solve it
in the window — the script polls every 5 seconds and resumes automatically.

Artifacts:
  Job_Applications/{Company}/Job_Description_{Company}.txt
  Job_Applications/tracker.csv
  find_jobs_log_{YYYY-MM-DD}.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout, Error as PWError

# UTF-8 console output (Windows defaults to cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BASE_DIR = Path(__file__).resolve().parent
JOBS_DIR = BASE_DIR / "Job_Applications"
TRACKER_CSV = JOBS_DIR / "tracker.csv"
PREFERENCES_JSON = BASE_DIR / "preferences.json"
TODAY = date.today()


# ---------- preferences ----------

def load_preferences() -> dict:
    if not PREFERENCES_JSON.exists():
        sys.exit(
            f"ERROR: {PREFERENCES_JSON} not found. Run the intake task or fill in "
            "preferences.md and run scripts/sync_preferences.py first."
        )
    with open(PREFERENCES_JSON, encoding="utf-8") as f:
        prefs = json.load(f)

    required_keys = ["target_titles", "location", "compensation", "skill_keywords"]
    missing = [k for k in required_keys if k not in prefs]
    if missing:
        sys.exit(f"ERROR: preferences.json missing required keys: {missing}")

    # Sanity-check that placeholders have been replaced
    placeholders = [
        t for t in prefs.get("target_titles", [])
        if "REPLACE" in str(t).upper()
    ]
    if placeholders:
        sys.exit(
            "ERROR: preferences.json still has REPLACE placeholders in target_titles. "
            "Run the intake task or fill in preferences.md first."
        )

    return prefs


# ---------- helpers ----------

def pascal_company(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip()
    parts = cleaned.split()
    if not parts:
        return "Unknown"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def load_tracker():
    if not TRACKER_CSV.exists():
        sys.exit(f"ERROR: tracker.csv not found at {TRACKER_CSV}")
    with open(TRACKER_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    for r in rows:
        for k in fieldnames:
            if r.get(k) is None:
                r[k] = ""

    def is_real(r):
        return bool((r.get("Company") or "").strip()) and bool((r.get("Role") or "").strip())

    skip_statuses = {
        "APPLIED", "READY TO SUBMIT", "FORM IN PROGRESS",
        "INTERVIEW SCHEDULED", "RECRUITER OUTREACH",
    }
    existing = {(r["Company"].strip().lower(), r["Role"].strip().lower())
                for r in rows if is_real(r)}
    skip_companies = {r["Company"].strip().lower() for r in rows
                      if is_real(r) and r.get("Status", "").strip().upper() in skip_statuses}
    return rows, fieldnames, existing, skip_companies


def append_tracker_row(fieldnames, company, role, url, platform, salary, notes, status="JD DOWNLOADED"):
    row = {k: "" for k in fieldnames}
    row["Company"] = company
    row["Role"] = role
    row["Status"] = status
    row["Platform"] = platform
    row["Date Applied"] = ""
    row["Tracking Status"] = "—"
    row["URL"] = url
    row["Salary Range"] = salary or "—"
    row["Required Fit Match"] = "—"
    row["Wanted Fit Match"] = "—"
    row["Notes"] = notes
    with open(TRACKER_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(row)


def auto_skip_title(title: str, patterns: list) -> bool:
    t = title.lower()
    return any(re.search(p, t) for p in patterns)


def extract_salary_top_usd(salary_str: str):
    if not salary_str:
        return None
    nums = []
    for m in re.finditer(r"\$?\s*(\d{2,3})(?:[,.]?(\d{3}))?\s*([kK])?", salary_str):
        whole, thousand, k = m.groups()
        if k:
            val = int(whole) * 1000
        elif thousand:
            val = int(whole) * 1000 + int(thousand)
        else:
            n = int(whole)
            val = n * 1000 if n < 1000 else n
        nums.append(val)
    return max(nums) if nums else None


def qualify_jd(title: str, jd_text: str, salary_str: str, prefs: dict):
    """Conservative pre-filter. Returns (verdict, reason).
    verdict ∈ {'OK', 'SKIP'}. False-skip is worse than false-save — the
    AI evaluate task can still DISQUALIFY a saved row.
    """
    if not jd_text:
        return "OK", ""

    title_lower = title.lower()
    jd_lower = jd_text.lower()

    # Hard credential gates
    softeners = re.compile(
        r"or\s+(equivalent|relevant|comparable)\s+(experience|expertise|education)"
        r"|or\s+\d+\s*\+?\s*years?\s+of"
        r"|or\s+equivalent\b"
        r"|preferred\b|nice[- ]to[- ]have\b|bonus\b",
        re.IGNORECASE,
    )
    hard_creds = [
        (r"\b(ph\.?\s*d|doctorate|doctoral degree)\b", "PhD"),
        (r"\bm\.?d\b\s*(degree|required)", "MD"),
        (r"\bj\.?d\b\s*(degree|required)", "JD"),
        (r"\bp\.?\s*e\.?\s*license\b", "PE license"),
        (r"\b(active|current)\s+(top secret|ts/sci|secret)\s+(clearance|security clearance)", "active security clearance"),
    ]
    user_skip_creds = {c.lower() for c in prefs.get("hard_credentials_to_skip", [])}
    for pat, label in hard_creds:
        if label.lower() not in str(user_skip_creds).lower():
            continue
        m = re.search(pat, jd_lower)
        if not m:
            continue
        tail = jd_lower[m.end():m.end() + 250]
        head = jd_lower[max(0, m.start() - 100):m.start()]
        if softeners.search(tail) or softeners.search(head):
            continue
        return "SKIP", f"hard credential: {label} required"

    # Skill keyword sanity — JD must mention at least one skill the user has
    skill_kws = [kw.lower() for kw in prefs.get("skill_keywords", [])]
    if skill_kws:
        if not any(re.search(rf"\b{re.escape(kw)}\b", jd_lower) for kw in skill_kws):
            return "SKIP", "no relevant skill keywords in JD body"

    # Salary floor
    min_salary = prefs.get("compensation", {}).get("min_salary_usd", 0)
    top = extract_salary_top_usd(salary_str)
    if top is None:
        m = re.search(
            r"\$\s?\d{2,3}[,.]?\d{3}\s*[-–to]+\s*\$?\s?\d{2,3}[,.]?\d{3}",
            jd_text, re.IGNORECASE,
        )
        if m:
            top = extract_salary_top_usd(m.group(0))
    if top is not None and min_salary and top < min_salary:
        return "SKIP", f"top salary ${top:,} below floor ${min_salary:,}"

    # Title auto-skip
    if auto_skip_title(title, prefs.get("auto_skip_title_patterns", [])):
        return "SKIP", "auto-skip title pattern"

    return "OK", ""


def location_verdict(jd_text: str, card_raw: str, prefs: dict) -> str:
    """Returns 'collect' (proceed) or 'skip' or 'ambiguous'."""
    loc = prefs.get("location", {})
    remote_ok = loc.get("remote_ok", False)
    hybrid_ok = loc.get("hybrid_ok", False)
    metro_cities = {c.lower() for c in loc.get("metro_cities", [])}

    txt = (jd_text + " " + (card_raw or "")).lower()

    remote_patterns = [
        r"\bfully remote\b", r"\bremote[- ]only\b", r"\bremote[- ]first\b",
        r"\bwork from anywhere\b", r"\bwork from home\b", r"\bwfh\b",
        r"\btelecommute\b|\btelecommuting\b", r"\b100\s*%?\s*remote\b",
        r"\bremote,\s*(united states|us|usa)\b",
    ]
    is_remote = any(re.search(p, txt) for p in remote_patterns) or re.search(r"\b(remote.*us|us.*remote)\b", txt)
    if is_remote and remote_ok:
        return "collect"

    for city in metro_cities:
        if re.search(rf"\b{re.escape(city)}\b", txt):
            return "collect"

    if "hybrid" in txt:
        return "collect" if hybrid_ok else "skip"
    if "onsite" in txt or "on-site" in txt or "in-office" in txt:
        return "skip"
    if re.search(r"\bremote\b", txt) and not re.search(r"remote:\s*no\b", txt):
        return "collect" if remote_ok else "ambiguous"

    return "ambiguous"


FORBIDDEN_URL_PATTERNS = [r"linkedin\.com/company/", r"/search\?"]

def forbidden_url(url: str) -> bool:
    if not url:
        return True
    u = url.strip().lower()
    if u.startswith(("chrome-error://", "chrome://", "about:", "data:", "javascript:")):
        return True
    return any(re.search(p, url) for p in FORBIDDEN_URL_PATTERNS)


def clean_url_through_google(u: str) -> str:
    try:
        p = urlparse(u)
    except Exception:
        return u
    if "google.com" in p.netloc:
        qs = parse_qs(p.query)
        for key in ("url", "q", "adurl"):
            if key in qs and qs[key]:
                inner = qs[key][0]
                if inner.startswith("http"):
                    return inner
    return u


def wait_for_not_captcha(page, log):
    banner_shown = False
    while True:
        url = page.url or ""
        try:
            body = page.evaluate("document.body ? document.body.innerText.slice(0, 2000) : ''")
        except Exception:
            body = ""
        is_captcha = (
            "sorry/index" in url or "consent.google" in url
            or "unusual traffic" in (body or "").lower()
        )
        if not is_captcha:
            if banner_shown:
                log.write("  [captcha cleared, resuming]\n")
                log.flush()
            return
        if not banner_shown:
            print("!! CAPTCHA detected — solve in browser, script will auto-resume.", flush=True)
            log.write("  [captcha detected, waiting]\n")
            log.flush()
            banner_shown = True
        time.sleep(5)


def run_scroll_loop(page):
    js = """
    (async () => {
      let last = 0, stable = 0;
      for (let i = 0; i < 60; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 900));
        const n = document.querySelectorAll('div.EimVGf').length;
        if (n === last) { if (++stable >= 4) break; } else { stable = 0; last = n; }
      }
      return document.querySelectorAll('div.EimVGf').length;
    })();
    """
    try:
        return page.evaluate(js) or 0
    except PWError:
        return page.evaluate("document.querySelectorAll('div.EimVGf').length") or 0


def enumerate_cards(page):
    js = """
    (() => {
      const out = [];
      document.querySelectorAll('div.EimVGf').forEach((card, idx) => {
        const clean = card.innerText.split('\\n').map(l=>l.trim()).filter(l=>l && l!=='NEW' && l.length>1);
        out.push({ idx, title: clean[0]||'', company: clean[1]||'', raw: clean.slice(0,6).join(' | ') });
      });
      return out;
    })();
    """
    return page.evaluate(js) or []


def click_card_and_extract(page, card_idx, card_title):
    click_js = """
    async (idx) => {
      const c = document.querySelectorAll('div.EimVGf')[idx];
      if (!c) return { ok:false };
      c.scrollIntoView({block:'center'});
      await new Promise(r => setTimeout(r, 400));
      const opener = c.querySelector('[jsaction="h5M12e"]') || c;
      opener.click();
      await new Promise(r => setTimeout(r, 2500));
      return { ok: true };
    }
    """
    page.evaluate(click_js, card_idx)

    # Expand "show full description" if present
    expand_js = """
    async () => {
      const TOGGLE_RE = /show full description|read more|see more/i;
      for (let pass = 0; pass < 4; pass++) {
        const all = [...document.querySelectorAll('div, span, button, a, [role="button"], [jsaction]')];
        const el = all.find(e => e.offsetParent !== null && TOGGLE_RE.test((e.innerText||'').trim()) && (e.innerText||'').length < 120);
        if (!el) return true;
        el.scrollIntoView({block:'center'});
        await new Promise(r => setTimeout(r, 250));
        try { el.click(); } catch(_) {}
        await new Promise(r => setTimeout(r, 1500));
      }
      return false;
    }
    """
    try:
        page.evaluate(expand_js)
    except PWError:
        pass

    extract_js = """
    (cardTitleSubstr) => {
      const heads = [...document.querySelectorAll('h1, h2, [role="heading"]')]
        .filter(h => h.offsetParent !== null);
      const h = heads.find(x => (x.innerText||'').includes(cardTitleSubstr)) || heads[0];
      if (!h) return { err: 'panel heading not found' };
      let node = h, best = h;
      for (let i = 0; i < 12; i++) {
        const parent = node.parentElement;
        if (!parent) break;
        const txt = parent.innerText || '';
        if (txt.length > 18000) break;
        node = parent;
        best = node;
      }
      const jdText = (best.innerText || '').substring(0, 15000);
      const applyLinks = [];
      document.querySelectorAll('a[target="_blank"]').forEach(a => {
        if (/^apply on /i.test((a.innerText||'').trim()) && applyLinks.length < 5) {
          applyLinks.push({ href: a.href, text: (a.innerText||'').trim() });
        }
      });
      return { jdText, applyLinks, hText: (h.innerText||'').trim().substring(0, 200) };
    }
    """
    return page.evaluate(extract_js, card_title[:30])


def google_jobs_url(query: str, prefs: dict) -> str:
    loc = prefs.get("location", {})
    primary = f"{loc.get('primary_city', '')} {loc.get('primary_state', '')}".strip()
    location_part = primary if primary else "United States"
    full_query = f"{query} {location_part}".strip()
    chips = "htichips=date_posted:week,remote_jobs:1" if loc.get("remote_ok") else "htichips=date_posted:week"
    return f"https://www.google.com/search?q={quote_plus(full_query)}&ibp=htl;jobs&{chips}"


def save_jd_and_append(card, jd_text, apply_url, prefs, fieldnames, existing, skip_companies, log):
    title = (card.get("title") or "").strip()
    company = (card.get("company") or "").strip()
    if not title or not company:
        return False

    company_pascal = pascal_company(company)
    key = (company.lower(), title.lower())
    if key in existing:
        log.write(f"  [dup] {company} — {title}\n")
        return False
    if company.lower() in skip_companies:
        log.write(f"  [skip-company-applied] {company} — {title}\n")
        return False

    # Location filter
    loc_verdict = location_verdict(jd_text, card.get("raw", ""), prefs)
    if loc_verdict == "skip":
        log.write(f"  [loc-skip] {company} — {title}\n")
        return False

    # Qualification pre-filter (conservative)
    salary_match = re.search(r"\$[\d,]+\s*(?:[-–to]+\s*\$[\d,]+)?(?:\s*[kK])?", jd_text)
    salary_str = salary_match.group(0) if salary_match else ""
    verdict, reason = qualify_jd(title, jd_text, salary_str, prefs)
    if verdict == "SKIP":
        append_tracker_row(fieldnames, company, title, apply_url, "Google Jobs",
                           salary_str, f"Auto-skip: {reason}", status="DISQUALIFIED")
        existing.add(key)
        log.write(f"  [dq] {company} — {title} — {reason}\n")
        return False

    # Save JD
    folder = JOBS_DIR / company_pascal
    folder.mkdir(parents=True, exist_ok=True)
    jd_path = folder / f"Job_Description_{company_pascal}.txt"
    header = (
        f"# {company} — {title}\n"
        f"# Source: Google Jobs\n"
        f"# Apply URL: {apply_url}\n"
        f"# Saved: {TODAY.isoformat()}\n"
        f"\n"
    )
    jd_path.write_text(header + jd_text, encoding="utf-8")

    notes = f"Found via Google Jobs on {TODAY.isoformat()}"
    append_tracker_row(fieldnames, company, title, apply_url, "Google Jobs", salary_str, notes)
    existing.add(key)
    log.write(f"  [save] {company} — {title}\n")
    print(f"  saved: {company} — {title}", flush=True)
    return True


# ---------- main ----------

def run_google_pass(page, prefs, fieldnames, existing, skip_companies, log, smoke=False):
    titles = prefs.get("target_titles", [])
    if smoke:
        titles = titles[:1]
    queries = list(titles) + list(prefs.get("boolean_queries", []))
    if smoke:
        queries = queries[:1]

    saved = 0
    for i, query in enumerate(queries):
        url = google_jobs_url(query, prefs)
        print(f"\n[{i+1}/{len(queries)}] {query}", flush=True)
        log.write(f"\n[query {i+1}] {query}\n  url: {url}\n")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except (PWTimeout, PWError) as e:
            log.write(f"  navigation failed: {e}\n")
            continue
        time.sleep(2)
        wait_for_not_captcha(page, log)
        card_count = run_scroll_loop(page)
        log.write(f"  cards loaded: {card_count}\n")
        if card_count == 0:
            continue

        cards = enumerate_cards(page)
        for card in cards:
            try:
                result = click_card_and_extract(page, card["idx"], card.get("title", ""))
                if not isinstance(result, dict) or "jdText" not in result:
                    continue
                jd_text = result.get("jdText", "")
                apply_links = result.get("applyLinks", [])
                apply_url = ""
                for a in apply_links:
                    cleaned = clean_url_through_google(a.get("href", ""))
                    if not forbidden_url(cleaned):
                        apply_url = cleaned
                        break
                if save_jd_and_append(card, jd_text, apply_url, prefs, fieldnames,
                                      existing, skip_companies, log):
                    saved += 1
            except (PWTimeout, PWError) as e:
                log.write(f"  card error: {e}\n")
                continue
        wait_for_not_captcha(page, log)

    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run one query only, for sanity-check")
    parser.add_argument("--no-headed", action="store_true",
                        help="Run headless (captchas will block the script)")
    args = parser.parse_args()

    prefs = load_preferences()
    _, fieldnames, existing, skip_companies = load_tracker()

    log_path = BASE_DIR / f"find_jobs_log_{TODAY.isoformat()}.txt"
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n=== {TODAY.isoformat()} run ===\n")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=args.no_headed)
            context = browser.new_context()
            page = context.new_page()

            saved = run_google_pass(page, prefs, fieldnames, existing, skip_companies, log,
                                    smoke=args.smoke_test)

            browser.close()

        log.write(f"\n=== run complete — saved {saved} new rows ===\n")
        print(f"\nDone. Saved {saved} new rows. Log: {log_path.name}", flush=True)


if __name__ == "__main__":
    main()
