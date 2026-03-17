#!/usr/bin/env bash
# verify-resume-ats.sh — Verify resume PDF is ATS-parseable and well-formatted
# Usage: bash scripts/verify-resume-ats.sh [resume.pdf] [source.tex]
#
# If a .tex source file is provided (or auto-detected), source-level checks run too.

set -euo pipefail

PDF="${1:-resume.pdf}"
TEX="${2:-}"
PASS=0
FAIL=0
WARN=0

green()  { printf '\033[32m✓ %s\033[0m\n' "$1"; }
red()    { printf '\033[31m✗ %s\033[0m\n' "$1"; }
yellow() { printf '\033[33m⚠ %s\033[0m\n' "$1"; }

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

check_not() {
  local label="$1" pattern="$2" text="$3"
  if echo "$text" | grep -qi "$pattern"; then
    red "$label"
    FAIL=$((FAIL + 1))
  else
    green "$label"
    PASS=$((PASS + 1))
  fi
}

warn_check() {
  local label="$1" pattern="$2" text="$3"
  if echo "$text" | grep -qi "$pattern"; then
    green "$label"
    PASS=$((PASS + 1))
  else
    yellow "$label — pattern not found: $pattern"
    WARN=$((WARN + 1))
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

# Auto-detect .tex source if not provided
if [ -z "$TEX" ]; then
  # Try to find matching .tex file based on PDF name
  BASE=$(basename "$PDF" .pdf)
  for candidate in \
    "${BASE}.tex" \
    "$(echo "$BASE" | sed 's/Ilyas_Ibragimov_Resume_/resume-/' | tr '[:upper:]' '[:lower:]').tex" \
    "resume-$(echo "$BASE" | sed 's/Ilyas_Ibragimov_Resume_//' | tr '[:upper:]' '[:lower:]').tex" \
    "resume.tex"; do
    if [ -f "$candidate" ]; then
      TEX="$candidate"
      break
    fi
  done
fi

echo "=== ATS Resume Verification: $PDF ==="
[ -n "$TEX" ] && echo "    LaTeX source: $TEX"
echo ""

# Extract text in multiple modes
LINEAR=$(pdftotext "$PDF" -)
LAYOUT=$(pdftotext -layout "$PDF" -)
RAW=$(pdftotext -raw "$PDF" -)

# ============================================================
# Section 1: Contact Info
# ============================================================
echo "--- Contact Info ---"
check "Name: ILYAS IBRAGIMOV"       "ILYAS IBRAGIMOV"               "$LINEAR"
check "Email"                        "ilyas.ibragimov@outlook.com"   "$LINEAR"
check "LinkedIn"                     "linkedin.com/in/ilyasi"        "$LINEAR"
check "Website"                      "ilyasi.com"                    "$LINEAR"
check "Location: New York"           "New York"                      "$LINEAR"

# ============================================================
# Section 2: Contact Info Position (must appear before any section header)
# ============================================================
echo ""
echo "--- Contact Info Position ---"
# Verify contact info appears in the first N lines, before section headers
# This ensures it's in the document body, not hidden in a header/footer
FIRST_SECTION_LINE=$(echo "$LINEAR" | grep -n "Summary\|Experience\|Technical Skills\|Education\|Projects" | head -1 | cut -d: -f1)
if [ -n "$FIRST_SECTION_LINE" ]; then
  CONTACT_AREA=$(echo "$LINEAR" | head -n "$((FIRST_SECTION_LINE - 1))")
  if echo "$CONTACT_AREA" | grep -qi "ILYAS IBRAGIMOV"; then
    green "Name appears before first section header (in body, not header/footer)"
    PASS=$((PASS + 1))
  else
    red "Name not found before first section header — may be in PDF header (ATS skips headers/footers)"
    FAIL=$((FAIL + 1))
  fi
  if echo "$CONTACT_AREA" | grep -qi "ilyas.ibragimov@outlook.com"; then
    green "Email appears before first section header"
    PASS=$((PASS + 1))
  else
    red "Email not found before first section header"
    FAIL=$((FAIL + 1))
  fi
else
  yellow "Could not determine first section position"
  WARN=$((WARN + 1))
fi

# ============================================================
# Section 3: Section Headers
# ============================================================
echo ""
echo "--- Section Headers ---"
check "Summary section"              "Summary"                       "$LINEAR"
check "Experience section"           "Experience"                    "$LINEAR"
check "Technical Skills section"     "Technical Skills"              "$LINEAR"
check "Education section"            "Education"                     "$LINEAR"
warn_check "Projects section"        "Projects"                      "$LINEAR"

# ============================================================
# Section 4: Section Header Whitelist
# ============================================================
echo ""
echo "--- Section Header Whitelist ---"
# Extract lines that look like section headers (all-caps or title case, short, standalone)
# Check that all section headers are ATS-recognized names
ATS_HEADERS="Summary|Professional Summary|Experience|Work Experience|Technical Skills|Skills|Education|Projects|Certifications|Certificates|Awards|Honors|Publications|Languages|Interests|Activities|Volunteer"
# Find section headers from the LaTeX source if available
if [ -n "$TEX" ] && [ -f "$TEX" ]; then
  SECTIONS_IN_TEX=$(grep '\\section{' "$TEX" | sed 's/.*\\section{\(.*\)}.*/\1/' | tr '\n' '|' | sed 's/|$//')
  NON_STANDARD=""
  while IFS= read -r section; do
    if ! echo "$section" | grep -qiE "^($ATS_HEADERS)$"; then
      NON_STANDARD="$NON_STANDARD $section"
    fi
  done < <(grep '\\section{' "$TEX" | sed 's/.*\\section{\(.*\)}.*/\1/')
  if [ -z "$NON_STANDARD" ]; then
    green "All section headers are ATS-recognized names"
    PASS=$((PASS + 1))
  else
    red "Non-standard section headers found:$NON_STANDARD"
    FAIL=$((FAIL + 1))
  fi
else
  yellow "No .tex source found — skipping section header whitelist check"
  WARN=$((WARN + 1))
fi

# ============================================================
# Section 5: Companies & Dates
# ============================================================
echo ""
echo "--- Companies & Dates ---"
check "Two Sigma"                    "Two Sigma"                     "$LINEAR"
check "Blueshift Asset Management"   "Blueshift Asset Management"    "$LINEAR"
check "Fidessa"                      "Fidessa"                       "$LINEAR"
check "Date: Nov. 2022"              "Nov. 2022"                     "$LINEAR"
check "Date: Present"                "Present"                       "$LINEAR"

# ============================================================
# Section 6: Date Format Consistency
# ============================================================
echo ""
echo "--- Date Format Consistency ---"
# Check for "Current" or "Now" instead of "Present"
if echo "$LINEAR" | grep -qiw "Current"; then
  red "Found 'Current' — ATS prefers 'Present' for ongoing roles"
  FAIL=$((FAIL + 1))
else
  green "No 'Current' found (uses 'Present' correctly)"
  PASS=$((PASS + 1))
fi

# Check for two-digit years (common ATS parsing failure)
if echo "$LINEAR" | perl -ne '$f=1 if /(?<!\d)'"'"'[0-9]{2}(?!\d)/; END{exit($f?0:1)}' 2>/dev/null; then
  red "Found two-digit year format — ATS cannot calculate experience duration"
  FAIL=$((FAIL + 1))
else
  green "No two-digit years found"
  PASS=$((PASS + 1))
fi

# Verify dates follow consistent format (Mon. YYYY or YYYY)
DATE_COUNT=$(echo "$LINEAR" | perl -ne 'while (/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4}/g) { $c++ } END { print $c // 0 }' 2>/dev/null)
YEAR_ONLY_COUNT=$(echo "$LINEAR" | perl -ne 'while (/\b(20[0-2]\d|201\d)\b/g) { $c++ } END { print $c // 0 }' 2>/dev/null)
if [ "$DATE_COUNT" -gt 0 ]; then
  green "Found $DATE_COUNT dates in standard Mon. YYYY format"
  PASS=$((PASS + 1))
else
  red "No dates in standard Mon. YYYY format found"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 7: Education (ATS-critical)
# ============================================================
echo ""
echo "--- Education (ATS-critical) ---"
check "UCL"                          "University College London"     "$LINEAR"
check "Master of Engineering"        "Master of Engineering"         "$LINEAR"
check "Bachelor of Engineering"      "Bachelor of Engineering"       "$LINEAR"
check "First Class Honors"           "First Class Honors"            "$LINEAR"
check "4.0 GPA"                      "4.0 GPA"                      "$LINEAR"
check "Baruch College"               "Baruch College"                "$LINEAR"
check "Distinction"                  "Distinction"                   "$LINEAR"
warn_check "Brooklyn Technical"      "Brooklyn Technical"            "$LINEAR"

# ============================================================
# Section 8: Education Date Ranges
# ============================================================
echo ""
echo "--- Education Date Ranges ---"
check "UCL MEng dates"               "2018.*2019"                    "$LAYOUT"
check "UCL BEng dates"               "2015.*2018"                    "$LAYOUT"
warn_check "BTHS dates"              "2011.*2015"                    "$LAYOUT"
check "Baruch date"                  "2020"                          "$LAYOUT"

# ============================================================
# Section 9: Layout — Page 1 Content
# ============================================================
echo ""
echo "--- Page 1 Layout ---"
PAGE1=$(pdftotext -layout "$PDF" - 2>/dev/null | awk '/\f/{exit} {print}')
check "Skills on page 1"            "Technical Skills"              "$PAGE1"
check "Education on page 1"         "Education"                     "$PAGE1"
check "Experience on page 1"        "Experience"                    "$PAGE1"

# ============================================================
# Section 10: Layout Quality
# ============================================================
echo ""
echo "--- Layout Quality ---"
SKILLS_SECTION=$(echo "$LAYOUT" | awk '/Technical Skills/{found=1; next} found && /\f/{exit} found && /Projects/{exit} found{print}')
SKILLS_LINES=$(echo "$SKILLS_SECTION" | grep -c "^" || true)
if [ "$SKILLS_LINES" -le 7 ]; then
  green "Skills section fits cleanly ($SKILLS_LINES lines)"
  PASS=$((PASS + 1))
else
  red "Skills section may have wrapping lines ($SKILLS_LINES lines, expected ≤7)"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 11: Skills Keywords
# ============================================================
echo ""
echo "--- Skills Keywords ---"
check "Python"                       "Python"                        "$LINEAR"
check "BigQuery"                     "BigQuery"                      "$LINEAR"
check "dbt"                          "dbt"                           "$LINEAR"
check "SQL"                          "SQL"                           "$LINEAR"
check "C++"                          "C++"                           "$LINEAR"
check "GCP"                          "GCP"                           "$LINEAR"
check "Claude"                       "Claude"                        "$LINEAR"
check "GenAI"                        "GenAI"                         "$LINEAR"
check "AI Pipelines"                 "AI Pipelines"                  "$LINEAR"
check "Vertex AI"                    "Vertex AI"                     "$LINEAR"

# ============================================================
# Section 12: Acronym / Full-Form Pairing
# ============================================================
echo ""
echo "--- Acronym / Full-Form Pairing ---"
# ATS (especially Lever) doesn't match acronyms to full forms.
# Both must appear for maximum keyword coverage.
ACRONYM_PAIRS=(
  "GCP:Google Cloud"
  "CI/CD:Continuous Integration\|Continuous Delivery\|CI/CD"
  "ELT:ELT\|Extract.*Load.*Transform"
)
for pair in "${ACRONYM_PAIRS[@]}"; do
  ACRONYM="${pair%%:*}"
  FULL_FORM="${pair#*:}"
  if echo "$LINEAR" | grep -qi "$ACRONYM"; then
    # Only check full form if acronym is present
    if echo "$LINEAR" | grep -qiE "$FULL_FORM"; then
      green "Both '$ACRONYM' and full form found"
      PASS=$((PASS + 1))
    else
      yellow "'$ACRONYM' found but full form not present (Lever ATS won't match searches for full name)"
      WARN=$((WARN + 1))
    fi
  fi
done

# ============================================================
# Section 13: PDF Metadata
# ============================================================
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

# ============================================================
# Section 14: PDF Encryption
# ============================================================
echo ""
echo "--- PDF Encryption ---"
if command -v pdfinfo &>/dev/null; then
  ENCRYPTED=$(pdfinfo "$PDF" 2>/dev/null | grep "^Encrypted:" | awk '{print $2}')
  if [ "$ENCRYPTED" = "no" ]; then
    green "PDF is not encrypted (ATS can parse)"
    PASS=$((PASS + 1))
  elif [ -z "$ENCRYPTED" ]; then
    green "No encryption detected"
    PASS=$((PASS + 1))
  else
    red "PDF is encrypted — ATS cannot parse encrypted PDFs"
    FAIL=$((FAIL + 1))
  fi
else
  echo "SKIP: pdfinfo not available"
fi

# ============================================================
# Section 15: Formatting Rules
# ============================================================
echo ""
echo "--- Formatting Rules ---"
check_not "No em dashes (—) in text"   "—"                         "$LINEAR"

# Check for non-standard bullet characters
if echo "$LINEAR" | perl -ne 'exit 1 if /[\x{2756}\x{2714}\x{2717}\x{25CB}\x{25CF}\x{25A0}\x{25AA}\x{2666}\x{2605}\x{2606}\x{2611}\x{2610}]/' 2>/dev/null; then
  green "No exotic bullet characters (using standard bullets)"
  PASS=$((PASS + 1))
else
  red "Found non-standard bullet characters — some ATS systems cannot parse these"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 16: Character Encoding
# ============================================================
echo ""
echo "--- Character Encoding ---"
if echo "$LINEAR" | perl -ne '$f=1 if /[\x00-\x08\x0e-\x1f]/; END{exit($f?0:1)}' 2>/dev/null; then
  red "Found control characters (font encoding issue)"
  FAIL=$((FAIL + 1))
else
  green "No garbled/control characters"
  PASS=$((PASS + 1))
fi

# Check for Unicode replacement characters (U+FFFD)
if echo "$LINEAR" | perl -ne 'exit 1 if /\x{FFFD}/' 2>/dev/null; then
  green "No Unicode replacement characters (U+FFFD)"
  PASS=$((PASS + 1))
else
  red "Found Unicode replacement characters (U+FFFD) — font mapping failure"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 17: Content Density
# ============================================================
echo ""
echo "--- Content Density ---"
WORD_COUNT=$(echo "$LINEAR" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 50 ]; then
  red "Only $WORD_COUNT words extracted — likely a text extraction failure (image-based PDF?)"
  FAIL=$((FAIL + 1))
elif [ "$WORD_COUNT" -lt 200 ]; then
  yellow "Only $WORD_COUNT words extracted — resume may be too sparse for ATS ranking"
  WARN=$((WARN + 1))
else
  green "Content density OK ($WORD_COUNT words extracted)"
  PASS=$((PASS + 1))
fi

# ============================================================
# Section 18: Font Embedding
# ============================================================
echo ""
echo "--- Font Embedding ---"
if command -v pdffonts &>/dev/null; then
  FONT_INFO=$(pdffonts "$PDF" 2>/dev/null || true)

  # Check all fonts are embedded
  NOT_EMBEDDED=$(echo "$FONT_INFO" | tail -n +3 | awk '{if ($3 == "no") print $1}')
  if [ -z "$NOT_EMBEDDED" ]; then
    green "All fonts embedded"
    PASS=$((PASS + 1))
  else
    red "Fonts not embedded: $NOT_EMBEDDED"
    FAIL=$((FAIL + 1))
  fi

  # Check all fonts have Unicode mapping
  NO_UNICODE=$(echo "$FONT_INFO" | tail -n +3 | awk '{if ($5 == "no") print $1}')
  if [ -z "$NO_UNICODE" ]; then
    green "All fonts have Unicode mapping"
    PASS=$((PASS + 1))
  else
    red "Fonts missing Unicode mapping: $NO_UNICODE"
    FAIL=$((FAIL + 1))
  fi

  # Check for Type 3 fonts (bitmap, unreliable for text extraction)
  if echo "$FONT_INFO" | tail -n +3 | grep -q "Type 3"; then
    red "Type 3 (bitmap) fonts detected — unreliable for ATS text extraction"
    FAIL=$((FAIL + 1))
  else
    green "No Type 3 bitmap fonts"
    PASS=$((PASS + 1))
  fi
else
  echo "SKIP: pdffonts not available (install poppler)"
fi

# ============================================================
# Section 19: Ligature Detection
# ============================================================
echo ""
echo "--- Ligature Detection ---"
if echo "$LINEAR" | perl -ne 'exit 1 if /[\x{FB00}-\x{FB04}]/' 2>/dev/null; then
  green "No ligature codepoints (fi/fl/ff extract as separate chars)"
  PASS=$((PASS + 1))
else
  red "Found ligature codepoints (U+FB00-FB04) — keywords with fi/fl/ff may not match"
  FAIL=$((FAIL + 1))
fi

# Verify words containing common ligature pairs extract correctly
LIGATURE_FAIL=0
for word in file first office platform effective financial; do
  if ! echo "$LINEAR" | grep -qi "$word" 2>/dev/null; then
    LIGATURE_FAIL=1
    break
  fi
done
if [ "$LIGATURE_FAIL" -eq 0 ]; then
  green "Ligature words extract correctly (file, first, office, etc.)"
  PASS=$((PASS + 1))
else
  yellow "Some ligature test words not found (may not be in this resume)"
  WARN=$((WARN + 1))
fi

# ============================================================
# Section 20: Image Detection
# ============================================================
echo ""
echo "--- Image Detection ---"
if command -v pdfimages &>/dev/null; then
  IMAGE_COUNT=$(pdfimages -list "$PDF" 2>/dev/null | tail -n +3 | wc -l | tr -d ' ')
  if [ "$IMAGE_COUNT" -eq 0 ]; then
    green "No raster images (text-only PDF)"
    PASS=$((PASS + 1))
  else
    red "Found $IMAGE_COUNT raster image(s) — ATS cannot read text in images"
    FAIL=$((FAIL + 1))
  fi
else
  echo "SKIP: pdfimages not available (install poppler)"
fi

# ============================================================
# Section 21: Hyperlinks
# ============================================================
echo ""
echo "--- Hyperlinks ---"
if command -v pdftohtml &>/dev/null; then
  LINKS=$(pdftohtml -stdout -noframes -i "$PDF" 2>/dev/null | grep -o 'href="[^"]*"' || true)
  if echo "$LINKS" | grep -q "linkedin.com"; then
    green "LinkedIn URL is a clickable hyperlink"
    PASS=$((PASS + 1))
  else
    red "LinkedIn URL is not hyperlinked"
    FAIL=$((FAIL + 1))
  fi
  if echo "$LINKS" | grep -q "ilyasi.com"; then
    green "Website URL is a clickable hyperlink"
    PASS=$((PASS + 1))
  else
    red "Website URL is not hyperlinked"
    FAIL=$((FAIL + 1))
  fi
  if echo "$LINKS" | grep -q "mailto:"; then
    green "Email is a clickable mailto: link"
    PASS=$((PASS + 1))
  else
    yellow "Email is not a mailto: hyperlink"
    WARN=$((WARN + 1))
  fi
else
  echo "SKIP: pdftohtml not available (install poppler)"
fi

# ============================================================
# Section 22: Text Ordering
# ============================================================
echo ""
echo "--- Text Ordering ---"
NORMAL_ORDER=$(echo "$LINEAR" | grep -o "Summary\|Experience\|Technical Skills\|Education\|Projects" | head -5)
RAW_ORDER=$(echo "$RAW" | grep -o "Summary\|Experience\|Technical Skills\|Education\|Projects" | head -5)
if [ "$NORMAL_ORDER" = "$RAW_ORDER" ]; then
  green "Section order consistent across extraction modes"
  PASS=$((PASS + 1))
else
  red "Section order differs between normal and raw extraction — layout may confuse ATS"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 23: Section Ordering
# ============================================================
echo ""
echo "--- Section Order ---"
SECTION_ORDER_OK=1
LAST_POS=0
for section in "Summary" "Experience" "Education" "Technical Skills"; do
  POS=$(echo "$LINEAR" | grep -n "$section" | head -1 | cut -d: -f1)
  if [ -z "$POS" ]; then
    red "Section '$section' not found in expected order"
    FAIL=$((FAIL + 1))
    SECTION_ORDER_OK=0
  elif [ "$POS" -lt "$LAST_POS" ]; then
    red "'$section' appears before previous section (unexpected order)"
    FAIL=$((FAIL + 1))
    SECTION_ORDER_OK=0
  fi
  LAST_POS=${POS:-$LAST_POS}
done
if [ "$SECTION_ORDER_OK" -eq 1 ]; then
  green "Sections in standard ATS order (Summary → Experience → Education → Skills)"
  PASS=$((PASS + 1))
fi

# ============================================================
# Section 24: File Size
# ============================================================
echo ""
echo "--- File Size ---"
SIZE=$(stat -f%z "$PDF" 2>/dev/null || stat -c%s "$PDF" 2>/dev/null || echo "0")
KB=$((SIZE / 1024))
if [ "$KB" -gt 2048 ]; then
  red "File size ${KB}KB exceeds 2MB ATS upload limit"
  FAIL=$((FAIL + 1))
elif [ "$KB" -gt 500 ]; then
  yellow "File size ${KB}KB exceeds 500KB (some job boards reject >500KB)"
  WARN=$((WARN + 1))
else
  green "File size ${KB}KB (well under ATS limits)"
  PASS=$((PASS + 1))
fi

# ============================================================
# Section 25: PDF Version
# ============================================================
echo ""
echo "--- PDF Version ---"
if command -v pdfinfo &>/dev/null; then
  PDF_VER=$(pdfinfo "$PDF" 2>/dev/null | grep "PDF version:" | awk '{print $3}')
  case "$PDF_VER" in
    1.[0-7])
      green "PDF version $PDF_VER (good ATS compatibility)"
      PASS=$((PASS + 1))
      ;;
    2.0)
      red "PDF version 2.0 (poor ATS compatibility, use \\pdfminorversion=4)"
      FAIL=$((FAIL + 1))
      ;;
    *)
      yellow "PDF version $PDF_VER (unknown compatibility)"
      WARN=$((WARN + 1))
      ;;
  esac
fi

# ============================================================
# Section 26: PDF Accessibility
# ============================================================
echo ""
echo "--- PDF Accessibility ---"
if command -v pdfinfo &>/dev/null; then
  TAGGED=$(pdfinfo "$PDF" 2>/dev/null | grep "^Tagged:" | awk '{print $2}')
  if [ "$TAGGED" = "yes" ]; then
    green "PDF is tagged (optimal ATS parsing)"
    PASS=$((PASS + 1))
  else
    yellow "PDF is not tagged (informational — hard to fix in LaTeX, but tagged PDFs parse better)"
    WARN=$((WARN + 1))
  fi
fi

# ============================================================
# Section 27: Page Count
# ============================================================
echo ""
echo "--- Document Structure ---"
if command -v pdfinfo &>/dev/null; then
  PAGES=$(pdfinfo "$PDF" 2>/dev/null | grep "^Pages:" | awk '{print $2}')
  if [ "$PAGES" = "1" ] || [ "$PAGES" = "2" ]; then
    green "Page count: $PAGES"
    PASS=$((PASS + 1))
  elif [ "$PAGES" = "3" ]; then
    red "Page count: $PAGES (too long — aim for 1-2 pages)"
    FAIL=$((FAIL + 1))
  else
    red "Page count: $PAGES (expected 1-2)"
    FAIL=$((FAIL + 1))
  fi
