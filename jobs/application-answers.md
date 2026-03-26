# Application Answers

## Have you encountered a bug or production issue introduced by AI-generated code? How did you identify the root cause, and what steps did you take to resolve and prevent it?

I use Claude Code and Vertex AI at Two Sigma. AI-written code can look correct in the PR, pass review, pass tests, and still not work with the rest of the system. It'll duplicate logic that already exists upstream, or make a wrong assumption about how data flows between services. You find out when the numbers are off downstream or when a stakeholder flags something.

I write tests first now. TDD works well with AI because the tests act as a spec, telling it what to do and what not to break. I run automated code reviews and static analysis on every PR through GitHub Actions, and I have reconciliation checks that compare outputs to source systems before anything gets promoted. We also decomposed a legacy monolith into 5 loosely coupled pipelines, which makes it much easier to isolate and test changes. There's schema drift auto-recovery so if an upstream source changes shape the system handles it instead of silently breaking. And I built an automated incident response pipeline that monitors for failures, sends Slack alerts, and does root-cause analysis, so if something still slips through it gets caught quickly.

## Describe a feature you've built end-to-end. What problem were you solving, how did you structure the frontend and/or backend, and what trade-offs did you make?

I built the backend for a firm-wide cost transparency platform at Two Sigma. The problem was that nobody had a clear picture of what the firm was actually spending on cloud, GenAI, and engineering products across hundreds of teams. Leadership needed that visibility to make decisions, and the existing tooling couldn't keep up.

I built the ELT backend in Python, dbt, and BigQuery. It ingests 15+ TB daily from 8+ data sources, normalizes everything into a common cost model, and feeds executive dashboards through Backstage. The data layer uses dimensional modeling so teams can slice spend by product, department, infrastructure type, whatever they need.

The main trade-off was build vs. buy. We had been using Apptio for this, which is an off-the-shelf cost management tool. It worked but it was slow, expensive, and every new data source or cost view took weeks to configure. Building in-house meant more upfront work, but we got 65% faster processing, $1M+ in annual savings from dropping the license, and the ability to ship new cost breakdowns same-day instead of waiting on vendor support. The other trade-off was choosing dbt over plain SQL for transformations. It added a learning curve for the team, but the testing framework and lineage tracking were worth it, especially at our scale.

## Tell us about a time you improved an existing system or tool. What was inefficient or breaking down, and how did your changes impact users or your team?

We were using Apptio to track cloud and engineering spend across the firm. It was slow, expensive, and inflexible. Processing took hours for what should have been minutes. Every time a new data source came online or the business needed a new cost view, it required weeks of configuration in a proprietary GUI that only a couple people understood. And we were paying significant licensing fees on top of all that.

I led the migration to an in-house stack built on Python, dbt, and BigQuery. Processing went from hours to minutes. We cut over $1M in annual licensing costs. But the real difference was flexibility. When a team needed a new cost breakdown or a new data source got added, I could write a dbt model and have it in production the same day instead of filing a ticket and waiting weeks.

After the migration I drove dbt adoption more broadly at the firm. I co-authored an internal best practices guide, built quickstart repos so other teams could get started quickly, and gave presentations. Multiple teams ended up adopting dbt for their own pipelines after seeing what we did with it.
