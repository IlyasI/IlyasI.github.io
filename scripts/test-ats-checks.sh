#!/usr/bin/env bash
# test-ats-checks.sh — Tests for resume and cover letter ATS verification scripts
# Usage: bash scripts/test-ats-checks.sh
#
# Creates intentionally bad LaTeX files, compiles them, and verifies the
# verification scripts correctly catch each class of issue.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR=$(mktemp -d)
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

cleanup() { rm -rf "$TEST_DIR"; }
trap cleanup EXIT

green()  { printf '\033[32m  PASS: %s\033[0m\n' "$1"; }
red()    { printf '\033[31m  FAIL: %s\033[0m\n' "$1"; }
header() { printf '\n\033[1;36m=== %s ===\033[0m\n' "$1"; }

assert_pass() {
  local desc="$1"; shift
  TESTS_RUN=$((TESTS_RUN + 1))
  if "$@" >/dev/null 2>&1; then
    green "$desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    red "$desc"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

assert_fail() {
  local desc="$1"; shift
  TESTS_RUN=$((TESTS_RUN + 1))
  if "$@" >/dev/null 2>&1; then
    red "$desc (expected failure but got success)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  else
    green "$desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  fi
}

assert_output_contains() {
  local desc="$1" pattern="$2"; shift 2
  TESTS_RUN=$((TESTS_RUN + 1))
  local output
  output=$("$@" 2>&1 || true)
  if echo "$output" | grep -q "$pattern"; then
    green "$desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    red "$desc — expected output to contain: $pattern"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

# Helper: compile a .tex file to PDF in the test directory
compile_tex() {
  local texfile="$1"
  local jobname="${2:-test-output}"
  (cd "$TEST_DIR" && pdflatex -interaction=nonstopmode -jobname="$jobname" "$texfile" >/dev/null 2>&1) || true
}

# ============================================================
header "Prerequisites"
# ============================================================

assert_pass "pdftotext available" command -v pdftotext
assert_pass "pdfinfo available" command -v pdfinfo
assert_pass "pdffonts available" command -v pdffonts
assert_pass "pdfimages available" command -v pdfimages
assert_pass "pdftohtml available" command -v pdftohtml
assert_pass "pdflatex available" command -v pdflatex
assert_pass "Resume verify script exists" test -f "$SCRIPT_DIR/verify-resume-ats.sh"
assert_pass "Cover letter verify script exists" test -f "$SCRIPT_DIR/verify-cover-letter-ats.sh"

# ============================================================
header "Resume Script: Missing File Handling"
# ============================================================

assert_fail "Fails on nonexistent PDF" bash "$SCRIPT_DIR/verify-resume-ats.sh" "/tmp/nonexistent_resume_42.pdf"

# ============================================================
header "Resume Script: Real CLEAR Resume (Regression)"
# ============================================================

if [ -f "$REPO_DIR/Ilyas_Ibragimov_Resume_CLEAR.pdf" ]; then
  assert_pass "CLEAR resume passes all checks" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$REPO_DIR/Ilyas_Ibragimov_Resume_CLEAR.pdf" "$REPO_DIR/resume-clear.tex"
else
  echo "  SKIP: Ilyas_Ibragimov_Resume_CLEAR.pdf not found (run 'make resume-clear' first)"
fi

# ============================================================
header "Cover Letter Script: Missing File Handling"
# ============================================================

assert_fail "Fails on nonexistent PDF" bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "/tmp/nonexistent_cover_42.pdf"
assert_fail "Fails with no arguments" bash "$SCRIPT_DIR/verify-cover-letter-ats.sh"

# ============================================================
header "Cover Letter Script: Real CLEAR Cover Letter (Regression)"
# ============================================================

if [ -f "$REPO_DIR/Ilyas_Ibragimov_Cover_Letter_CLEAR.pdf" ]; then
  assert_pass "CLEAR cover letter passes all checks" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$REPO_DIR/Ilyas_Ibragimov_Cover_Letter_CLEAR.pdf" "$REPO_DIR/cover-clear.tex"
else
  echo "  SKIP: Ilyas_Ibragimov_Cover_Letter_CLEAR.pdf not found (run 'make cover-clear' first)"
fi

# ============================================================
header "Resume Script: Missing LaTeX ATS Packages"
# ============================================================

# Create a resume missing cmap, glyphtounicode, pdfgentounicode
cat > "$TEST_DIR/bad-resume-no-packages.tex" << 'TEXEOF'
\documentclass[letterpaper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Senior Software Engineer},
  pdfauthor={Ilyas Ibragimov},
  pdfkeywords={Software Engineer, Python}
}
\begin{document}
\begin{center}
\textbf{\huge ILYAS IBRAGIMOV} \\
New York, NY | ilyas.ibragimov@outlook.com | linkedin.com/in/ilyasi | ilyasi.com
\end{center}
\section{Summary}
Software engineer with 6+ years experience. Python, BigQuery, dbt, SQL, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI.
\section{Experience}
\textbf{Two Sigma} \hfill Nov. 2022 -- Present \\
Senior Software Developer \\
Built systems. Google Cloud Platform (GCP). CI/CD.
\textbf{Blueshift Asset Management} \hfill Jan. 2020 -- Nov. 2022 \\
Software Developer
\textbf{Fidessa} \hfill July 2018 -- Sep. 2018 \\
Platform Development Intern
\section{Education}
University College London (UCL) \\
Master of Engineering \hfill 2018 -- 2019 \\
Bachelor of Engineering \hfill 2015 -- 2018 \\
First Class Honors, 4.0 GPA \\
Baruch College MFE Program, Distinction \hfill 2020 \\
Brooklyn Technical High School \hfill 2011 -- 2015
\section{Technical Skills}
Python, Java, SQL, BigQuery, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI, dbt
\section{Projects}
Deep Learning project.
\end{document}
TEXEOF

compile_tex "$TEST_DIR/bad-resume-no-packages.tex" "bad-resume-no-packages"

if [ -f "$TEST_DIR/bad-resume-no-packages.pdf" ]; then
  assert_output_contains "Detects missing cmap" "Missing.*cmap" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-no-packages.pdf" "$TEST_DIR/bad-resume-no-packages.tex"
  assert_output_contains "Detects missing glyphtounicode" "Missing.*glyphtounicode" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-no-packages.pdf" "$TEST_DIR/bad-resume-no-packages.tex"
  assert_output_contains "Detects missing pdfgentounicode" "Missing.*pdfgentounicode" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-no-packages.pdf" "$TEST_DIR/bad-resume-no-packages.tex"
  assert_output_contains "Detects missing pdfminorversion" "pdfminorversion" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-no-packages.pdf" "$TEST_DIR/bad-resume-no-packages.tex"
  assert_fail "Fails overall when ATS packages missing" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-no-packages.pdf" "$TEST_DIR/bad-resume-no-packages.tex"
else
  echo "  SKIP: bad-resume-no-packages.pdf failed to compile"
fi

# ============================================================
header "Resume Script: Em Dash Detection"
# ============================================================

cat > "$TEST_DIR/bad-resume-emdash.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[letterpaper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{cmap}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Senior Software Engineer},
  pdfauthor={Ilyas Ibragimov},
  pdfkeywords={Software Engineer, Python}
}
\pdfgentounicode=1
\begin{document}
\begin{center}
\textbf{\huge ILYAS IBRAGIMOV} \\
New York, NY | ilyas.ibragimov@outlook.com | linkedin.com/in/ilyasi | ilyasi.com
\end{center}
\section{Summary}
Software engineer — building systems. Python, BigQuery, dbt, SQL, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI.
\section{Experience}
\textbf{Two Sigma} \hfill Nov. 2022 -- Present \\
Senior Software Developer \\
Built systems.
\textbf{Blueshift Asset Management} \hfill Jan. 2020 -- Nov. 2022 \\
Software Developer
\textbf{Fidessa} \hfill July 2018 -- Sep. 2018 \\
Intern
\section{Education}
University College London (UCL) \\
Master of Engineering \hfill 2018 -- 2019 \\
Bachelor of Engineering \hfill 2015 -- 2018 \\
First Class Honors, 4.0 GPA \\
Baruch College, Distinction \hfill 2020 \\
Brooklyn Technical High School \hfill 2011 -- 2015
\section{Technical Skills}
Python, SQL, BigQuery, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI, dbt
\section{Projects}
Project.
\end{document}
TEXEOF

