#!/usr/bin/env bash
# verify-resume-ats.sh — Verify resume PDF is ATS-parseable
# Usage: bash scripts/verify-resume-ats.sh [resume.pdf]

set -euo pipefail

PDF="${1:-resume.pdf}"
PASS=0
FAIL=0

green() { printf '\033[32m✓ %s\033[0m\n' "$1"; }
red()   { printf '\033[31m✗ %s\033[0m\n' "$1"; }

check() {
  local label="$1" pattern="$2" text="$3"
  if echo "$text" | grep -qi "$pattern"; then
    green "$label"
    PASS=$((PASS + 1))
  else
    red "$label — pattern not found: $pattern"
    FAIL=$((FAIL + 1))
  fi
}

if ! command -v pdftotext &>/dev/null; then
  echo "ERROR: pdftotext not found. Install with: brew install poppler"
  exit 1
fi

if [ ! -f "$PDF" ]; then
  echo "ERROR: $PDF not found"
  exit 1
fi

echo "=== ATS Resume Verification: $PDF ==="
echo ""

# Extract text in both modes
LINEAR=$(pdftotext "$PDF" -)
LAYOUT=$(pdftotext -layout "$PDF" -)

# --- Section 1: Contact Info ---
echo "--- Contact Info ---"
check "Name: ILYAS IBRAGIMOV"       "ILYAS IBRAGIMOV"               "$LINEAR"
check "Email"                        "ilyas.ibragimov@outlook.com"   "$LINEAR"
check "LinkedIn"                     "linkedin.com/in/ilyasi"        "$LINEAR"
check "Website"                      "ilyasi.com"                    "$LINEAR"
check "Location: New York"           "New York"                      "$LINEAR"

# --- Section 2: Section Headers ---
echo ""
echo "--- Section Headers ---"
check "Summary section"              "Summary"                       "$LINEAR"
check "Experience section"           "Experience"                    "$LINEAR"
check "Technical Skills section"     "Technical Skills"              "$LINEAR"
check "Education section"            "Education"                     "$LINEAR"
check "Projects section"             "Projects"                      "$LINEAR"

# --- Section 3: Companies & Dates ---
echo ""
echo "--- Companies & Dates ---"
check "Two Sigma"                    "Two Sigma"                     "$LINEAR"
check "Blueshift Asset Management"   "Blueshift Asset Management"    "$LINEAR"
check "Fidessa"                      "Fidessa"                       "$LINEAR"
check "Date: Nov. 2022"              "Nov. 2022"                     "$LINEAR"
check "Date: Present"                "Present"                       "$LINEAR"

# --- Section 4: Education (critical — this is the fix) ---
echo ""
echo "--- Education (ATS-critical) ---"
check "UCL"                          "University College London"     "$LINEAR"
check "Master of Engineering"        "Master of Engineering"         "$LINEAR"
check "First Class Honors"           "First Class Honors"            "$LINEAR"
check "4.0 GPA"                      "4.0 GPA"                      "$LINEAR"
check "Baruch College"               "Baruch College"                "$LINEAR"
check "Distinction"                  "Distinction"                   "$LINEAR"
check "Brooklyn Technical"           "Brooklyn Technical"            "$LINEAR"

# --- Section 5: Layout mode — field separation ---
echo ""
echo "--- Layout Mode: Field Separation ---"
check "Layout: UCL + London"         "London, UK"                    "$LAYOUT"
check "Layout: Baruch + New York"    "New York, NY"                  "$LAYOUT"
check "Layout: date 2019"            "2019"                          "$LAYOUT"
check "Layout: date 2020"            "2020"                          "$LAYOUT"

# --- Section 6: Skills Keywords ---
echo ""
echo "--- Skills Keywords ---"
check "Python"                       "Python"                        "$LINEAR"
check "BigQuery"                     "BigQuery"                      "$LINEAR"
check "dbt"                          "dbt"                           "$LINEAR"
check "SQL"                          "SQL"                           "$LINEAR"
check "C++"                          "C++"                           "$LINEAR"
check "GCP"                          "GCP"                           "$LINEAR"
check "Claude"                       "Claude"                        "$LINEAR"

# --- Section 7: PDF Metadata ---
echo ""
echo "--- PDF Metadata ---"
if command -v pdfinfo &>/dev/null; then
  META=$(pdfinfo "$PDF" 2>/dev/null || true)
  check "Metadata: Title"           "Ilyas Ibragimov"               "$META"
  check "Metadata: Author"          "Ilyas Ibragimov"               "$META"
  check "Metadata: Keywords"        "Software Engineer"             "$META"
else
  echo "SKIP: pdfinfo not available (install poppler)"
fi

# --- Section 8: Garbled Characters ---
echo ""
echo "--- Character Encoding ---"
if echo "$LINEAR" | grep -qP '[\x00-\x08\x0e-\x1f]' 2>/dev/null; then
  red "Found control characters (font encoding issue)"
  FAIL=$((FAIL + 1))
else
  green "No garbled/control characters"
  PASS=$((PASS + 1))
fi

# --- Section 9: Page Count ---
echo ""
echo "--- Document Structure ---"
if command -v pdfinfo &>/dev/null; then
  PAGES=$(pdfinfo "$PDF" 2>/dev/null | grep "^Pages:" | awk '{print $2}')
  if [ "$PAGES" = "2" ]; then
    green "Page count: 2"
    PASS=$((PASS + 1))
  else
    red "Page count: $PAGES (expected 2)"
    FAIL=$((FAIL + 1))
  fi
fi

# --- Summary ---
echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  echo "STATUS: FAIL"
  exit 1
else
  echo "STATUS: PASS"
  exit 0
fi
