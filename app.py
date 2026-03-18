"""
CBJ-Approps Report Linker
Connects agency Congressional Budget Justifications with appropriations committee report sections.
"""

import json
import os
import re
import time
import hashlib
from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

CONGRESS_API_KEY = "CONGRESS_API_KEY"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# The 12 appropriations subcommittees with their FY2024 report numbers
SUBCOMMITTEES = [
    {
        "id": "ag",
        "name": "Agriculture, Rural Development, FDA & Related Agencies",
        "short_name": "Agriculture",
        "house_report": {"congress": 118, "type": "HRPT", "number": 124},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 80},
        "house_bill": "H.R. 4368",
        "agencies": [
            "Department of Agriculture",
            "Farm Credit System Insurance Corporation",
            "Commodity Futures Trading Commission",
        ],
    },
    {
        "id": "cjs",
        "name": "Commerce, Justice, Science & Related Agencies",
        "short_name": "Commerce-Justice-Science",
        "house_report": None,  # CJS didn't get a House committee report in 118th
        "senate_report": {"congress": 118, "type": "SRPT", "number": 62},
        "house_bill": "H.R. 5893",
        "agencies": [
            "Department of Commerce",
            "Department of Justice",
            "National Aeronautics and Space Administration",
            "National Science Foundation",
            "Marine Mammal Commission",
            "Commission on Civil Rights",
            "Equal Employment Opportunity Commission",
            "International Trade Commission",
            "United States Trade and Development Agency",
        ],
    },
    {
        "id": "defense",
        "name": "Defense",
        "short_name": "Defense",
        "house_report": {"congress": 118, "type": "HRPT", "number": 121},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 81},
        "house_bill": "H.R. 4365",
        "agencies": [
            "Department of Defense",
        ],
    },
    {
        "id": "ew",
        "name": "Energy & Water Development & Related Agencies",
        "short_name": "Energy-Water",
        "house_report": {"congress": 118, "type": "HRPT", "number": 126},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 72},
        "house_bill": "H.R. 4394",
        "agencies": [
            "Department of Energy",
            "Corps of Engineers - Civil Works",
            "Nuclear Regulatory Commission",
            "Defense Nuclear Facilities Safety Board",
            "Nuclear Waste Technical Review Board",
            "Appalachian Regional Commission",
            "Delta Regional Authority",
            "Denali Commission",
            "Northern Border Regional Commission",
            "Southeast Crescent Regional Commission",
        ],
    },
    {
        "id": "fsgg",
        "name": "Financial Services & General Government",
        "short_name": "Financial Services",
        "house_report": {"congress": 118, "type": "HRPT", "number": 145},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 75},
        "house_bill": "H.R. 4664",
        "agencies": [
            "Department of the Treasury",
            "Executive Office of the President",
            "General Services Administration",
            "Office of Personnel Management",
            "Small Business Administration",
            "Securities and Exchange Commission",
            "Federal Communications Commission",
            "Federal Trade Commission",
            "Federal Election Commission",
            "Federal Labor Relations Authority",
            "Consumer Product Safety Commission",
            "Election Assistance Commission",
            "Federal Deposit Insurance Corporation",
            "National Credit Union Administration",
            "Office of Government Ethics",
            "Office of Special Counsel",
            "Merit Systems Protection Board",
            "Federal Permitting Improvement Steering Council",
            "National Archives and Records Administration",
            "Administrative Conference of the U.S.",
            "Access Board",
            "Public Buildings Reform Board",
            "Consumer Financial Protection Bureau",
            "District of Columbia Courts",
        ],
    },
    {
        "id": "dhs",
        "name": "Homeland Security",
        "short_name": "Homeland Security",
        "house_report": {"congress": 118, "type": "HRPT", "number": 123},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 85},
        "house_bill": "H.R. 4367",
        "agencies": [
            "Department of Homeland Security",
        ],
    },
    {
        "id": "interior",
        "name": "Interior, Environment & Related Agencies",
        "short_name": "Interior-Environment",
        "house_report": {"congress": 118, "type": "HRPT", "number": 155},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 83},
        "house_bill": "H.R. 4821",
        "agencies": [
            "Department of the Interior",
            "Environmental Protection Agency",
            "Advisory Council on Historic Preservation",
            "Commission of Fine Arts",
            "Commission for Preservation of America's Heritage Abroad",
            "Gulf Coast Ecosystem Restoration Council",
            "Institute of Museum and Library Services",
            "John F. Kennedy Center for the Performing Arts",
            "National Endowment for the Arts",
            "National Endowment for the Humanities",
            "Morris K. Udall and Stewart L. Udall Foundation",
            "Presidio Trust",
            "United States Chemical Safety Board",
        ],
    },
    {
        "id": "lhhs",
        "name": "Labor, HHS, Education & Related Agencies",
        "short_name": "Labor-HHS-Education",
        "house_report": None,  # LHHS didn't get a formal House committee report in 118th
        "senate_report": {"congress": 118, "type": "SRPT", "number": 82},
        "house_bill": "H.R. 5894",
        "agencies": [
            "Department of Labor",
            "Department of Health and Human Services",
            "Department of Education",
            "Corporation for National and Community Service",
            "Federal Mediation and Conciliation Service",
            "Federal Mine Safety and Health Review Commission",
            "National Labor Relations Board",
            "National Mediation Board",
            "Occupational Safety and Health Review Commission",
            "Railroad Retirement Board",
            "Social Security Administration",
        ],
    },
    {
        "id": "leg",
        "name": "Legislative Branch",
        "short_name": "Legislative Branch",
        "house_report": {"congress": 118, "type": "HRPT", "number": 120},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 60},
        "house_bill": "H.R. 4364",
        "agencies": [
            "Government Accountability Office",
        ],
    },
    {
        "id": "milcon",
        "name": "Military Construction, Veterans Affairs & Related Agencies",
        "short_name": "MilCon-VA",
        "house_report": {"congress": 118, "type": "HRPT", "number": 122},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 73},
        "house_bill": "H.R. 4366",
        "agencies": [
            "Department of Veterans Affairs",
            "American Battle Monuments Commission",
            "United States Court of Appeals for Veterans Claims",
            "Court Services and Offender Supervision Agency",
        ],
    },
    {
        "id": "sfops",
        "name": "State, Foreign Operations & Related Programs",
        "short_name": "State-Foreign Ops",
        "house_report": {"congress": 118, "type": "HRPT", "number": 146},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 71},
        "house_bill": "H.R. 4665",
        "agencies": [
            "Department of State",
            "Agency for International Development",
            "African Development Foundation",
            "Export-Import Bank of the United States",
            "Millennium Challenge Corporation",
            "Overseas Private Investment Corporation",
            "U.S. International Development Finance Corporation",
            "Peace Corps",
            "U.S. Agency for Global Media",
        ],
    },
    {
        "id": "thud",
        "name": "Transportation, HUD & Related Agencies",
        "short_name": "Transportation-HUD",
        "house_report": {"congress": 118, "type": "HRPT", "number": 154},
        "senate_report": {"congress": 118, "type": "SRPT", "number": 70},
        "house_bill": "H.R. 4820",
        "agencies": [
            "Department of Transportation",
            "Department of Housing and Urban Development",
            "National Transportation Safety Board",
            "Surface Transportation Board",
            "Federal Maritime Commission",
            "National Capital Planning Commission",
        ],
    },
]


