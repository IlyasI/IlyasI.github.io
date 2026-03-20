#!/usr/bin/env python3
"""Generate a weekly content calendar for developer community promotion.

Usage:
    python scripts/promote/content-calendar.py [--weeks N] [--start YYYY-MM-DD]
    python scripts/promote/content-calendar.py --weeks 4
    python scripts/promote/content-calendar.py --weeks 2 --start 2026-03-23

Outputs a Markdown content calendar with daily posting schedule across platforms.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "calendars"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# Each week has a theme and daily tasks per platform
WEEKLY_TEMPLATES = [
    {
        "theme": "Pre-Launch: Build Credibility",
        "goal": "Establish presence in target communities before any promotion",
        "days": {
            "Monday": [
                {"platform": "Reddit", "action": "Answer 2-3 questions in r/cscareerquestions (career advice, interview tips)", "time": "9 AM EST", "type": "engagement"},
                {"platform": "Twitter/X", "action": "Post an interview tip tweet (system design, behavioral, or coding)", "time": "10 AM EST", "type": "content"},
            ],
            "Tuesday": [
                {"platform": "Reddit", "action": "Comment helpfully on r/experienceddevs thread about career growth", "time": "9 AM EST", "type": "engagement"},
                {"platform": "Twitter/X", "action": "Engage with 5 tech thought leaders (meaningful replies, not just likes)", "time": "10 AM EST", "type": "engagement"},
                {"platform": "Discord", "action": "Join 2-3 developer communities (Reactiflux, CodeSupport). Introduce yourself.", "time": "afternoon", "type": "setup"},
            ],
            "Wednesday": [
                {"platform": "Dev.to", "action": "Publish first article: 'System Design Patterns I've Seen From Both Sides'", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Share key insight from the Dev.to article as a thread (3-5 tweets)", "time": "11 AM EST", "type": "content"},
                {"platform": "Reddit", "action": "Answer questions in r/learnprogramming", "time": "afternoon", "type": "engagement"},
            ],
            "Thursday": [
                {"platform": "Twitter/X", "action": "Post a hot take or opinion tweet about frameworks vs vanilla JS", "time": "10 AM EST", "type": "content"},
                {"platform": "Reddit", "action": "Answer 2-3 questions in r/webdev about JS or portfolio sites", "time": "9 AM EST", "type": "engagement"},
            ],
            "Friday": [
                {"platform": "Hashnode", "action": "Cross-post Dev.to article with canonical URL to your domain", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Weekend engagement: ask a question to your followers about interview experiences", "time": "10 AM EST", "type": "engagement"},
            ],
            "Weekend": [
                {"platform": "Blog", "action": "Write next week's article (draft): technical deep-dive on vanilla JS portfolio", "time": "flexible", "type": "prep"},
            ],
        },
    },
    {
        "theme": "Launch Week: Show HN + Reddit + Cross-Post",
        "goal": "Launch the portfolio site across all platforms in a coordinated push",
        "days": {
            "Monday": [
                {"platform": "Blog", "action": "Publish blog post on your domain: 'I Built an Interactive Portfolio with Zero Dependencies'", "time": "morning", "type": "content"},
                {"platform": "Twitter/X", "action": "Teaser tweet: 'Rebuilt my portfolio with zero dependencies. Writeup coming this week.'", "time": "10 AM EST", "type": "content"},
            ],
            "Tuesday": [
                {"platform": "Hacker News", "action": "Post 'Show HN: Interactive portfolio built with vanilla JS'. Write top comment immediately.", "time": "9 AM EST", "type": "launch"},
                {"platform": "Twitter/X", "action": "Launch thread (5-6 tweets). Link in reply, not main tweet.", "time": "10 AM EST", "type": "launch"},
                {"platform": "ALL", "action": "Monitor HN and Twitter ALL DAY. Respond to every comment within 30 min.", "time": "all day", "type": "engagement"},
            ],
            "Wednesday": [
                {"platform": "Reddit", "action": "Post in r/SideProject: 'I built my portfolio with vanilla JS'", "time": "9 AM EST", "type": "launch"},
                {"platform": "Dev.to", "action": "Cross-post the blog article with canonical URL", "time": "10 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Share learnings from HN launch: 'Yesterday I posted on HN, here's what happened...'", "time": "11 AM EST", "type": "content"},
            ],
            "Thursday": [
                {"platform": "Reddit", "action": "Post in r/webdev: technical deep-dive on the vanilla JS approach", "time": "9 AM EST", "type": "launch"},
                {"platform": "Hashnode", "action": "Cross-post blog article with canonical URL", "time": "10 AM EST", "type": "content"},
                {"platform": "Discord", "action": "Share in #show-your-work channels (Reactiflux, CodeSupport)", "time": "afternoon", "type": "launch"},
            ],
            "Friday": [
                {"platform": "Medium", "action": "Cross-post to Medium (submit to Better Programming publication)", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Week recap thread: metrics, feedback, what you learned from launching", "time": "10 AM EST", "type": "content"},
                {"platform": "Reddit", "action": "Post value-add comment in r/cscareerquestions referencing your experience", "time": "afternoon", "type": "engagement"},
            ],
            "Weekend": [
                {"platform": "Blog", "action": "Write launch retrospective post (what worked, traffic numbers, lessons)", "time": "flexible", "type": "prep"},
                {"platform": "Twitter/X", "action": "Casual weekend engagement and replies", "time": "flexible", "type": "engagement"},
            ],
        },
    },
    {
        "theme": "Post-Launch: Sustain Momentum",
        "goal": "Keep engagement high with consistent value content",
        "days": {
            "Monday": [
                {"platform": "Twitter/X", "action": "Interview tip tweet (behavioral or coding)", "time": "10 AM EST", "type": "content"},
                {"platform": "Reddit", "action": "Answer 2-3 questions in career/interview subreddits", "time": "9 AM EST", "type": "engagement"},
            ],
            "Tuesday": [
                {"platform": "Blog", "action": "Publish new article: career advice or technical content from content themes", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Thread summarizing the new blog post", "time": "11 AM EST", "type": "content"},
            ],
            "Wednesday": [
                {"platform": "Dev.to", "action": "Cross-post latest blog article", "time": "9 AM EST", "type": "content"},
                {"platform": "Reddit", "action": "Value post in r/experienceddevs (career lessons, technical insights)", "time": "10 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Engage with trending dev conversations", "time": "afternoon", "type": "engagement"},
            ],
            "Thursday": [
                {"platform": "Twitter/X", "action": "Opinion or hot take tweet on tech/career topic", "time": "10 AM EST", "type": "content"},
                {"platform": "Hashnode", "action": "Cross-post latest article", "time": "9 AM EST", "type": "content"},
                {"platform": "Discord", "action": "Help people in developer community channels", "time": "afternoon", "type": "engagement"},
            ],
            "Friday": [
                {"platform": "Twitter/X", "action": "Engagement tweet: ask followers a question", "time": "10 AM EST", "type": "engagement"},
                {"platform": "Reddit", "action": "Weekly helpful answers in target subreddits", "time": "9 AM EST", "type": "engagement"},
            ],
            "Weekend": [
                {"platform": "Blog", "action": "Draft next week's article", "time": "flexible", "type": "prep"},
            ],
        },
    },
    {
        "theme": "Growth: Newsletter Outreach + SEO",
        "goal": "Scale through SEO content and newsletter sponsorships",
        "days": {
            "Monday": [
                {"platform": "SEO", "action": "Publish long-form SEO article targeting a long-tail keyword (e.g., 'how to prepare for system design interviews 2026')", "time": "morning", "type": "content"},
                {"platform": "Twitter/X", "action": "Daily tip tweet", "time": "10 AM EST", "type": "content"},
            ],
            "Tuesday": [
                {"platform": "Newsletter", "action": "Reach out to 2-3 smaller dev newsletters about sponsorship (Pony Foo Weekly, CSS Weekly)", "time": "morning", "type": "outreach"},
                {"platform": "Dev.to", "action": "Cross-post SEO article", "time": "10 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Thread or tip tweet", "time": "11 AM EST", "type": "content"},
            ],
            "Wednesday": [
                {"platform": "Reddit", "action": "Value post in target subreddits (tips, advice, insights)", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Engage with trending conversations", "time": "10 AM EST", "type": "engagement"},
                {"platform": "SEO", "action": "Update any year-tagged content with current year (2026)", "time": "afternoon", "type": "maintenance"},
            ],
            "Thursday": [
                {"platform": "Blog", "action": "Publish comparison article (e.g., 'Framework vs Vanilla JS for Portfolio Sites')", "time": "9 AM EST", "type": "content"},
                {"platform": "Twitter/X", "action": "Share key insight from comparison article", "time": "11 AM EST", "type": "content"},
                {"platform": "Hashnode", "action": "Cross-post comparison article", "time": "afternoon", "type": "content"},
            ],
            "Friday": [
                {"platform": "Newsletter", "action": "Follow up on sponsorship outreach. Track UTM links.", "time": "morning", "type": "outreach"},
                {"platform": "Twitter/X", "action": "Week recap or engagement question", "time": "10 AM EST", "type": "engagement"},
                {"platform": "Reddit", "action": "Helpful answers in career subreddits", "time": "afternoon", "type": "engagement"},
            ],
            "Weekend": [
                {"platform": "Blog", "action": "Draft 2 articles for next week (1 SEO-targeted, 1 value-driven)", "time": "flexible", "type": "prep"},
                {"platform": "Analytics", "action": "Review traffic, top pages, conversion rates. Adjust strategy.", "time": "flexible", "type": "analysis"},
            ],
        },
    },
]

TYPE_ICONS = {
    "engagement": "[engage]",
    "content": "[content]",
    "launch": "[LAUNCH]",
    "setup": "[setup]",
    "prep": "[prep]",
    "outreach": "[outreach]",
    "maintenance": "[maint]",
    "analysis": "[analysis]",
}


def generate_calendar(start_date, num_weeks):
    lines = []
    lines.append("# Content Calendar")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Period: {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(weeks=num_weeks) - timedelta(days=1)).strftime('%Y-%m-%d')}")
    lines.append("")

    lines.append("## Legend")
    for type_name, icon in TYPE_ICONS.items():
        lines.append(f"- {icon} = {type_name}")
    lines.append("")

    for week_num in range(num_weeks):
        template = WEEKLY_TEMPLATES[week_num % len(WEEKLY_TEMPLATES)]
        week_start = start_date + timedelta(weeks=week_num)

        lines.append(f"---")
        lines.append(f"## Week {week_num + 1}: {template['theme']}")
        lines.append(f"**{week_start.strftime('%B %d')} - {(week_start + timedelta(days=6)).strftime('%B %d, %Y')}**")
        lines.append(f"**Goal:** {template['goal']}")
        lines.append("")

        day_offsets = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Weekend": 5,
        }

        for day_name, tasks in template["days"].items():
            offset = day_offsets.get(day_name, 0)
            day_date = week_start + timedelta(days=offset)
            if day_name == "Weekend":
                day_label = f"Sat-Sun ({day_date.strftime('%b %d')}-{(day_date + timedelta(days=1)).strftime('%b %d')})"
            else:
                day_label = f"{day_name} ({day_date.strftime('%b %d')})"

            lines.append(f"### {day_label}")
            for task in tasks:
                icon = TYPE_ICONS.get(task["type"], "")
                lines.append(f"- [ ] {icon} **{task['platform']}** — {task['action']} _{task['time']}_")
            lines.append("")

    # Summary stats
    total_tasks = sum(
        len(tasks)
        for week_num in range(num_weeks)
        for tasks in WEEKLY_TEMPLATES[week_num % len(WEEKLY_TEMPLATES)]["days"].values()
    )
    lines.append("---")
    lines.append("## Summary")
    lines.append(f"- **Total tasks:** {total_tasks}")
    lines.append(f"- **Weeks planned:** {num_weeks}")
    lines.append("")
    lines.append("## Time Estimates (weekly)")
    lines.append("| Channel | Hours/Week |")
    lines.append("|---------|-----------|")
    lines.append("| Reddit (answers + posts) | 3-5 |")
    lines.append("| Twitter/X (tweets + engagement) | 5-7 |")
    lines.append("| Blog writing | 4-6 |")
    lines.append("| Dev.to/Hashnode/Medium cross-posting | 1-2 |")
    lines.append("| Discord/Slack communities | 2-3 |")
    lines.append("| Newsletter outreach | 1-2 |")
    lines.append("| SEO + analytics | 2-3 |")
    lines.append("| **Total** | **18-28** |")
    lines.append("")

    lines.append("## Key Rules")
    lines.append("1. **Reddit 90/10 rule:** 90% genuine contributions, 10% promotional")
    lines.append("2. **Canonical URLs:** Always point cross-posted content back to your domain")
    lines.append("3. **Twitter links:** Put links in replies, not main tweets")
    lines.append("4. **HN etiquette:** Be humble, technical, and respond to every comment")
    lines.append("5. **Track everything:** UTM parameters on every link, measure what works")
    lines.append("6. **Engage authentically:** Help people first, promote second")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate content calendar")
    parser.add_argument("--weeks", "-w", type=int, default=4,
                        help="Number of weeks to plan (default: 4)")
    parser.add_argument("--start", "-s", type=str, default=None,
                        help="Start date YYYY-MM-DD (default: next Monday)")
    parser.add_argument("--save", action="store_true",
                        help="Save calendar to file")
    args = parser.parse_args()

    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start_date = today + timedelta(days=days_until_monday)

    calendar = generate_calendar(start_date, args.weeks)
    print(calendar)

    if args.save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = OUTPUT_DIR / f"calendar_{start_date.strftime('%Y%m%d')}_{args.weeks}w.md"
        with open(filename, "w") as f:
            f.write(calendar)
        print(f"\nSaved to: {filename}")


if __name__ == "__main__":
    main()
