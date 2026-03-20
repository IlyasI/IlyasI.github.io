#!/usr/bin/env python3
"""Generate platform-specific promotional posts from config.

Usage:
    python scripts/promote/draft-posts.py [--platform PLATFORM] [--topic TOPIC]
    python scripts/promote/draft-posts.py --all
    python scripts/promote/draft-posts.py --platform reddit --topic launch
    python scripts/promote/draft-posts.py --platform hackernews
    python scripts/promote/draft-posts.py --platform twitter --topic tips
    python scripts/promote/draft-posts.py --list-topics

Platforms: reddit, hackernews, twitter, devto, medium, all
Topics: launch, tips, story, technical, all (default: launch)
"""

import argparse
import textwrap
import sys
from datetime import datetime
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "drafts"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def wrap(text, width=72):
    return textwrap.fill(textwrap.dedent(text).strip(), width=width)


# ---------------------------------------------------------------------------
# Reddit posts
# ---------------------------------------------------------------------------

def draft_reddit_launch(cfg):
    product = cfg["product"]
    author = cfg["author"]
    posts = []

    # r/SideProject — showcase format
    posts.append({
        "platform": "reddit",
        "subreddit": "r/SideProject",
        "title": f"I built {product['name']} — my portfolio site as a senior fintech engineer",
        "body": textwrap.dedent(f"""\
            Hey everyone,

            I'm a senior software developer with 6+ years in fintech (platform
            infrastructure and trading systems). I recently rebuilt my portfolio
            site from scratch with vanilla HTML/CSS/JS — no frameworks, no
            dependencies.

            Some things I'm happy with:
            - Interactive particle simulation on canvas
            - Built-in terminal emulator
            - 3D card tilt effects
            - Dark/light theme switching
            - Perfect Lighthouse scores
            - Full accessibility testing with Playwright + axe-core

            Check it out: {product['url']}

            I'm open to feedback on the design, the interactions, or the content.
            Also happy to answer questions about building interactive portfolio
            sites without frameworks.

            Source: https://github.com/{author['github']}/{author['github']}.github.io
        """),
        "notes": "Post in r/SideProject — explicitly allows project sharing.",
    })

    # r/webdev — technical angle
    posts.append({
        "platform": "reddit",
        "subreddit": "r/webdev",
        "title": "Built an interactive portfolio with vanilla JS — particles, terminal emulator, 3D effects, zero dependencies",
        "body": textwrap.dedent(f"""\
            Wanted to share a portfolio site I built entirely with vanilla
            HTML/CSS/JS. No React, no build tools, no npm packages.

            Technical highlights:
            - Canvas-based particle simulation (200 particles with physics)
            - Functional terminal emulator
            - CSS custom properties for theming (light/dark)
            - 3D card tilt effect with pure CSS transforms
            - Scroll progress bar
            - Typing animation
            - Playwright + axe-core for automated accessibility testing
            - ESLint + Stylelint for code quality

            Live: {product['url']}
            Source: https://github.com/{author['github']}/{author['github']}.github.io

            I'd love to hear what you think, especially about the vanilla JS
            approach vs using a framework. For a portfolio site, I found
            frameworks added complexity without much benefit.
        """),
        "notes": "Focus on the technical implementation. r/webdev respects the no-framework approach.",
    })

    # r/cscareerquestions — career angle
    posts.append({
        "platform": "reddit",
        "subreddit": "r/cscareerquestions",
        "title": "After 6 years in fintech, here's what I've learned about standing out as a senior engineer",
        "body": textwrap.dedent("""\
            I've been working in financial technology for the past 6+ years,
            starting at a trading software company, moving to a quantitative
            hedge fund, and currently working at a large systematic trading
            firm.

            A few things I've learned along the way that might help others:

            1. **Platform work is underrated.** Building internal tools and
               infrastructure might seem less glamorous than product work, but
               it gives you incredibly broad exposure to the entire stack.

            2. **Operational ownership matters.** Oncall, incident response,
               and production debugging taught me more about systems than any
               design doc.

            3. **Data engineering skills compound.** Understanding how data
               flows through a system — from ingestion to analytics — makes
               you valuable everywhere.

            4. **GenAI is a real tool, not just hype.** I've built actual
               GenAI-powered systems in production. The key is knowing where
               LLMs add value vs where traditional approaches work better.

            5. **Your portfolio is your proof.** I rebuilt my portfolio site
               recently and it's been a great conversation starter in
               interviews.

            Happy to answer questions about fintech careers, senior engineer
            interviews, or the job market.
        """),
        "notes": "Value-first post. No direct product link in the body. Mention portfolio naturally. Answer questions and link if asked.",
    })

    return posts