def get_cache_path(key):
    """Get a cache file path for a given key."""
    safe_key = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{safe_key}.json")


def cache_get(key, max_age=86400):
    """Get a cached value. Returns None if not cached or expired."""
    path = get_cache_path(key)
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < max_age:
                return data.get("value")
        except (json.JSONDecodeError, IOError):
            pass
    return None


def cache_set(key, value):
    """Cache a value."""
    path = get_cache_path(key)
    with open(path, "w") as f:
        json.dump({"timestamp": time.time(), "value": value}, f)


def fetch_agencies():
    """Fetch agency data from USASpending.gov."""
    cache_key = "usaspending_agencies"
    cached = cache_get(cache_key)
    if cached:
        return cached

    url = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        agencies = data.get("results", [])
        cache_set(cache_key, agencies)
        return agencies
    except Exception as e:
        print(f"Error fetching agencies: {e}")
        return []


def get_report_text_url(report_info):
    """Get the HTML text URL for a committee report from Congress.gov API."""
    if not report_info:
        return None

    congress = report_info["congress"]
    rtype = report_info["type"].lower()
    number = report_info["number"]

    cache_key = f"report_text_url_{congress}_{rtype}_{number}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    api_url = (
        f"https://api.congress.gov/v3/committee-report/{congress}/{rtype}/{number}/text"
        f"?api_key={CONGRESS_API_KEY}&format=json"
    )
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text_versions = data.get("textVersions", data.get("text", []))
        # Prefer HTML format
        for tv in text_versions:
            formats = tv.get("formats", [])
            for fmt in formats:
                if fmt.get("type") == "Formatted Text":
                    url = fmt.get("url")
                    if url:
                        cache_set(cache_key, url)
                        return url
        # Fallback to any available
        if text_versions:
            formats = text_versions[0].get("formats", [])
            if formats:
                url = formats[0].get("url")
                cache_set(cache_key, url)
                return url
    except Exception as e:
        print(f"Error fetching report text URL: {e}")

    return None


