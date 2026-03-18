# After Action Report: CBJ-Approps Report Linker

## Project Summary

**Goal:** Connect each federal agency's Congressional Budget Justifications (CBJs) with the corresponding sections of appropriations committee reports.

**Result:** A web application that maps 90+ federal agencies to their appropriations subcommittees, links to their CBJ documents, and provides searchable, browsable access to the full text of 22 committee reports (10 House, 12 Senate) from the 118th Congress, FY2024 appropriations cycle. The tool also extracts and classifies hundreds of committee directives from each report.

**URL:** http://127.0.0.1:8097 (local Flask server)

---

## What the Tool Does

### Three ways to use it:

1. **Find an agency** - Type an agency name or abbreviation (e.g., "EPA", "NASA", "HUD") in the search box. The tool identifies which appropriations subcommittee handles that agency and navigates directly to it.

2. **Search report language** - Search for a topic (e.g., "cybersecurity", "opioid", "artificial intelligence") across all 22 committee reports. Returns highlighted snippets showing where each subcommittee addressed that topic.

3. **Browse by subcommittee** - Select any of the 12 appropriations subcommittees to see:
   - Which agencies it covers
   - Links to each agency's CBJ and USASpending.gov profile
   - The full committee report text, parsed into expandable sections
   - Toggle between House and Senate versions
   - Extracted committee directives, classified by strength

### Committee Directive Extraction

The tool automatically extracts language where the committee tells agencies what to do:
- **Directives** (red): "The Committee directs...", "instructs...", "requires..."
- **Recommendations** (amber): "encourages...", "recommends...", "urges..."
- **Expectations** (blue): "expects...", "requests..."
- **Observations** (gray): "notes that...", "believes...", "supports..."

For example, the Agriculture report contains 351 extractable directives; Interior-Environment has 380.

---

## How I Built It

### Phase 1: Research (understanding the data landscape)

I started by investigating what APIs and data sources exist:
- **USASpending.gov API** provides a list of all federal agencies with links to their CBJ documents and spending profiles
- **Congress.gov API** provides committee report metadata and links to full-text HTML versions
- Committee report text is available as plain text inside `<pre>` tags on Congress.gov

**Key challenge identified:** There's no existing mapping between agencies and appropriations subcommittees in any API. I had to build this mapping using domain knowledge of the appropriations process.

### Phase 2: Building the mapping

I mapped all 90+ agencies to their correct appropriations subcommittees and identified the correct committee report numbers for each. This required:
- Querying the Congress.gov API for each report number to verify its title
- Cross-referencing with search results to find the correct Senate report numbers
- I initially had 4 incorrect Senate report numbers (out of 12) and caught and fixed all of them during verification

### Phase 3: Report text parsing

This was the most technically challenging part. Committee reports are hundreds of pages of plain text with structure indicated only by formatting conventions:
- ALL-CAPS lines indicate section headings
- Centered text indicates agency/bureau names
- Budget tables follow specific column formatting
- "COMMITTEE PROVISIONS" markers precede directive text
- Different reports use different preamble structures

I built a parser that:
- Joins multi-line headings (e.g., "NATIONAL INSTITUTE OF FOOD AND AGRICULTURE RESEARCH AND EDUCATION" + "ACTIVITIES")
- Distinguishes between TITLE-level, agency-level, and account-level headings
- Handles both "TITLE I" (standalone) and "TITLE I--DESCRIPTION" (inline) formats
- Skips table-of-contents lines and non-substantive preamble
- Filters out "Minority Views", "Bill Totals", and other non-content sections

### Phase 4: Feedback and iteration

I created a DC reviewer agent (role-playing as Daniel Schuman from Demand Progress) to provide expert feedback. Key feedback and responses:

