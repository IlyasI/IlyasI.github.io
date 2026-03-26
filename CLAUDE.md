# Claude Instructions

## File Naming
Always name output files (PDFs, cover letters, resumes) in the format:
`Ilyas_Ibragimov_<Type>_<Company>.pdf`

Examples:
- `Ilyas_Ibragimov_Resume_CLEAR.pdf`
- `Ilyas_Ibragimov_Cover_Letter_Peregrine.pdf`

## ATS / Machine Readability

### Resumes
Every tailored resume must be verified for ATS parsability before delivery:
1. Compile the PDF with `pdflatex`
2. Run `bash scripts/verify-resume-ats.sh <pdf> [source.tex]` on the output
3. All checks must pass (contact info, section headers, skills keywords, encoding, page count, PDF version, fonts, metadata)
4. The LaTeX template includes `\pdfminorversion=4`, `\pdfgentounicode=1`, `cmap`, `glyphtounicode`, and `[T1]{fontenc}` for proper text extraction and ATS compatibility. Do not remove these.
5. When creating tailored resumes, ensure all JD-relevant skills the user actually has are listed in Technical Skills to pass ATS keyword filters, even if rudimentary.
6. Shortcut: `make build-verify-clear` builds and verifies in one step.

### Cover Letters
Every cover letter must be verified for ATS parsability before delivery:
1. Compile the PDF with `pdflatex`
2. Run `bash scripts/verify-cover-letter-ats.sh <pdf> [source.tex]` on the output
3. All checks must pass (filename, structure, word count 200-400, encoding, fonts, PDF version, page count = 1)
4. Cover letter LaTeX files must include `\pdfminorversion=4`, `cmap`, `[T1]{fontenc}`, `glyphtounicode`, and `\pdfgentounicode=1`. See cover-clear.tex as the reference template.
5. Shortcut: `make build-verify-cover-clear` builds and verifies in one step.

### Testing
Run `make test-ats` to execute the full ATS verification test suite (34 tests).

## Workflow: Creating a Tailored Resume
1. Copy `resume-clear.tex` to `resume-<company>.tex`
2. Edit the copy for the target role (reorder bullets, adjust skills, update summary)
3. Add a `resume-<company>` target to the Makefile
4. Add `resume-<company>.tex`, `resume-<company>.pdf`, and `Ilyas_Ibragimov_Resume_<Company>.pdf` to `.gitignore`
5. Build: `make resume-<company>`
6. Verify: `bash scripts/verify-resume-ats.sh Ilyas_Ibragimov_Resume_<Company>.pdf resume-<company>.tex`
7. All checks must pass before sending

## Workflow: Creating a Cover Letter
1. Copy `cover-clear.tex` to `cover-<company>.tex`
2. Edit for the target role (update company name, tailor content, set pdftitle)
3. Add a `cover-<company>` target to the Makefile
4. Add `cover-<company>.tex`, `cover-<company>.pdf`, and `Ilyas_Ibragimov_Cover_Letter_<Company>.pdf` to `.gitignore`
5. Build: `make cover-<company>`
6. Verify: `bash scripts/verify-cover-letter-ats.sh Ilyas_Ibragimov_Cover_Letter_<Company>.pdf cover-<company>.tex`
7. All checks must pass before sending

## Make Targets Reference
| Target | Description |
|--------|-------------|
| `make resume-clear` | Build CLEAR resume PDF |
| `make cover-clear` | Build CLEAR cover letter PDF |
| `make verify` | Verify base resume |
| `make verify-clear` | Verify CLEAR resume |
| `make verify-cover-clear` | Verify CLEAR cover letter |
| `make verify-ats PDF=... TEX=...` | Verify any resume |
| `make verify-cover PDF=... TEX=...` | Verify any cover letter |
| `make build-verify-clear` | Build + verify CLEAR resume |
| `make build-verify-cover-clear` | Build + verify CLEAR cover letter |
| `make test-ats` | Run ATS verification test suite |
| `make clean` | Remove LaTeX build artifacts |

## Writing Style: Don't Sound Like AI
When writing prose for the user (cover letters, application answers, LinkedIn posts, etc.):

### Never use these words/phrases

**Red flag words (AI uses these 10-180x more than humans):**
"delve", "leverage", "utilize", "facilitate", "pivotal", "crucial", "paramount", "robust", "comprehensive", "cutting-edge", "streamline", "harness", "foster", "revolutionize", "game-changer", "unlock", "seamless", "showcasing", "aligns", "aims to", "surpassing", "impacting", "remarked", "realm", "tapestry", "synergy", "cognizant", "sentinel", "peril", "pertinent", "elevated", "proactive", "innovative", "supercharge", "future-proof", "unleash", "transform" (as buzzword), "optimize" (as buzzword), "enable", "powerful", "intuitive"

**Red flag phrases:**
"moreover", "furthermore", "additionally", "in conclusion", "in summary", "to sum up", "it's worth noting", "in today's fast-paced world", "I've got", "testament to", "plays a significant role in shaping", "not just X, but also Y", "the goal?", "the result?", "fundamentally", "I'm thrilled", "I'm passionate about", "deeply resonates", "at its core", "notable works include", "one should keep in mind", "aims to explore"

### Never use em dashes
Use commas, periods, or "and" instead.

### Avoid AI structural patterns
- No setup/explanation/lesson sandwich structure
- No neat wrap-up or takeaway paragraph at the end
- Don't make every sentence roughly the same length
- Don't use formal transitions between every thought
- Don't follow a rigid paragraph pattern
- Don't over-qualify or hedge everything

### Do
- Use contractions
- Vary sentence length (short ones mixed with longer ones)
- Start sentences with "And", "But", "So" sometimes
- Write how the user actually talks
- Keep it slightly messy/imperfect, like a real person wrote it
- Use simple common words ("use" not "utilize", "important" not "crucial")
- If the user gives you their rough wording, preserve their voice and just clean it up