compile_tex "$TEST_DIR/bad-resume-emdash.tex" "bad-resume-emdash"

if [ -f "$TEST_DIR/bad-resume-emdash.pdf" ]; then
  assert_output_contains "Detects em dash in source" "Em dash" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-emdash.pdf" "$TEST_DIR/bad-resume-emdash.tex"
  assert_fail "Fails when em dash present" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-emdash.pdf" "$TEST_DIR/bad-resume-emdash.tex"
else
  echo "  SKIP: bad-resume-emdash.pdf failed to compile"
fi

# ============================================================
header "Resume Script: Non-Standard Section Headers"
# ============================================================

cat > "$TEST_DIR/bad-resume-headers.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[letterpaper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{cmap}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Senior Software Engineer},
  pdfauthor={Ilyas Ibragimov},
  pdfkeywords={Software Engineer, Python}
}
\pdfgentounicode=1
\begin{document}
\begin{center}
\textbf{\huge ILYAS IBRAGIMOV} \\
New York, NY | ilyas.ibragimov@outlook.com | linkedin.com/in/ilyasi | ilyasi.com
\end{center}
\section{About Me}
Software engineer. Python, BigQuery, dbt, SQL, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI.
\section{Career History}
\textbf{Two Sigma} \hfill Nov. 2022 -- Present \\
Built systems.
\textbf{Blueshift Asset Management} \hfill Jan. 2020 -- Nov. 2022 \\
Software Developer
\textbf{Fidessa} \hfill July 2018 -- Sep. 2018 \\
Intern
\section{Education}
University College London (UCL) \\
Master of Engineering \hfill 2018 -- 2019 \\
Bachelor of Engineering \hfill 2015 -- 2018 \\
First Class Honors, 4.0 GPA \\
Baruch College, Distinction \hfill 2020 \\
Brooklyn Technical High School \hfill 2011 -- 2015
\section{Technical Skills}
Python, SQL, BigQuery, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI, dbt
\section{Projects}
Project.
\end{document}
TEXEOF

