.PHONY: resume resume-full resume-harvey resume-hearst resume-peregrine resume-clear resume-breakfast resume-twentyai resume-camber resume-decagon resume-carta resume-chalk resume-brellium resume-etsy resume-plaid resume-distylai verify clean jobs jobs-fresh jobs-json jobs-site jobs-setup tracker tracker-list tracker-add tracker-update tracker-followups tracker-stats apply
resume:
	pdflatex resume.tex

resume-full:
	pdflatex -jobname=resume-full "\def\includephone{1}\input{resume.tex}"

resume-harvey:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Harvey "\def\includephone{1}\input{resume-harvey.tex}"

resume-hearst:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Hearst "\def\includephone{1}\input{resume-hearst.tex}"

resume-peregrine:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Peregrine "\def\includephone{1}\input{resume-peregrine.tex}"

resume-clear:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_CLEAR "\def\includephone{1}\input{resume-clear.tex}"

resume-breakfast:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Breakfast "\def\includephone{1}\input{resume-breakfast.tex}"

resume-twentyai:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_TwentyAI "\def\includephone{1}\input{resume-twentyai.tex}"

resume-robinhood:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Robinhood "\def\includephone{1}\input{resume-robinhood.tex}"

cover-robinhood:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Robinhood cover-robinhood.tex

resume-decagon:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Decagon "\def\includephone{1}\input{resume-decagon.tex}"

resume-camber:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Camber "\def\includephone{1}\input{resume-camber.tex}"

resume-hubspot:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_HubSpot "\def\includephone{1}\input{resume-hubspot.tex}"

cover-hubspot:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_HubSpot cover-hubspot.tex

resume-carta:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Carta "\def\includephone{1}\input{resume-carta.tex}"

cover-carta:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Carta cover-carta.tex

resume-stubhub:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_StubHub "\def\includephone{1}\input{resume-stubhub.tex}"

resume-bloomberg:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Bloomberg "\def\includephone{1}\input{resume-bloomberg.tex}"

cover-bloomberg:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Bloomberg cover-bloomberg.tex

resume-hinge:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Hinge "\def\includephone{1}\input{resume-hinge.tex}"

resume-posh:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Posh "\def\includephone{1}\input{resume-posh.tex}"

resume-merge:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Merge "\def\includephone{1}\input{resume-merge.tex}"

resume-whatnot:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Whatnot "\def\includephone{1}\input{resume-whatnot.tex}"

resume-chalk:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Chalk "\def\includephone{1}\input{resume-chalk.tex}"

cover-chalk:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Chalk cover-chalk.tex

resume-doordash:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_DoorDash "\def\includephone{1}\input{resume-doordash.tex}"

cover-doordash:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_DoorDash cover-doordash.tex

resume-brellium:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Brellium "\def\includephone{1}\input{resume-brellium.tex}"

resume-etsy:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Etsy "\def\includephone{1}\input{resume-etsy.tex}"

resume-clearwater:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Clearwater "\def\includephone{1}\input{resume-clearwater.tex}"

resume-plaid:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Plaid "\def\includephone{1}\input{resume-plaid.tex}"

resume-blueflame:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_BlueflameAI "\def\includephone{1}\input{resume-blueflame.tex}"

resume-distylai:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_DistylAI "\def\includephone{1}\input{resume-distylai.tex}"

resume-candidhealth:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_CandidHealth "\def\includephone{1}\input{resume-candidhealth.tex}"

resume-coreweave:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_CoreWeave "\def\includephone{1}\input{resume-coreweave.tex}"

cover-candidhealth:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_CandidHealth cover-candidhealth.tex

resume-ramp:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Ramp "\def\includephone{1}\input{resume-ramp.tex}"

cover-coreweave:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_CoreWeave cover-coreweave.tex

resume-sony:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Sony "\def\includephone{1}\input{resume-sony.tex}"

cover-sony:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Sony cover-sony.tex

resume-vanta:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Vanta "\def\includephone{1}\input{resume-vanta.tex}"

