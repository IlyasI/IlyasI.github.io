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