| Feedback | Response |
|----------|----------|
| "Browse-first is wrong; staffers search by agency" | Added agency autocomplete with abbreviation matching |
| "Search should be the primary entry point" | Redesigned with search-first interface and quick-search buttons |
| "Extract directives - that's what oversight staff need" | Built directive extraction with strength classification |
| "Need copy/export for memos" | Added copy buttons on sections and "Copy All" on directives |
| "Fix agency search matching 'epa' inside 'Department'" | Implemented smart matching: abbreviation > word-start > substring |

---

## Obstacles Encountered

### 1. Wrong API response key name
**Problem:** The Congress.gov API returns committee report text URLs under the key `"text"`, not `"textVersions"` as I initially coded.
**Resolution:** Discovered when reports returned 0 sections. Added fallback: `data.get("textVersions", data.get("text", []))`.

### 2. Reports with 0 sections despite valid HTML
**Problem:** Several reports (DHS House, Energy-Water House, Interior House, Legislative Branch House) returned 0 parsed sections.
**Root cause:** My parser required an "OVERVIEW" heading to start parsing. Some reports skip this and go directly to "TITLE I--..." with description inline.
**Resolution:** Made preamble detection flexible - now triggers on OVERVIEW, SUMMARY, any TITLE pattern, or the first substantive all-caps heading.

### 3. Incorrect Senate report numbers
**Problem:** I initially guessed Senate report numbers and got 4 out of 12 wrong (Agriculture, FSGG, LHHS, MilCon-VA).
**Resolution:** Systematically verified all 12 by querying the Congress.gov API for each report number and checking the returned title. For example, S. Rept. 118-80 (which I'd assigned to Agriculture) was actually an Indian Affairs Committee report.

### 4. Agency search matching "epa" inside "department"
**Problem:** Searching "EPA" in the agency autocomplete returned every department because "department" contains the substring "epa" at position 1.
**Resolution:** Implemented tiered matching: abbreviation match (highest priority) > word-start match > substring match (only for queries 4+ characters).

### 5. Multi-line headings in committee reports
**Problem:** Some agency names span two lines in the report text (e.g., "NATIONAL INSTITUTE OF FOOD AND AGRICULTURE RESEARCH AND EDUCATION\nACTIVITIES"), causing the parser to create two separate, broken sections.
**Resolution:** Added a pre-processing pass that joins consecutive all-caps lines when they appear to form a single heading.

---

## What I Would Do With More Time

1. **FY2025/FY2026 data** - The 119th Congress has begun producing appropriations reports. Adding current-cycle data would make this an operational tool rather than a historical reference.

2. **Conference report / Explanatory Statement coverage** - The enacted law follows the conference report, which is the authoritative document. FY2024 used joint explanatory statements published in the Congressional Record.

3. **CBJ content integration** - Currently links to CBJ PDFs. Fetching and parsing the actual CBJ documents would enable true side-by-side comparison of what the agency requested versus what the committee said.

4. **Program-level cross-referencing** - A staffer working on "Community Development Block Grants" should be able to see every mention across both the CBJ and all committee reports instantly.

5. **Contact stakeholders** - I would have reached out to actual Hill staffers to understand their workflow and pain points, but this was outside the project constraints.

---

## Technical Details

- **Backend:** Python/Flask (~750 lines)
- **Frontend:** Single HTML file with vanilla JS (~500 lines)
- **Data Sources:** USASpending.gov API, Congress.gov API
- **Caching:** File-based JSON cache (24-hour TTL) to avoid repeated API calls
- **Port:** 8097
- **Reports covered:** 22 committee reports (10 House + 12 Senate) across all 12 appropriations subcommittees
- **Agencies mapped:** 90+ federal agencies to their correct subcommittees

---

## Team

- **Main developer:** Claude (me) - designed, researched, built, and iterated
- **DC Reviewer agent:** Role-played as Daniel Schuman (Demand Progress) to provide domain-expert feedback on usability and completeness. Provided two rounds of detailed feedback that drove the search-first redesign, directive extraction feature, and agency autocomplete improvements.
