# CBJ-Approps Report Linker: Implementation Plan

## Problem
Congressional staffers need to cross-reference agency Congressional Budget Justifications (CBJs) with the corresponding sections of appropriations committee reports. Currently this requires manually navigating between different documents and knowing which report sections correspond to which agencies.

## Solution
A web application that:
1. Maps each federal agency to its appropriations subcommittee
2. Fetches and displays the relevant committee report section for each agency
3. Links to the agency's CBJ
4. Provides a side-by-side browsing experience

## Data Sources
- **USASpending.gov API**: Agency list with CBJ URLs (`/api/v2/references/toptier_agencies/`)
- **Congress.gov API**: Committee report metadata and text URLs
- **Congress.gov**: Actual report HTML text (e.g., `congress.gov/118/crpt/hrpt124/generated/CRPT-118hrpt124.htm`)

## Architecture
- **Backend**: Python (Flask) server
  - Fetches agency data from USASpending.gov
  - Fetches committee report text from Congress.gov
  - Parses report text into agency/account sections
  - Caches data to avoid repeated API calls
- **Frontend**: HTML/CSS/JS
  - Browse by appropriations subcommittee → agency → account
  - Side-by-side view: committee report section | CBJ link
  - Search across report sections
  - Clean, professional UI suitable for Hill use

## Key Mapping: Agencies to Appropriations Subcommittees
The 12 subcommittees and their FY2024 House report numbers:

1. Agriculture (H.Rept. 118-124)
2. Commerce, Justice, Science (H.Rept. 118-125)
3. Defense (H.Rept. 118-121)
4. Energy & Water (H.Rept. 118-122)
5. Financial Services & General Government (H.Rept. 118-145)
6. Homeland Security (H.Rept. 118-123)
7. Interior & Environment (H.Rept. 118-126)
8. Labor, HHS, Education (H.Rept. 118-224)
9. Legislative Branch (H.Rept. 118-127)
10. Military Construction, VA (H.Rept. 118-120)
11. State, Foreign Operations (H.Rept. 118-146)
12. Transportation, HUD (H.Rept. 118-150)

## Implementation Steps
1. Build agency-to-subcommittee mapping
2. Create Python backend to fetch and parse data
3. Build the frontend UI
4. Parse committee report HTML into navigable sections
5. Test and polish
6. Get DC feedback and iterate

## Port Selection
Will use port 8097 to avoid conflicts with other projects.
