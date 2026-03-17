# Claude Instructions

## File Naming
Always name output files (PDFs, cover letters, resumes) in the format:
`Ilyas_Ibragimov_<Type>_<Company>.pdf`

Examples:
- `Ilyas_Ibragimov_Resume_CLEAR.pdf`
- `Ilyas_Ibragimov_Cover_Letter_Peregrine.pdf`

## ATS / Machine Readability
Every tailored resume must be verified for ATS parsability before delivery:
1. Compile the PDF with `pdflatex`
2. Run `bash scripts/verify-resume-ats.sh <pdf>` on the output
3. All checks must pass (contact info, section headers, skills keywords, encoding, page count)
4. The LaTeX template already includes `\pdfgentounicode=1`, `cmap`, and `[T1]{fontenc}` for proper text extraction. Do not remove these.
5. When creating tailored resumes, ensure all JD-relevant skills the user actually has are listed in Technical Skills to pass ATS keyword filters, even if rudimentary.
