#!/usr/bin/env python3
"""Fetch Katie B. Hines (Carolina Beach) events from New Hanover County and write events.json.

How it works:
1. Opens the county Nutrition page and finds the newest Carolina Beach monthly
   calendar PDF (links named like "Nov-2026-CB" or "Carolina-Beach---Feb-2026").
2. Reads the "Special Events" column of that PDF with pdftotext (poppler-utils).
3. Adds county-wide closures ("Closed for Holiday") from the SRC - Events iCal feed.
   (The county iCal feeds only list Wilmington Senior Resource Center events, not
   Carolina Beach ones, so the PDF is the only county source for this center.)
4. Keeps the existing events.json if anything fails, so the site never goes blank.
"""
import json, re, subprocess, sys, tempfile, urllib.request, datetime, os, html

UA = {"User-Agent": "Mozilla/5.0 (KatieBHinesSiteBot)"}
BASE = "https://www.nhcgov.com"
NUTRITION = BASE + "/524/Nutrition"
ICAL = BASE + "/common/modules/iCalendar/iCalendar.aspx?catID=56&feed=calendar"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "events.json")
MONTHS = {m: i for i, m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def find_pdf():
    page = get(NUTRITION).decode("utf-8", "ignore")
    best = None
    for path in set(re.findall(r'/DocumentCenter/View/(\d+/[^"\'>\s]+)', page)):
        name = path.split("/", 1)[1].lower()
        if not (name.endswith("-cb") or "carolina-beach" in name):
            continue
        m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*-+(20\d\d)", name)
        if not m:
            continue
        key = (int(m.group(2)), MONTHS[m.group(1)])
        if best is None or key > best[0]:
            best = (key, BASE + "/DocumentCenter/View/" + path)
    if not best:
        raise RuntimeError("No Carolina Beach calendar PDF link found on Nutrition page")
    return best

TIME_RE = re.compile(r"^\d{1,2}(:\d\d)?(-\d{0,2}(:\d\d)?)?$|^\d{1,2}(:\d\d)?-$")
DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})(?:-(\d{1,2}))?(?:\s+(.*))?$")

def parse_pdf(data, year, source_url):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data); f.flush()
        text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    # Right-hand column starts where the first M/D date appears far to the right.
    col = min((m.start(1) for l in lines for m in [re.search(r"\s{3,}(\d{1,2}/\d{1,2})\b", l)] if m and m.start(1) > 50), default=None)
    if col is None:
        raise RuntimeError("Could not find the Special Events column in the PDF")
    events, cur = [], None
    for l in lines:
        if "NHC SRC Rep" in l or "Drop-in Daily" in l:
            break
        right = l[col - 2:].strip() if len(l) > col - 2 else ""
        if not right:
            continue
        parts = re.split(r"\s{2,}", right)
        for p in parts:
            p = p.strip()
            d = DATE_RE.match(p)
            if d:
                cur = {"month": int(d.group(1)), "day": int(d.group(2)), "end_day": int(d.group(3)) if d.group(3) else None, "time": "", "title": [d.group(4)] if d.group(4) else []}
                events.append(cur)
            elif cur and TIME_RE.match(p):
                cur["time"] += p
            elif cur:
                cur["title"].append(p)
    out = []
    for e in events:
        title = re.sub(r"\s+", " ", " ".join(e["title"])).strip(" ,")
        if not title:
            continue
        start = datetime.date(year, e["month"], e["day"])
        item = {"date": start.isoformat(), "time": fmt_time(e["time"]), "title": title,
                "location": "Katie B. Hines Senior Center", "source": source_url}
        if e["end_day"]:
            item["end_date"] = datetime.date(year, e["month"], e["end_day"]).isoformat()
        if title.upper().startswith("CLOSED"):
            item["closed"] = True
        out.append(item)
    return out

def fmt_time(t):
    t = t.strip("-")
    if not t:
        return ""
    def one(x):
        h, _, m = x.partition(":")
        h = int(h); ampm = "AM" if 8 <= h <= 11 else "PM"
        return f"{h}:{m or '00'} {ampm}"
    bits = [b for b in t.split("-") if b]
    return " – ".join(one(b) for b in bits)

def ical_closures():
    raw = get(ICAL).decode("utf-8", "ignore").replace("\r\n ", "")
    out = []
    for ev in raw.split("BEGIN:VEVENT")[1:]:
        s = re.search(r"^SUMMARY:(.*)$", ev, re.M); d = re.search(r"^DTSTART[^:]*:(\d{8})", ev, re.M)
        if s and d and "closed" in s.group(1).lower():
            ds = d.group(1)
            out.append({"date": f"{ds[:4]}-{ds[4:6]}-{ds[6:]}", "time": "", "title": "CLOSED – " + s.group(1).strip().replace("Closed for ", ""),
                        "location": "All county senior sites", "source": ICAL, "closed": True})
    return out

def pancake_breakfasts():
    """Island Famous Pancake Breakfast: first Saturday of each month, 7:30-11 AM, $10.
    Not on the county calendar; schedule from https://whatsupcb.com/venues/katie-b-hines-center/"""
    today = datetime.date.today(); out = []
    for k in range(2):
        y, m = today.year + (today.month - 1 + k) // 12, (today.month - 1 + k) % 12 + 1
        d = datetime.date(y, m, 1); d += datetime.timedelta(days=(5 - d.weekday()) % 7)
        out.append({"date": d.isoformat(), "time": "7:30 AM – 11:00 AM", "title": "Island Famous Pancake Breakfast ($10)",
                    "location": "Katie B. Hines Senior Center", "source": "https://whatsupcb.com/venues/katie-b-hines-center/"})
    return out

def main():
    (y, mo), url = find_pdf()
    events = parse_pdf(get(url), y, url)
    if not events:
        raise RuntimeError("PDF parsed but no events found")
    try:
        have = {e["date"] for e in events if e.get("closed")}
        have |= {(datetime.date.fromisoformat(e["date"]) + datetime.timedelta(days=1)).isoformat() for e in events if e.get("end_date")}
        events += [c for c in ical_closures() if c["date"] not in have]
    except Exception as ex:
        print("iCal closures skipped:", ex, file=sys.stderr)
    events += pancake_breakfasts()
    events.sort(key=lambda e: (e["date"], e["time"]))
    data = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "calendar_month": f"{y}-{mo:02d}", "calendar_pdf": url, "events": events}
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(events)} events from {url}")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("Update failed, keeping old events.json:", ex, file=sys.stderr)
        sys.exit(0 if os.path.exists(OUT) else 1)