resume-crosby:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Crosby "\def\includephone{1}\input{resume-crosby.tex}"

resume-optiver:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Optiver "\def\includephone{1}\input{resume-optiver.tex}"

resume-amd:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_AMD "\def\includephone{1}\input{resume-amd.tex}"

cover-amd:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_AMD cover-amd.tex

resume-projectcanary:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_ProjectCanary "\def\includephone{1}\input{resume-projectcanary.tex}"

resume-bip:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_BIP "\def\includephone{1}\input{resume-bip.tex}"

resume-hartford:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Hartford "\def\includephone{1}\input{resume-hartford.tex}"

resume-deloitte:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Deloitte "\def\includephone{1}\input{resume-deloitte.tex}"

cover-deloitte:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Deloitte cover-deloitte.tex

resume-unify:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Unify "\def\includephone{1}\input{resume-unify.tex}"

resume-rationaldynamics:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_RationalDynamics "\def\includephone{1}\input{resume-rationaldynamics.tex}"

cover-rationaldynamics:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_RationalDynamics cover-rationaldynamics.tex

cover-projectcanary:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_ProjectCanary cover-projectcanary.tex

resume-unity:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Unity "\def\includephone{1}\input{resume-unity.tex}"

cover-unity:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Unity cover-unity.tex

resume-datadog:
	pdflatex -jobname=Ilyas_Ibragimov_Resume_Datadog "\def\includephone{1}\input{resume-datadog.tex}"

cover-datadog:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_Datadog cover-datadog.tex

verify:
	bash scripts/verify-resume-ats.sh resume.pdf resume.tex

verify-clear:
	bash scripts/verify-resume-ats.sh Ilyas_Ibragimov_Resume_CLEAR.pdf resume-clear.tex

# Verify any resume: make verify-ats PDF=Ilyas_Ibragimov_Resume_Plaid.pdf TEX=resume-plaid.tex
verify-ats:
	bash scripts/verify-resume-ats.sh $(PDF) $(TEX)

# Build and verify CLEAR resume in one step
build-verify-clear: resume-clear verify-clear

# Cover letter verification
cover-clear:
	pdflatex -jobname=Ilyas_Ibragimov_Cover_Letter_CLEAR cover-clear.tex

verify-cover-clear:
	bash scripts/verify-cover-letter-ats.sh Ilyas_Ibragimov_Cover_Letter_CLEAR.pdf cover-clear.tex

# Verify any cover letter: make verify-cover PDF=Ilyas_Ibragimov_Cover_Letter_Chalk.pdf TEX=cover-chalk.tex
verify-cover:
	bash scripts/verify-cover-letter-ats.sh $(PDF) $(TEX)

# Build and verify CLEAR cover letter in one step
build-verify-cover-clear: cover-clear verify-cover-clear

# Run ATS verification test suite
test-ats:
	bash scripts/test-ats-checks.sh

# --- Job Search ---
jobs-setup:
	pip3 install -r jobs/requirements.txt

jobs:
	python3 jobs/search.py

jobs-fresh:
	python3 jobs/search.py --max-age 24

jobs-json:
	python3 jobs/search.py --json

jobs-site:
	python3 jobs/search.py --json --output jobs/data/results.json
	@echo "Dashboard ready: open jobs.html"

jobs-test:
	python3 -m pytest jobs/test_search.py -v

jobs-install:
	bash jobs/install.sh

jobs-uninstall:
	bash jobs/uninstall.sh

# --- Application Tracker ---
tracker:
	python3 scripts/tracker.py

tracker-list:
	python3 scripts/tracker.py list

tracker-add:
	python3 scripts/tracker.py add "$(COMPANY)" "$(ROLE)" "$(URL)"

tracker-update:
	python3 scripts/tracker.py update "$(COMPANY)" $(STATUS)

tracker-followups:
	python3 scripts/tracker.py followups

tracker-stats:
	python3 scripts/tracker.py stats

# --- Apply to a Job ---
apply:
	python3 jobs/apply.py "$(COMPANY)" "$(URL)"

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz
