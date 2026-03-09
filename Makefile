.PHONY: resume resume-full verify clean

resume:
	pdflatex resume.tex

resume-full:
	pdflatex -jobname=resume-full "\def\includephone{1}\input{resume.tex}"

verify:
	bash scripts/verify-resume-ats.sh resume.pdf

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz
