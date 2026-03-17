#!/usr/bin/env bash
# verify-cover-letter-ats.sh — Verify cover letter PDF is ATS-parseable
# Usage: bash scripts/verify-cover-letter-ats.sh <cover-letter.pdf> [source.tex]
#
# If a .tex source file is provided (or auto-detected), source-level checks run too.

set -euo pipefail

PDF="${1:-}"
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

if [ -z "$PDF" ]; then
  echo "Usage: bash scripts/verify-cover-letter-ats.sh <cover-letter.pdf> [source.tex]"
  exit 1
fi

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
  BASE=$(basename "$PDF" .pdf)
  for candidate in \
    "$(echo "$BASE" | sed 's/Ilyas_Ibragimov_Cover_Letter_/cover-/' | tr '[:upper:]' '[:lower:]').tex" \
    "cover-$(echo "$BASE" | sed 's/Ilyas_Ibragimov_Cover_Letter_//' | tr '[:upper:]' '[:lower:]').tex" \
    "${BASE}.tex"; do
    if [ -f "$candidate" ]; then
      TEX="$candidate"
      break
    fi
  done
fi

echo "=== ATS Cover Letter Verification: $PDF ==="
[ -n "$TEX" ] && echo "    LaTeX source: $TEX"
echo ""

# Extract text
LINEAR=$(pdftotext "$PDF" -)
RAW=$(pdftotext -raw "$PDF" -)

# ============================================================
# Section 1: Filename Format
# ============================================================
echo "--- Filename ---"
BASENAME=$(basename "$PDF")

# Check no spaces in filename
if echo "$BASENAME" | grep -q " "; then
  red "Filename contains spaces — ATS may mangle filename with special characters"
  FAIL=$((FAIL + 1))
else
  green "No spaces in filename"
  PASS=$((PASS + 1))
fi

# Check filename contains Cover and Letter
if echo "$BASENAME" | grep -qi "cover" && echo "$BASENAME" | grep -qi "letter"; then
  green "Filename contains 'Cover Letter'"
  PASS=$((PASS + 1))
else
  yellow "Filename doesn't contain 'Cover Letter' — may not be identified as cover letter by ATS"
  WARN=$((WARN + 1))
fi

# Check only safe characters
if echo "$BASENAME" | grep -qE '^[A-Za-z0-9_.-]+$'; then
  green "Filename uses only safe characters (letters, numbers, underscores, hyphens, dots)"
  PASS=$((PASS + 1))
else
  red "Filename contains special characters — use only letters, numbers, underscores, hyphens"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 2: Contact Info
# ============================================================
echo ""
echo "--- Contact Info ---"
check "Name: Ilyas"                  "Ilyas"                         "$LINEAR"
warn_check "Email"                   "ilyas.ibragimov@outlook.com"   "$LINEAR"
warn_check "Phone number"           "929"                            "$LINEAR"

# ============================================================
# Section 3: Letter Structure
# ============================================================
echo ""
echo "--- Letter Structure ---"

# Check for salutation
if echo "$LINEAR" | grep -qiE "^(Dear|Hi|Hello|To)"; then
  green "Salutation found"
  PASS=$((PASS + 1))
else
  yellow "No salutation found (Dear/Hi/Hello) — expected in business letter format"
  WARN=$((WARN + 1))
fi

# Check for closing
if echo "$LINEAR" | grep -qiE "(Thank you|Sincerely|Regards|Best|Respectfully)"; then
  green "Closing found"
  PASS=$((PASS + 1))
else
  yellow "No closing found — expected in business letter format"
  WARN=$((WARN + 1))
fi

# Check it doesn't contain resume-style section headers (it's a letter, not a resume)
RESUME_HEADERS_FOUND=""
for header in "Work Experience" "Technical Skills" "Education" "Projects" "Certifications"; do
  if echo "$LINEAR" | grep -qi "^$header"; then
    RESUME_HEADERS_FOUND="$RESUME_HEADERS_FOUND $header"
  fi
done
if [ -z "$RESUME_HEADERS_FOUND" ]; then
  green "No resume-style section headers (correct for a cover letter)"
  PASS=$((PASS + 1))
else
  yellow "Found resume-style headers:$RESUME_HEADERS_FOUND — cover letters should be prose, not structured like a resume"
  WARN=$((WARN + 1))
fi

# ============================================================
# Section 4: Content Quality
# ============================================================
echo ""
echo "--- Content Quality ---"

# Word count
WORD_COUNT=$(echo "$LINEAR" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 50 ]; then
  red "Only $WORD_COUNT words extracted — likely a text extraction failure"
  FAIL=$((FAIL + 1))
elif [ "$WORD_COUNT" -lt 150 ]; then
  red "Only $WORD_COUNT words — cover letter is too short for ATS indexing"
  FAIL=$((FAIL + 1))
elif [ "$WORD_COUNT" -lt 200 ]; then
  yellow "$WORD_COUNT words — slightly short (200-400 optimal for ATS + recruiter review)"
  WARN=$((WARN + 1))
elif [ "$WORD_COUNT" -le 400 ]; then
  green "Word count: $WORD_COUNT (optimal 200-400 range)"
  PASS=$((PASS + 1))
elif [ "$WORD_COUNT" -le 500 ]; then
  yellow "$WORD_COUNT words — slightly long (200-400 optimal)"
  WARN=$((WARN + 1))
else
  red "$WORD_COUNT words — too long, recruiters won't read and ATS may truncate"
  FAIL=$((FAIL + 1))
fi

# Company name personalization check
# Try to extract company from filename: Ilyas_Ibragimov_Cover_Letter_<Company>.pdf
COMPANY=$(echo "$BASENAME" | sed -n 's/.*Cover_Letter_\(.*\)\.pdf/\1/p')
if [ -n "$COMPANY" ]; then
  # Handle multi-word company names (CamelCase to space-separated)
  COMPANY_SEARCH=$(echo "$COMPANY" | sed 's/\([a-z]\)\([A-Z]\)/\1 \2/g')
  if echo "$LINEAR" | grep -qi "$COMPANY_SEARCH\|$COMPANY"; then
    green "Company name '$COMPANY' appears in letter body (personalized)"
    PASS=$((PASS + 1))
  else
    red "Company name '$COMPANY' not found in letter body — appears generic"
    FAIL=$((FAIL + 1))
  fi
fi

# ============================================================
# Section 5: PDF Metadata
# ============================================================
echo ""
echo "--- PDF Metadata ---"
if command -v pdfinfo &>/dev/null; then
  META=$(pdfinfo "$PDF" 2>/dev/null || true)

  if echo "$META" | grep -qi "Title.*Ilyas Ibragimov"; then
    green "Metadata: Title contains name"
    PASS=$((PASS + 1))
  else
    yellow "Metadata: Title should contain 'Ilyas Ibragimov'"
    WARN=$((WARN + 1))
  fi

  if echo "$META" | grep -qi "Title.*Cover Letter"; then
    green "Metadata: Title identifies as cover letter"
    PASS=$((PASS + 1))
  else
    yellow "Metadata: Title should contain 'Cover Letter'"
    WARN=$((WARN + 1))
  fi

  if echo "$META" | grep -qi "Author.*Ilyas Ibragimov"; then
    green "Metadata: Author set"
    PASS=$((PASS + 1))
  else
    yellow "Metadata: Author should be 'Ilyas Ibragimov'"
    WARN=$((WARN + 1))
  fi
else
  echo "SKIP: pdfinfo not available (install poppler)"
fi

# ============================================================
# Section 6: PDF Encryption
# ============================================================
echo ""
echo "--- PDF Encryption ---"
if command -v pdfinfo &>/dev/null; then
  ENCRYPTED=$(pdfinfo "$PDF" 2>/dev/null | grep "^Encrypted:" | awk '{print $2}')
  if [ "$ENCRYPTED" = "no" ] || [ -z "$ENCRYPTED" ]; then
    green "PDF is not encrypted"
    PASS=$((PASS + 1))
  else
    red "PDF is encrypted — ATS cannot parse encrypted PDFs"
    FAIL=$((FAIL + 1))
  fi
fi

# ============================================================
# Section 7: Formatting Rules
# ============================================================
echo ""
echo "--- Formatting Rules ---"
check_not "No em dashes (—) in text" "—" "$LINEAR"

# Non-standard bullet characters
if echo "$LINEAR" | perl -ne 'exit 1 if /[\x{2756}\x{2714}\x{2717}\x{25CB}\x{25CF}\x{25A0}\x{25AA}\x{2666}\x{2605}\x{2606}\x{2611}\x{2610}]/' 2>/dev/null; then
  green "No exotic characters"
  PASS=$((PASS + 1))
else
  red "Found non-standard characters — some ATS systems cannot parse these"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 8: Character Encoding
# ============================================================
echo ""
echo "--- Character Encoding ---"
if echo "$LINEAR" | grep -qP '[\x00-\x08\x0e-\x1f]' 2>/dev/null; then
  red "Found control characters (font encoding issue)"
  FAIL=$((FAIL + 1))
else
  green "No garbled/control characters"
  PASS=$((PASS + 1))
fi

if echo "$LINEAR" | perl -ne 'exit 1 if /\x{FFFD}/' 2>/dev/null; then
  green "No Unicode replacement characters (U+FFFD)"
  PASS=$((PASS + 1))
else
  red "Found Unicode replacement characters (U+FFFD) — font mapping failure"
  FAIL=$((FAIL + 1))
fi

# ============================================================
# Section 9: Font Embedding
# ============================================================
echo ""
echo "--- Font Embedding ---"
if command -v pdffonts &>/dev/null; then
  FONT_INFO=$(pdffonts "$PDF" 2>/dev/null || true)

  NOT_EMBEDDED=$(echo "$FONT_INFO" | tail -n +3 | awk '{if ($3 == "no") print $1}')
  if [ -z "$NOT_EMBEDDED" ]; then
    green "All fonts embedded"
    PASS=$((PASS + 1))
  else
    red "Fonts not embedded: $NOT_EMBEDDED"
    FAIL=$((FAIL + 1))
  fi

  NO_UNICODE=$(echo "$FONT_INFO" | tail -n +3 | awk '{if ($5 == "no") print $1}')
  if [ -z "$NO_UNICODE" ]; then
    green "All fonts have Unicode mapping"
    PASS=$((PASS + 1))
  else
    red "Fonts missing Unicode mapping: $NO_UNICODE"
    FAIL=$((FAIL + 1))
  fi

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
# Section 10: Ligature Detection
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

# ============================================================
# Section 11: Image Detection
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
# Section 12: File Size
# ============================================================
echo ""
echo "--- File Size ---"
SIZE=$(stat -f%z "$PDF" 2>/dev/null || stat -c%s "$PDF" 2>/dev/null || echo "0")
KB=$((SIZE / 1024))
if [ "$KB" -gt 5120 ]; then
  red "File size ${KB}KB exceeds 5MB (some ATS systems reject)"
  FAIL=$((FAIL + 1))
elif [ "$KB" -gt 2048 ]; then
  yellow "File size ${KB}KB exceeds 2MB (most ATS accept up to 5MB, but smaller is better)"
  WARN=$((WARN + 1))
else
  green "File size ${KB}KB (well under ATS limits)"
  PASS=$((PASS + 1))
fi

# ============================================================
# Section 13: PDF Version
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
# Section 14: Page Count
# ============================================================
echo ""
echo "--- Document Structure ---"
if command -v pdfinfo &>/dev/null; then
  PAGES=$(pdfinfo "$PDF" 2>/dev/null | grep "^Pages:" | awk '{print $2}')
  if [ "$PAGES" = "1" ]; then
    green "Page count: 1 (correct for cover letter)"
    PASS=$((PASS + 1))
  else
    red "Page count: $PAGES (cover letters must be exactly 1 page)"
    FAIL=$((FAIL + 1))
  fi
fi

# ============================================================
# Section 15: LaTeX Source Checks
# ============================================================
if [ -n "$TEX" ] && [ -f "$TEX" ]; then
  echo ""
  echo "--- LaTeX Source Checks ($TEX) ---"
  TEX_CONTENT=$(cat "$TEX")

  # ATS-critical packages
  if echo "$TEX_CONTENT" | grep -q 'usepackage{cmap}'; then
    green "\\usepackage{cmap} present"
    PASS=$((PASS + 1))
  else
    red "Missing \\usepackage{cmap} — PDF text extraction will be unreliable"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'usepackage\[T1\]{fontenc}'; then
    green "\\usepackage[T1]{fontenc} present"
    PASS=$((PASS + 1))
  else
    red "Missing \\usepackage[T1]{fontenc} — ligatures will break keyword matching"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'input{glyphtounicode}'; then
    green "\\input{glyphtounicode} present"
    PASS=$((PASS + 1))
  else
    red "Missing \\input{glyphtounicode} — characters may not map correctly"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfgentounicode=1'; then
    green "\\pdfgentounicode=1 present"
    PASS=$((PASS + 1))
  else
    red "Missing \\pdfgentounicode=1 — PDF text extraction will produce garbage"
    FAIL=$((FAIL + 1))
  fi

  if echo "$TEX_CONTENT" | grep -q 'pdfminorversion'; then
    green "\\pdfminorversion set (PDF version pinned)"
    PASS=$((PASS + 1))
  else
    yellow "No \\pdfminorversion set — consider \\pdfminorversion=4 for max ATS compatibility"
    WARN=$((WARN + 1))
  fi

  # Multi-column layout (ATS killer)
  if echo "$TEX_CONTENT" | grep -q 'usepackage{multicol}\|\\begin{multicols}'; then
    red "multicol package detected — multi-column layout breaks ATS parsing"
    FAIL=$((FAIL + 1))
  else
    green "No multicol package (single-column layout)"
    PASS=$((PASS + 1))
  fi

  # Em dashes in source
  if echo "$TEX_CONTENT" | grep -q '—'; then
    red "Em dash (—) found in LaTeX source"
    FAIL=$((FAIL + 1))
  else
    green "No em dashes in source"
    PASS=$((PASS + 1))
  fi

  # PDF metadata
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