compile_tex "$TEST_DIR/bad-resume-headers.tex" "bad-resume-headers"

if [ -f "$TEST_DIR/bad-resume-headers.pdf" ]; then
  assert_output_contains "Detects non-standard section headers" "Non-standard section headers" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-headers.pdf" "$TEST_DIR/bad-resume-headers.tex"
else
  echo "  SKIP: bad-resume-headers.pdf failed to compile"
fi

# ============================================================
header "Resume Script: Multicol Layout Detection"
# ============================================================

cat > "$TEST_DIR/bad-resume-multicol.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[letterpaper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{cmap}
\usepackage[T1]{fontenc}
\input{glyphtounicode}
\usepackage{multicol}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Senior Software Engineer},
  pdfauthor={Ilyas Ibragimov},
  pdfkeywords={Software Engineer, Python}
}
\pdfgentounicode=1
\begin{document}
\begin{center}
\textbf{\huge ILYAS IBRAGIMOV} \\
New York, NY | ilyas.ibragimov@outlook.com | linkedin.com/in/ilyasi | ilyasi.com
\end{center}
\section{Summary}
Engineer. Python, BigQuery, dbt, SQL, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI.
\section{Experience}
\textbf{Two Sigma} \hfill Nov. 2022 -- Present \\
Built systems.
\textbf{Blueshift Asset Management} \hfill Jan. 2020 -- Nov. 2022 \\
Dev
\textbf{Fidessa} \hfill July 2018 -- Sep. 2018 \\
Intern
\section{Education}
University College London (UCL) \\
Master of Engineering \hfill 2018 -- 2019 \\
Bachelor of Engineering \hfill 2015 -- 2018 \\
First Class Honors, 4.0 GPA \\
Baruch College, Distinction \hfill 2020 \\
Brooklyn Technical High School \hfill 2011 -- 2015
\section{Technical Skills}
Python, SQL, BigQuery, C++, GCP, Claude, GenAI, AI Pipelines, Vertex AI, dbt
\section{Projects}
Project.
\end{document}
TEXEOF

compile_tex "$TEST_DIR/bad-resume-multicol.tex" "bad-resume-multicol"

if [ -f "$TEST_DIR/bad-resume-multicol.pdf" ]; then
  assert_output_contains "Detects multicol package" "multicol" \
    bash "$SCRIPT_DIR/verify-resume-ats.sh" "$TEST_DIR/bad-resume-multicol.pdf" "$TEST_DIR/bad-resume-multicol.tex"