def fetch_report_html(report_info):
    """Fetch the HTML text of a committee report."""
    if not report_info:
        return None

    congress = report_info["congress"]
    rtype = report_info["type"].lower()
    number = report_info["number"]

    cache_key = f"report_html_{congress}_{rtype}_{number}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    text_url = get_report_text_url(report_info)
    if not text_url:
        return None

    try:
        resp = requests.get(text_url, timeout=60)
        resp.raise_for_status()
        html = resp.text
        cache_set(cache_key, html)
        return html
    except Exception as e:
        print(f"Error fetching report HTML: {e}")
        return None


def parse_report_sections(html):
    """Parse committee report HTML into navigable sections.

    Appropriations committee reports follow a consistent structure:
    - TITLE I, TITLE II, etc. for major divisions
    - Agency/Department names as sub-headings (centered, all-caps)
    - Account names (e.g., "SALARIES AND EXPENSES") under each agency
    - "COMMITTEE PROVISIONS" markers precede the actual directives
    - Budget tables with dollar amounts
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    lines = text.split("\n")

    sections = []
    current_title = None
    current_heading = None
    current_content = []
    current_level = 0
    past_preamble = False

    # Patterns
    title_pattern = re.compile(r"^TITLE\s+[IVXLC]+\s*$")
    toc_line_pattern = re.compile(r".*\.{3,}\s*\d+")
    heading_pattern = re.compile(r"^[A-Z][A-Z\s,\-\.\&\(\)\/\'\:]+$")
    dollar_pattern = re.compile(r"\$[\d,]+")

    # Headings to skip (not useful as section markers)
    skip_headings = {
        "HOUSE OF REPRESENTATIVES", "R E P O R T", "CONTENTS",
        "DISSENTING VIEWS", "COMPARISON", "FY",
    }

    # Major agency/department level keywords
    major_org_keywords = [
        "DEPARTMENT OF", "AGENCY FOR", "OFFICE OF THE",
        "NATIONAL", "FEDERAL", "ENVIRONMENTAL PROTECTION",
        "SMALL BUSINESS", "SECURITIES AND EXCHANGE",
        "GENERAL SERVICES", "SOCIAL SECURITY",
    ]

    def flush_section():
        """Save current accumulated section."""
        nonlocal current_content
        if current_content:
            content_text = "\n".join(current_content).strip()
            if content_text and len(content_text) > 30:
                sections.append({
                    "title": current_title or "Overview",
                    "heading": current_heading,
                    "content": content_text,
                    "level": current_level,
                })
        current_content = []

    # First pass: join multi-line headings
    joined_lines = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Check if this and next line form a multi-line heading
        if (
            heading_pattern.match(stripped)
            and len(stripped) > 5
            and i + 1 < len(lines)
        ):
            next_stripped = lines[i + 1].strip()
            if (
                heading_pattern.match(next_stripped)
                and len(next_stripped) > 2
                and len(next_stripped) < 80
                and not dollar_pattern.search(next_stripped)
                and not toc_line_pattern.match(next_stripped)
            ):
                # Join the two lines
                joined_lines.append(stripped + " " + next_stripped)
                i += 2
                continue
        joined_lines.append(lines[i])
        i += 1

    for line in joined_lines:
        stripped = line.strip()
        if not stripped:
            current_content.append("")
            continue

        # Skip TOC lines
        if toc_line_pattern.match(stripped) and not past_preamble:
            continue

        # Detect start of substantive content
        if stripped == "OVERVIEW" or title_pattern.match(stripped):
            past_preamble = True

        if not past_preamble:
            continue

        # TITLE markers
        if title_pattern.match(stripped):
            flush_section()
            current_title = stripped
            current_heading = None
            current_level = 0
            current_content = [stripped]
            continue

        # All-caps headings
        if (
            heading_pattern.match(stripped)
            and len(stripped) > 5
            and len(stripped) < 200
            and not dollar_pattern.search(stripped)
            and stripped not in skip_headings
            and stripped != "COMMITTEE PROVISIONS"
        ):
            # Is this a major heading?
            is_major = (
                any(kw in stripped for kw in major_org_keywords)
                or len(stripped) > 30
            )

            flush_section()
            current_heading = stripped.title()
            current_level = 1 if is_major else 2
            current_content = [stripped]
            continue

        current_content.append(line)

    flush_section()
    return sections


def build_agency_cbj_map(agencies):
    """Build a mapping from agency name to CBJ URL."""
    cbj_map = {}
    for agency in agencies:
        name = agency.get("agency_name", "")
        url = agency.get("congressional_justification_url")
        if name and url:
            cbj_map[name] = {
                "url": url,
                "toptier_code": agency.get("toptier_code", ""),
                "abbreviation": agency.get("abbreviation", ""),
                "budget_authority": agency.get("budget_authority_amount", 0),
                "agency_slug": agency.get("agency_slug", ""),
            }
    return cbj_map


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/subcommittees")
def api_subcommittees():
    """Return list of appropriations subcommittees."""
    return jsonify(SUBCOMMITTEES)


@app.route("/api/agencies")
def api_agencies():
    """Return agency data with CBJ URLs from USASpending.gov."""
    agencies = fetch_agencies()
    cbj_map = build_agency_cbj_map(agencies)

    # Enrich subcommittee data with CBJ URLs
    result = []
    for sub in SUBCOMMITTEES:
        sub_data = {
            "id": sub["id"],
            "name": sub["name"],
            "short_name": sub["short_name"],
            "house_bill": sub["house_bill"],
            "agencies": [],
        }
        for agency_name in sub["agencies"]:
            agency_info = cbj_map.get(agency_name, {})
            sub_data["agencies"].append({
                "name": agency_name,
                "cbj_url": agency_info.get("url"),
                "toptier_code": agency_info.get("toptier_code", ""),
                "abbreviation": agency_info.get("abbreviation", ""),
                "budget_authority": agency_info.get("budget_authority", 0),
                "usaspending_url": (
                    f"https://www.usaspending.gov/agency/{agency_info['agency_slug']}"
                    if agency_info.get("agency_slug")
                    else None
                ),
            })
        result.append(sub_data)

    return jsonify(result)


@app.route("/api/report/<sub_id>/<chamber>")
def api_report(sub_id, chamber):
    """Fetch and return parsed committee report sections for a subcommittee."""
    sub = next((s for s in SUBCOMMITTEES if s["id"] == sub_id), None)
    if not sub:
        return jsonify({"error": "Subcommittee not found"}), 404

    report_info = sub.get(f"{chamber}_report")
    if not report_info:
        return jsonify({
            "error": f"No {chamber} committee report available for this subcommittee",
            "available": False,
        }), 404

    html = fetch_report_html(report_info)
    if not html:
        return jsonify({"error": "Could not fetch report text"}), 500

    sections = parse_report_sections(html)

    # Build the report URL for linking
    congress = report_info["congress"]
    rtype = report_info["type"].lower()
    number = report_info["number"]
    report_url = get_report_text_url(report_info)

    return jsonify({
        "subcommittee": sub["name"],
        "chamber": chamber,
        "report_citation": f"{'H' if chamber == 'house' else 'S'}. Rept. {congress}-{number}",
        "report_url": report_url,
        "sections": sections,
        "section_count": len(sections),
    })


@app.route("/api/search")
def api_search():
    """Search across all cached report sections."""
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({"error": "Query too short", "results": []}), 400

    results = []
    query_lower = query.lower()
    query_words = query_lower.split()

    for sub in SUBCOMMITTEES:
        for chamber in ["house", "senate"]:
            report_info = sub.get(f"{chamber}_report")
            if not report_info:
                continue

            html = fetch_report_html(report_info)
            if not html:
                continue

            sections = parse_report_sections(html)
            for section in sections:
                content_lower = section["content"].lower()
                # Check if all query words appear in the content
                if all(w in content_lower for w in query_words):
                    # Find the most relevant snippet
                    snippet = extract_snippet(section["content"], query, max_len=300)
                    results.append({
                        "subcommittee": sub["short_name"],
                        "subcommittee_id": sub["id"],
                        "chamber": chamber,
                        "title": section.get("title", ""),
                        "heading": section.get("heading", ""),
                        "snippet": snippet,
                    })

    return jsonify({"query": query, "results": results[:50]})


def extract_snippet(text, query, max_len=300):
    """Extract a relevant snippet from text around the query."""
    query_lower = query.lower()
    text_lower = text.lower()
    idx = text_lower.find(query_lower)
    if idx == -1:
        # Find first query word
        for word in query_lower.split():
            idx = text_lower.find(word)
            if idx != -1:
                break
    if idx == -1:
        return text[:max_len] + "..." if len(text) > max_len else text

    start = max(0, idx - max_len // 3)
    end = min(len(text), idx + max_len * 2 // 3)

    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8097, debug=True)