def draft_reddit_tips(cfg):
    posts = []
    posts.append({
        "platform": "reddit",
        "subreddit": "r/cscareerquestions",
        "title": "System design interviews: patterns I've seen from both sides of the table",
        "body": textwrap.dedent("""\
            I've both taken and given system design interviews at fintech
            companies. Here are patterns that consistently separate strong
            candidates from average ones:

            **What strong candidates do:**
            - Start with clarifying requirements and capacity estimates
            - Draw the high-level architecture before diving into details
            - Explicitly call out trade-offs (consistency vs availability,
              latency vs throughput)
            - Reference real systems they've built, not just textbook answers
            - Discuss monitoring, alerting, and failure modes

            **Common mistakes:**
            - Jumping straight into database schema
            - Designing for Google scale when the prompt says "10K users"
            - Not asking about read/write ratio
            - Ignoring caching entirely
            - Over-engineering with microservices when a monolith is fine

            **The meta-skill:** The best candidates think out loud and treat
            the interview as a collaborative design session, not an exam.
            Interviewers want to see how you think, not whether you memorized
            the "right" architecture.

            Happy to elaborate on any of these. What patterns have you all
            noticed?
        """),
        "notes": "Pure value post. No promotion. Builds credibility and karma.",
    })
    return posts


# ---------------------------------------------------------------------------
# Hacker News posts
# ---------------------------------------------------------------------------

def draft_hn_launch(cfg):
    product = cfg["product"]
    author = cfg["author"]
    return [{
        "platform": "hackernews",
        "title": f"Show HN: Interactive portfolio built with vanilla JS — particles, terminal, 3D effects",
        "url": product["url"],
        "top_comment": textwrap.dedent(f"""\
            Hi HN, I'm Ilyas. I'm a senior software developer working in
            fintech (currently at Two Sigma). I rebuilt my portfolio site
            from scratch using only vanilla HTML, CSS, and JavaScript — no
            frameworks, no build tools, no dependencies.

            Some technical details:
            - 200-particle physics simulation on <canvas>
            - Functional terminal emulator (try typing 'help')
            - 3D card tilt with CSS transforms and pointer tracking
            - CSS custom properties for dark/light theming
            - Scroll-driven progress bar
            - Automated accessibility testing with Playwright + axe-core

            I wanted to see how far vanilla JS could go for an interactive
            site. The answer: pretty far. The entire JS is ~40KB unminified
            with zero external dependencies.

            Source code: https://github.com/{author['github']}/{author['github']}.github.io

            Would love feedback on the interactions and any performance
            concerns. I'm especially curious what HN thinks about the
            no-framework approach for this kind of site.
        """),
        "notes": textwrap.dedent("""\
            POST TIMING: Tuesday or Wednesday, ~9 AM EST.
            RULES:
            - Title must start with "Show HN:"
            - Link to the live site, not GitHub
            - Write the detailed comment IMMEDIATELY after posting
            - Respond to every comment, especially criticism
            - Be humble and technical, not promotional
        """),
    }]


# ---------------------------------------------------------------------------
# Twitter/X posts
# ---------------------------------------------------------------------------

