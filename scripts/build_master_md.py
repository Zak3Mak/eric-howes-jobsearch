"""Combine every text file in Eric's job-search repo into one Markdown file.

Usage: .venv/bin/python scripts/build_master_md.py .
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = ROOT / "ERIC_HOWES_COMPLETE.md"
APPS = ROOT / "Job_Applications"

PACKETS = ["IONSolar", "LVT", "Epcon", "ADIGlobalDistribution", "ManlyBands"]


def demote(text, levels=2):
    """Push embedded headings down so they nest under this file's sections."""
    def shift(match):
        hashes = match.group(1)
        return "#" * min(len(hashes) + levels, 6) + " "
    return re.sub(r"^(#{1,6}) ", shift, text, flags=re.M)


def read(path):
    return path.read_text(encoding="utf-8").strip()


def tracker_table(rows):
    header = ["Company", "Role", "Status", "Salary Range", "Required Fit Match", "Wanted Fit Match", "Notes", "URL"]
    index = {name: i for i, name in enumerate(rows[0])}
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in rows[1:]:
        cells = [row[index[name]].replace("|", "/").replace("\n", " ") for name in header]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def resume_markdown(content):
    out = ["**ERIC HOWES**", "", f"*{content['title_line'].replace('  |  ', ' | ')}*", "",
           "Orem, UT | (801) 367-6743 | howesfamilyhomes@gmail.com | linkedin.com/in/eric-howes-utah", "",
           "**Professional Summary**", "", content["summary"], ""]
    if content.get("skills"):
        out += ["**Core Skills**", "", " | ".join(content["skills"]), ""]
    out += ["**Professional Experience**", ""]
    for role in content["roles"]:
        out.append(f"*{role['title']}* | **{role['company']}** | {role['location']} | {role['dates']}")
        out.append("")
        if role.get("scope"):
            out += [f"_{role['scope']}_", ""]
        out += [f"- {b}" for b in role["bullets"]]
        out.append("")
    if content.get("earlier"):
        out += ["**Earlier Experience**", ""] + [f"- {e}" for e in content["earlier"]] + [""]
    out += ["**Education & Certifications**", ""] + [f"- {e}" for e in content["education"]]
    return "\n".join(out)


def letter_markdown(content):
    letter = content["cover_letter"]
    body = "\n\n".join(letter["paragraphs"])
    words = len(" ".join(letter["paragraphs"]).split())
    return (f"{letter['date']}\n\nHiring Manager\n{letter['company']}\n\nRe: {letter['role']}\n\n"
            f"{body}\n\nSincerely,\nEric Howes\n\n*({words} words)*")


rows = list(csv.reader((APPS / "tracker.csv").open(encoding="utf-8")))
status_of = {r[0]: r[2] for r in rows[1:]}
counts = {}
for r in rows[1:]:
    counts[r[2]] = counts.get(r[2], 0) + 1

doc = []
doc.append(f"# Eric Howes: Complete Job Search File\n\n"
           f"Generated {date.today():%B %-d, %Y} from the private repo github.com/Zak3Mak/eric-howes-jobsearch. "
           "This single file holds his profile, full work history, search preferences, the job tracker, every job "
           "description and fit evaluation, every tailored resume and cover letter (as text), and the rules used to "
           "produce them. Reference contacts are intentionally left out (they live only in the local references.md).")

doc.append("## Contents\n\n"
           "1. Pipeline Snapshot\n2. Candidate Profile\n3. Work History (source of truth)\n4. Search Preferences\n"
           "5. Open Questions for Eric\n6. Application Packets (resume + cover letter + notes + JD)\n"
           "7. Other Job Descriptions on File\n8. Full Job Tracker\n9. Appendix: Pipeline Rules, Task Files, and Scripts")

snapshot = "\n".join(f"- **{k}:** {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
doc.append(f"## 1. Pipeline Snapshot\n\n{len(rows) - 1} jobs tracked.\n\n{snapshot}\n\n"
           "**Ready for Eric to review and submit:** "
           "ION Solar (Operations Manager), LVT (Technical Program Manager, Hardware), Epcon (Construction Site Manager, contract), "
           "ADI Global Distribution (Quality Engineering Supervisor), Manly Bands (Director of Operations).\n\n"
           "**Borderline, no materials yet:** CRH / Jack B. Parson (South Area Shop & Equipment Manager), Daikin Comfort (Branch Manager).\n\n"
           "**Search method:** LinkedIn guest job search, Utah County (Provo, 25 mi) plus remote, past 7 days, about 40 queries "
           "across operations, quality, RMA, warehouse, inventory, program, product, and energy titles. Google Jobs is blocked by captcha.")

doc.append("## 2. Candidate Profile\n\n" + demote(read(ROOT / "profile.md")))
doc.append("## 3. Work History (source of truth)\n\n" + demote(read(ROOT / "workHistory.md")))
doc.append("## 4. Search Preferences\n\n" + demote(read(ROOT / "preferences.md")) +
           "\n\n### preferences.json (machine-readable)\n\n```json\n" + read(ROOT / "preferences.json") + "\n```")

doc.append("## 5. Open Questions for Eric\n\n"
           "- Degree conferral year for the UVU business degree (no year is stated on any resume).\n"
           "- Phone number: resumes use (801) 367-6743 from his master resume; LinkedIn lists 801-687-1022. Confirm which to use.\n"
           "- Smartsheet experience (named in the LVT posting).\n"
           "- ERP / SAP experience (named in the ADI posting).\n"
           "- LVT letter says he \"ran\" the PPG2500 into production; his master document says he \"supported\" it. Confirm he's comfortable with \"ran.\"\n"
           "- Epcon letter says he spent two years rolling boiler pipe at AA Machine. Confirm.\n"
           "- Any commercial, industrial, or utility-scale construction work not yet on file (biggest gap for Epcon).\n"
           "- Whether to use Vivint people as references (search is confidential at his current employer).\n"
           "- EEO fields in profile.md are still blank.")

packet_sections = ["## 6. Application Packets"]
for key in PACKETS:
    folder = APPS / key
    content = json.loads(read(folder / "content.json"))
    company = content["cover_letter"]["company"]
    role = content["cover_letter"]["role"]
    row = next((r for r in rows[1:] if r[0].split(" (")[0].replace(" ", "").lower()[:4] == company.replace(" ", "").lower()[:4]), None)
    status = row[2] if row else ""
    url = row[6] if row else ""
    part = [f"### {company}: {role}", "", f"**Status:** {status}  ", f"**Posting:** {url}  ",
            f"**Files:** Job_Applications/{key}/Howes_Eric_Resume_{key}.pdf, Howes_Eric_CoverLetter_{key}.pdf", "",
            "#### Tailored Resume", "", resume_markdown(content), "",
            "#### Cover Letter", "", letter_markdown(content), ""]
    notes = list(folder.glob("CoverLetter_Notes_*.txt"))
    if notes:
        part += ["#### Notes for Eric", "", "```text", read(notes[0]), "```", ""]
    for jd in folder.glob("Job_Description_*.txt"):
        part += ["#### Job Description and Fit Evaluation", "", "```text", read(jd), "```", ""]
    packet_sections.append("\n".join(part))
doc.append("\n\n".join(packet_sections))

other = ["## 7. Other Job Descriptions on File"]
for folder in sorted(p for p in APPS.iterdir() if p.is_dir() and p.name not in PACKETS):
    for jd in folder.glob("Job_Description_*.txt"):
        other.append(f"### {folder.name}\n\n```text\n{read(jd)}\n```")
doc.append("\n\n".join(other))

doc.append("## 8. Full Job Tracker\n\n" + tracker_table(rows))

appendix = ["## 9. Appendix: Pipeline Rules, Task Files, and Scripts"]
for name in ["START_HERE.md", "guardrails.md", "writingStyle.md", "evaluate_and_generate.md", "updater.md",
             "intake.md", "CLAUDE.md", "README.md", "ONBOARDING.md"]:
    path = ROOT / name
    if path.exists():
        appendix.append(f"### {name}\n\n" + demote(read(path), 3))
for name in ["scripts/build_documents.py", "scripts/sync_preferences.py", "find_jobs.py"]:
    path = ROOT / name
    if path.exists():
        appendix.append(f"### {name}\n\n```python\n{read(path)}\n```")
doc.append("\n\n".join(appendix))

OUT.write_text("\n\n---\n\n".join(doc) + "\n", encoding="utf-8")
print(OUT, OUT.stat().st_size, "bytes", len(OUT.read_text().splitlines()), "lines")