fi

# ============================================================
# Section 28: LaTeX Source Validation
# ============================================================
if [ -n "$TEX" ] && [ -f "$TEX" ]; then
  echo ""
  echo "--- LaTeX Source Checks ($TEX) ---"
  TEX_CONTENT=$(cat "$TEX")

  # ATS-critical packages
  if echo "$TEX_CONTENT" | grep -q 'usepackage{cmap}'; then
    green "\\usepackage{cmap} present (CMap tables for text extraction)"
    PASS=$((PASS + 1))
  else
    red "Missing \\usepackage{cmap} — PDF text extraction will be unreliable"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'usepackage\[T1\]{fontenc}'; then
    green "\\usepackage[T1]{fontenc} present (proper ligature handling)"
    PASS=$((PASS + 1))
  else
    red "Missing \\usepackage[T1]{fontenc} — ligatures will break keyword matching"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'input{glyphtounicode}'; then
    green "\\input{glyphtounicode} present (glyph-to-Unicode mapping)"
    PASS=$((PASS + 1))
  else
    red "Missing \\input{glyphtounicode} — characters may not map correctly"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfgentounicode=1'; then
    green "\\pdfgentounicode=1 present (Unicode generation enabled)"
    PASS=$((PASS + 1))
  else
    red "Missing \\pdfgentounicode=1 — PDF text extraction will produce garbage"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfminorversion'; then
    green "\\pdfminorversion set (PDF version pinned for ATS compatibility)"
    PASS=$((PASS + 1))
  else
    yellow "No \\pdfminorversion set — consider \\pdfminorversion=4 for max ATS compatibility"
    WARN=$((WARN + 1))
  fi

  # Check for multi-column layout packages (ATS killers)
  if echo "$TEX_CONTENT" | grep -q 'usepackage{multicol}\|\\begin{multicols}'; then
    red "multicol package detected — multi-column layout breaks ATS parsing"
    FAIL=$((FAIL + 1))
  else
    green "No multicol package (single-column layout)"
    PASS=$((PASS + 1))
  fi

  # Check for em dashes in source
  if echo "$TEX_CONTENT" | grep -q '—'; then
    red "Em dash (—) found in LaTeX source"
    FAIL=$((FAIL + 1))
  else
    green "No em dashes in source"
    PASS=$((PASS + 1))
  fi

  # Check PDF metadata is set
  if echo "$TEX_CONTENT" | grep -q 'pdftitle='; then
    green "PDF title metadata set"
    PASS=$((PASS + 1))
  else
    yellow "No pdftitle set — missing metadata reduces ATS confidence"
    WARN=$((WARN + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfauthor='; then
    green "PDF author metadata set"
    PASS=$((PASS + 1))
  else
    yellow "No pdfauthor set"
    WARN=$((WARN + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfkeywords='; then
    green "PDF keywords metadata set"
    PASS=$((PASS + 1))
  else
    yellow "No pdfkeywords set — adding keywords improves ATS indexing"
    WARN=$((WARN + 1))
  fi
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed, $WARN warnings"
if [ "$FAIL" -gt 0 ]; then
  echo "STATUS: FAIL"
  exit 1
else
  echo "STATUS: PASS"
  exit 0
fi