def draft_twitter_launch(cfg):
    product = cfg["product"]
    author = cfg["author"]
    posts = []

    # Launch thread
    posts.append({
        "platform": "twitter",
        "type": "thread",
        "tweets": [
            f"I rebuilt my portfolio site from scratch with zero dependencies.\n\nNo React. No build tools. No npm.\n\nJust HTML, CSS, and vanilla JavaScript.\n\nHere's what I learned (thread):",
            "1/ Vanilla JS can do a LOT more than most devs think.\n\nI built a full particle physics simulation, a terminal emulator, and 3D card effects — all without a single framework.",
            "2/ The entire JavaScript is ~40KB unminified.\n\nFor comparison, a bare Create React App is ~200KB+ gzipped.\n\nFor a portfolio site, the framework IS the complexity.",
            "3/ CSS custom properties make theming trivial.\n\nDark mode, light mode, and the toggle — all handled with a few CSS variables and one class swap. No styled-components needed.",
            "4/ Playwright + axe-core for accessibility testing.\n\nAutomated a11y testing caught issues I never would have found manually. This should be standard for every portfolio site.",
            f"5/ The result: perfect Lighthouse scores and a site that loads instantly.\n\nCheck it out and let me know what you think:\n\n(link in reply)",
        ],
        "reply_with_link": product["url"],
        "hashtags": "#webdev #programming",
        "notes": "Post the link in a reply to tweet 5, not in the thread itself. This maximizes distribution.",
    })

    # Standalone tips (for ongoing posting)
    posts.append({
        "platform": "twitter",
        "type": "single",
        "tweet": "Hot take: for portfolio sites, the best framework is no framework.\n\nVanilla HTML/CSS/JS gives you:\n- Zero build step\n- Instant loads\n- Full control\n- Nothing to update\n\nFrameworks solve problems portfolio sites don't have.",
        "hashtags": "#webdev",
        "notes": "Standalone opinion tweet. Good for engagement/discussion.",
    })

    return posts


def draft_twitter_tips(cfg):
    posts = []
    tips = [
        "System design interview tip:\n\nAlways start with: 'What's the expected read/write ratio?'\n\nThis one question shapes your entire architecture — caching strategy, database choice, consistency model.\n\nMost candidates skip it. Don't.",
        "Interview prep tip that nobody talks about:\n\nPractice thinking out loud.\n\nThe algorithm is easy to study. Communicating your thought process while coding under pressure is the actual hard skill.\n\nRecord yourself solving problems. You'll cringe, then improve.",
        "After 6 years in fintech, here's my honest take on technical interviews:\n\nThe best interviews feel like pair programming with a future colleague.\n\nThe worst feel like exams.\n\nAs a candidate, you can shift the dynamic by asking questions, proposing alternatives, and treating it as a conversation.",
    ]
    for i, tip in enumerate(tips):
        posts.append({
            "platform": "twitter",
            "type": "single",
            "tweet": tip,
            "hashtags": "#codinginterview #softwareengineer",
            "notes": f"Tip tweet {i+1}. Post one per day. Builds credibility.",
        })
    return posts


# ---------------------------------------------------------------------------
# Dev.to posts
# ---------------------------------------------------------------------------

def draft_devto_launch(cfg):
    product = cfg["product"]
    author = cfg["author"]
    return [{
        "platform": "devto",
        "title": "I Built an Interactive Portfolio with Zero Dependencies — Here's How",
        "tags": ["webdev", "javascript", "css", "portfolio"],
        "canonical_url": f"{product['url']}/blog/zero-dependency-portfolio",
        "body": textwrap.dedent(f"""\
            ---
            title: I Built an Interactive Portfolio with Zero Dependencies — Here's How
            published: true
            tags: webdev, javascript, css, portfolio
            canonical_url: {product['url']}/blog/zero-dependency-portfolio
            ---

            I recently rebuilt my portfolio site using only vanilla HTML, CSS,
            and JavaScript. No React, no Next.js, no build tools, no npm.

            The result: an interactive site with particle physics, a terminal
            emulator, 3D effects, and perfect Lighthouse scores.

            ## Why No Framework?

            For a portfolio site, I found that frameworks added complexity
            without proportional benefit. The entire JavaScript is ~40KB
            unminified. A bare React setup would have been 5x that before
            writing a single component.

            ## Technical Highlights

            ### Particle Simulation
            200 particles with collision detection and mouse interaction,
            rendered on `<canvas>`. The physics runs at 60fps on most devices.

            ### Terminal Emulator
            A functional terminal you can type into. Try `help` for available
            commands. Built with a simple command parser and DOM manipulation.

            ### 3D Card Effects
            CSS `transform: perspective()` combined with pointer tracking
            creates a natural tilt effect on project cards.

            ### Dark/Light Theming
            CSS custom properties make this trivial. One class swap on
            `<body>` changes every color in the palette.

            ### Accessibility
            Automated testing with Playwright + axe-core catches a11y issues
            in CI. Every interactive element is keyboard-navigable.

            ## What I'd Do Differently

            - Add a service worker for offline support
            - Pre-render the particle canvas as a static image for
              initial load
            - Add a blog section (coming soon)

            ## Check It Out

            - Live: [{product['url']}]({product['url']})
            - Source: [GitHub](https://github.com/{author['github']}/{author['github']}.github.io)

            I'd love feedback, especially on the vanilla JS approach.
            What's your take — frameworks or no frameworks for portfolio sites?
        """),
        "notes": textwrap.dedent("""\
            IMPORTANT:
            - Set canonical_url to your own domain's blog post URL
            - Publish on your own blog FIRST, then cross-post to Dev.to
            - Engage with every comment
            - Cross-post to Hashnode and Medium with same canonical URL
        """),
    }]


def draft_devto_tips(cfg):
    return [{
        "platform": "devto",
        "title": "System Design Interview Patterns I've Seen From Both Sides",
        "tags": ["career", "interview", "systemdesign", "beginners"],
        "body": textwrap.dedent("""\
            ---
            title: System Design Interview Patterns I've Seen From Both Sides
            published: true
            tags: career, interview, systemdesign, beginners
            ---

            After 6 years in fintech, I've both taken and given system design
            interviews. Here are the patterns I've noticed.

            ## What Strong Candidates Do

            1. **Clarify requirements first.** "How many users? What's the
               read/write ratio? What are the latency requirements?" These
               questions show you think about systems practically.

            2. **Draw the architecture before diving in.** A whiteboard
               sketch of boxes and arrows grounds the conversation.

            3. **Call out trade-offs explicitly.** "We could use a cache here
               for lower latency, but we'd sacrifice consistency. Given the
               requirements, I think that's acceptable because..."

            4. **Reference real experience.** "At my current company, we
               faced a similar problem and solved it by..." This is gold.

            5. **Discuss failure modes.** "What happens if this service goes
               down? Here's how we'd handle it..." Shows operational maturity.

            ## Common Mistakes

            - Jumping into database schema without understanding the problem
            - Designing for Google scale when the prompt says 10K users
            - Ignoring caching entirely
            - Over-engineering with microservices when a monolith is fine
            - Not asking about read vs write patterns

            ## The Meta-Skill

            The best candidates treat the interview as a collaborative design
            session. They think out loud, ask questions, and iterate. The worst
            treat it as an exam where there's one "right" answer.

            Interviewers want to see your thought process. They already know
            the architecture. They want to see how you get there.

            ---

            What patterns have you noticed? I'd love to hear from others who
            have been on both sides.
        """),
        "notes": "Pure value content. No promotion. Builds authority for your profile.",
    }]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

GENERATORS = {
    "reddit": {"launch": draft_reddit_launch, "tips": draft_reddit_tips},
    "hackernews": {"launch": draft_hn_launch},
    "twitter": {"launch": draft_twitter_launch, "tips": draft_twitter_tips},
    "devto": {"launch": draft_devto_launch, "tips": draft_devto_tips},
}