else
  echo "  SKIP: bad-resume-multicol.pdf failed to compile"
fi

# ============================================================
header "Cover Letter Script: Good Cover Letter"
# ============================================================

cat > "$TEST_DIR/cover-good.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{cmap}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Cover Letter - TestCo},
  pdfauthor={Ilyas Ibragimov},
}
\pdfgentounicode=1
\begin{document}
\begin{letter}{}
\opening{Hi,}

I am writing to express interest in the Software Engineer role at TestCo. I have spent the last six years building backend systems at quantitative hedge funds where security and data accuracy are critical, and I think that experience maps well to what you are building.

At Two Sigma I helped build a firm-wide cost transparency platform from the ground up over three years in Python and BigQuery, ingesting fifteen terabytes daily from eight data sources. After several engineers left I stepped up to lead the backend, broke a monolith into separate services with continuous integration and automated testing, and kept the system running and evolving. I also built several production tools using generative AI. Before that, at a small twenty-person hedge fund, I built real-time portfolio monitoring, compliance systems, and exchange integrations all from scratch, handling sensitive financial data for hundreds of millions in managed assets.

I have been following TestCo for a while and I really like the direction you are heading. Building reliable infrastructure at scale is exactly the kind of problem I want to work on. My whole career has been in environments where getting it wrong has real consequences, and I value that same rigor. I am based in New York and happy to be in office.

Thank you for your consideration,

Ilyas
\end{letter}
\end{document}
TEXEOF

compile_tex "$TEST_DIR/cover-good.tex" "Ilyas_Ibragimov_Cover_Letter_TestCo"

if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_TestCo.pdf" ]; then
  assert_pass "Good cover letter passes all checks" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_TestCo.pdf" "$TEST_DIR/cover-good.tex"
else
  echo "  SKIP: good cover letter failed to compile"
fi

# ============================================================
header "Cover Letter Script: Too Short"
# ============================================================

cat > "$TEST_DIR/cover-short.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{cmap}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Cover Letter - ShortCo},
  pdfauthor={Ilyas Ibragimov},
}
\pdfgentounicode=1
\begin{document}
\begin{letter}{}
\opening{Hi,}

I want this job at ShortCo. I am a good engineer. Please hire me.

Thank you for your consideration,

Ilyas
\end{letter}
\end{document}
TEXEOF

compile_tex "$TEST_DIR/cover-short.tex" "Ilyas_Ibragimov_Cover_Letter_ShortCo"

if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_ShortCo.pdf" ]; then
  assert_fail "Too-short cover letter fails" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_ShortCo.pdf" "$TEST_DIR/cover-short.tex"
  assert_output_contains "Reports word count issue" "too short\|words" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_ShortCo.pdf" "$TEST_DIR/cover-short.tex"
else
  echo "  SKIP: short cover letter failed to compile"
fi

# ============================================================
header "Cover Letter Script: Missing ATS Packages"
# ============================================================

cat > "$TEST_DIR/cover-no-packages.tex" << 'TEXEOF'
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Cover Letter - BadCo},
  pdfauthor={Ilyas Ibragimov},
}
\begin{document}
\begin{letter}{}
\opening{Hi,}

I am writing about the role at BadCo. I have spent many years building backend systems at quantitative hedge funds. At Two Sigma I built a cost transparency platform in Python and BigQuery. I led the backend effort and broke a monolith into separate services. Before that at a small hedge fund I built portfolio monitoring and compliance systems.

I am based in New York and happy to be in office. I look forward to hearing from you soon about the opportunity.

Thank you for your consideration,

Ilyas
\end{letter}
\end{document}
TEXEOF

compile_tex "$TEST_DIR/cover-no-packages.tex" "Ilyas_Ibragimov_Cover_Letter_BadCo"

if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_BadCo.pdf" ]; then
  assert_output_contains "Detects missing cmap in cover letter" "Missing.*cmap" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_BadCo.pdf" "$TEST_DIR/cover-no-packages.tex"
  assert_output_contains "Detects missing glyphtounicode in cover letter" "Missing.*glyphtounicode" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_BadCo.pdf" "$TEST_DIR/cover-no-packages.tex"
  assert_output_contains "Detects missing pdfgentounicode in cover letter" "Missing.*pdfgentounicode" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_BadCo.pdf" "$TEST_DIR/cover-no-packages.tex"
  assert_fail "Cover letter fails when ATS packages missing" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_BadCo.pdf" "$TEST_DIR/cover-no-packages.tex"
else
  echo "  SKIP: bad cover letter failed to compile"
fi

# ============================================================
header "Cover Letter Script: Em Dash Detection"
# ============================================================

cat > "$TEST_DIR/cover-emdash.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{cmap}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Cover Letter - DashCo},
  pdfauthor={Ilyas Ibragimov},
}
\pdfgentounicode=1
\begin{document}
\begin{letter}{}
\opening{Hi,}

I am writing about the role at DashCo. I have built systems — large and small — for many years at quantitative hedge funds. At Two Sigma I built a cost transparency platform in Python and BigQuery. I led the backend effort and broke a monolith into separate services. Before that at a hedge fund I built portfolio monitoring and compliance systems.

I am based in New York and happy to be in office. I am excited about the opportunity.

Thank you for your consideration,

Ilyas
\end{letter}
\end{document}
TEXEOF

compile_tex "$TEST_DIR/cover-emdash.tex" "Ilyas_Ibragimov_Cover_Letter_DashCo"

if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_DashCo.pdf" ]; then
  assert_output_contains "Detects em dash in cover letter source" "Em dash" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_DashCo.pdf" "$TEST_DIR/cover-emdash.tex"
  assert_fail "Cover letter fails when em dash present" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_DashCo.pdf" "$TEST_DIR/cover-emdash.tex"
else
  echo "  SKIP: emdash cover letter failed to compile"
fi

# ============================================================
header "Cover Letter Script: Filename Validation"
# ============================================================

# Test with spaces in filename
if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_TestCo.pdf" ]; then
  cp "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_TestCo.pdf" "$TEST_DIR/Cover Letter TestCo.pdf"
  assert_output_contains "Detects spaces in filename" "spaces" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Cover Letter TestCo.pdf"

  # Test with special characters in filename
  cp "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_TestCo.pdf" "$TEST_DIR/Cover#Letter&TestCo.pdf"
  assert_output_contains "Detects special characters in filename" "special characters" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Cover#Letter&TestCo.pdf"
fi

# ============================================================
header "Cover Letter Script: Company Personalization"
# ============================================================

cat > "$TEST_DIR/cover-generic.tex" << 'TEXEOF'
\pdfminorversion=4
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[T1]{fontenc}
\usepackage{cmap}
\input{glyphtounicode}
\usepackage{hyperref}
\hypersetup{
  pdftitle={Ilyas Ibragimov - Cover Letter - SpecialCorp},
  pdfauthor={Ilyas Ibragimov},
}
\pdfgentounicode=1
\begin{document}
\begin{letter}{}
\opening{Hi,}

I am writing about a software engineering role at your company. I have spent the last six years building backend systems at quantitative hedge funds where security and data accuracy are paramount.

At Two Sigma I built a cost transparency platform in Python and BigQuery, ingesting many terabytes daily. I led the backend effort and broke a monolith into separate services. Before that at a small hedge fund I built portfolio monitoring, compliance systems, and exchange integrations.

I am based in New York and happy to be in office. I look forward to hearing from you about this opportunity.

Thank you for your consideration,

Ilyas
\end{letter}
\end{document}
TEXEOF

compile_tex "$TEST_DIR/cover-generic.tex" "Ilyas_Ibragimov_Cover_Letter_SpecialCorp"

if [ -f "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_SpecialCorp.pdf" ]; then
  assert_output_contains "Detects missing company name in body" "not found in letter body" \
    bash "$SCRIPT_DIR/verify-cover-letter-ats.sh" "$TEST_DIR/Ilyas_Ibragimov_Cover_Letter_SpecialCorp.pdf" "$TEST_DIR/cover-generic.tex"
else
  echo "  SKIP: generic cover letter failed to compile"
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "========================================"
printf "Tests: %d run, \033[32m%d passed\033[0m, \033[31m%d failed\033[0m\n" "$TESTS_RUN" "$TESTS_PASSED" "$TESTS_FAILED"
if [ "$TESTS_FAILED" -gt 0 ]; then
  echo "STATUS: FAIL"
  exit 1
else
  echo "STATUS: ALL TESTS PASSED"
  exit 0
fi