def generate_posts(cfg, platform="all", topic="launch"):
    posts = []
    platforms = GENERATORS.keys() if platform == "all" else [platform]
    for plat in platforms:
        if plat not in GENERATORS:
            print(f"Unknown platform: {plat}", file=sys.stderr)
            continue
        topics = GENERATORS[plat].keys() if topic == "all" else [topic]
        for t in topics:
            if t in GENERATORS[plat]:
                posts.extend(GENERATORS[plat][t](cfg))
    return posts


def format_post(post, index):
    lines = []
    lines.append(f"{'=' * 70}")
    lines.append(f"POST #{index}")
    lines.append(f"{'=' * 70}")
    lines.append(f"Platform:  {post['platform']}")
    if "subreddit" in post:
        lines.append(f"Subreddit: {post['subreddit']}")
    if "type" in post:
        lines.append(f"Type:      {post['type']}")
    lines.append(f"{'─' * 70}")

    if "title" in post:
        lines.append(f"TITLE: {post['title']}")
        lines.append("")

    if "tweets" in post:
        for i, tweet in enumerate(post["tweets"]):
            lines.append(f"  Tweet {i+1}/{len(post['tweets'])}:")
            lines.append(textwrap.indent(tweet, "    "))
            lines.append("")
        if "reply_with_link" in post:
            lines.append(f"  Reply with link: {post['reply_with_link']}")
    elif "tweet" in post:
        lines.append(post["tweet"])
    elif "body" in post:
        lines.append(post["body"])
    elif "top_comment" in post:
        if "url" in post:
            lines.append(f"URL: {post['url']}")
            lines.append("")
        lines.append("TOP COMMENT:")
        lines.append(post["top_comment"])

    if "hashtags" in post:
        lines.append(f"\nHashtags: {post['hashtags']}")
    if "tags" in post:
        lines.append(f"\nTags: {', '.join(post['tags'])}")

    lines.append(f"\n{'─' * 70}")
    lines.append("NOTES:")
    lines.append(post.get("notes", "None"))
    lines.append("")

    return "\n".join(lines)


def save_drafts(posts, platform, topic):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"drafts_{platform}_{topic}_{timestamp}.md"

    with open(filename, "w") as f:
        f.write(f"# Draft Posts — {platform} / {topic}\n")
        f.write(f"# Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for i, post in enumerate(posts, 1):
            f.write(format_post(post, i))
            f.write("\n")

    return filename


def main():
    parser = argparse.ArgumentParser(description="Generate promotional post drafts")
    parser.add_argument("--platform", "-p", default="all",
                        choices=["reddit", "hackernews", "twitter", "devto", "medium", "all"],
                        help="Target platform (default: all)")
    parser.add_argument("--topic", "-t", default="launch",
                        choices=["launch", "tips", "story", "technical", "all"],
                        help="Post topic (default: launch)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Generate all posts for all platforms and topics")
    parser.add_argument("--save", "-s", action="store_true",
                        help="Save drafts to file")
    parser.add_argument("--list-topics", action="store_true",
                        help="List available topics per platform")
    args = parser.parse_args()

    if args.list_topics:
        for plat, topics in GENERATORS.items():
            print(f"{plat}: {', '.join(topics.keys())}")
        return

    if args.all:
        args.platform = "all"
        args.topic = "all"

    cfg = load_config()
    posts = generate_posts(cfg, args.platform, args.topic)

    if not posts:
        print(f"No posts generated for platform={args.platform}, topic={args.topic}")
        print("Use --list-topics to see available combinations.")
        return

    for i, post in enumerate(posts, 1):
        print(format_post(post, i))

    if args.save:
        filename = save_drafts(posts, args.platform, args.topic)
        print(f"\nDrafts saved to: {filename}")

    print(f"\nGenerated {len(posts)} post(s).")


if __name__ == "__main__":
    main()
