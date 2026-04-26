import os
import pandas as pd
from exa_py import Exa
from groq import Groq
from pathlib import Path

# Load .env manually
_env = Path(__file__).parent / '.env'
if _env.exists():
    for _line in _env.read_text().splitlines():
        if '=' in _line and not _line.startswith('#'):
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

exa = Exa(api_key=os.environ["EXA_API_KEY"])
groq = Groq(api_key=os.environ["GROQ_API_KEY"])

COMPANIES = [
    {"name": "NedFOX", "url": "https://retailvista.io/en/"},
    {"name": "Jazzware", "url": "https://www.jazzware.com/"},
    {"name": "CoreCashless", "url": "https://www.corecashless.com/en"},
    {"name": "Ampliphi", "url": "https://www.getampliphi.com/"},
    {"name": "Servico", "url": "https://www.servico.be/"},
    {"name": "TigerTMS", "url": "https://www.tigertms.com/"},
    {"name": "CMS Hospitality", "url": "https://www.cmshospitality.com/"},
    {"name": "Thermeon", "url": "https://www.thermeon.com/"},
]


PROFILE_SITES = ("cbinsights.com", "crunchbase.com", "linkedin.com", "zoominfo.com", "owler.com", "pitchbook.com", "dnb.com", "rocketreach.co", "apollo.io", "signalhire.com")

def find_signal(company_name, company_url):
    query = f'"{company_name}" recent news OR hiring OR funding OR product launch'
    results = exa.search_and_contents(
        query=query,
        num_results=5,
        type="auto",
    )
    if not results.results:
        return {"text": "No signal found.", "url": company_url}
    name_key = company_name.lower().replace(" ", "")
    own_domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
    clean = [r for r in results.results if not any(site in r.url for site in PROFILE_SITES)]

    # 1. Prefer company's own domain
    for r in clean:
        if own_domain in r.url:
            text = (r.text or r.title or "No content available").strip()[:600]
            return {"text": text, "url": r.url}
    # 2. Prefer results with company name in URL or title (press releases, parent co announcements)
    for r in clean:
        if name_key in r.url.lower().replace(" ", "") or name_key in (r.title or "").lower().replace(" ", ""):
            text = (r.text or r.title or "No content available").strip()[:600]
            return {"text": text, "url": r.url}
    # 3. Fall back to first clean result
    if clean:
        text = (clean[0].text or clean[0].title or "No content available").strip()[:600]
        return {"text": text, "url": clean[0].url}
    top = results.results[0]
    text = (top.text or top.title or "No content available").strip()[:600]
    return {"text": text, "url": top.url}


def draft_email(company_name, signal):
    system_prompt = """You write cold outreach emails on behalf of an AI automation engineer who builds custom AI agents for vertical SaaS companies. His engagements are 4-6 weeks: he embeds, identifies the highest-ROI manual workflow, ships a working agent to production, and measures hours of labor replaced. He is not a consultant, not a software vendor — he writes code and ships agents.

Verticals he works with: hotel tech, car rental software, retail POS/ERP, field service management, hospitality SaaS, and similar niche B2B software companies.

Typical workflows he automates: tier-1 customer support, SDR outreach research, customer onboarding, documentation generation, renewal follow-ups.

Rules for every email:
- Open with the specific signal (the news, hiring move, or product launch) as the first sentence
- Reference the specific vertical the company operates in — sound like you know the industry
- Name a specific bottleneck that companies in that vertical hit when scaling (don't generalize)
- State the outcome concretely: hours saved, workflow shipped, agent in production
- 4 sentences max, under 80 words
- End with a specific question tied to their business — not "would you be open to a chat"
- No em-dashes. No "I wanted to reach out." No "I came across your company." No "I hope this finds you well." No "integration challenges." No "digital transformation." No "leverage AI." No "synergies."

Here are three examples of great emails:

---
Subject: NedFox + Valsoft — onboarding at scale?

Saw Valsoft acquired NedFox last week — retail POS rollouts post-acquisition usually mean a spike in new merchant onboarding with the same support headcount. I build AI agents for vertical SaaS teams that handle tier-1 onboarding tickets and setup walkthroughs end-to-end, typically replacing 20-30 hours of manual support per week within a 4-6 week engagement. Are your support reps currently handling onboarding steps that a well-trained agent could own?

---
Subject: Hiring SDRs at [Company] — what's their research process?

Noticed you're scaling your sales team with three new SDR hires. In hotel tech, reps usually spend the first hour of every day manually pulling property data and recent news before writing a single email. I ship AI agents that cut that to under 10 minutes per account, so reps start selling instead of researching. Is manual account research currently a bottleneck for your team?

---
Subject: [Company] Series B — CS team keeping up?

Saw you closed a Series B last month — in car rental software, that kind of growth usually means customer success is fielding the same renewal and upsell questions across hundreds of accounts with a team built for dozens. I build agents that handle tier-1 CS workflows end-to-end (renewal nudges, usage check-ins, support escalation routing) and get them to production in 4-6 weeks. Which part of your CS motion is most manual right now?

---

For the subject line: write an original subject for this specific company and signal. Do NOT copy or adapt the example subjects above. 5-8 words. Reference something concrete from the signal (the acquisition name, the product launched, the role they're hiring for, etc.). No "Quick question", no "Reaching out", no generic openers.

End with exactly ONE question. The final sentence must end with a single question mark. There must be no other question mark anywhere else in the email.

Now write one email for the company and signal provided. Return ONLY valid JSON with two keys: "subject" and "body". No markdown, no explanation."""

    user_prompt = f"""Company: {company_name}
Signal: {signal['text'][:400]}
Source: {signal['url']}

Write the cold email JSON now."""

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    import json
    parsed = json.loads(raw.strip())
    return {"subject": parsed["subject"], "body": parsed["body"]}


def main():
    results = []
    for c in COMPANIES:
        print(f"\n--- Processing {c['name']} ---")
        signal = find_signal(c['name'], c['url'])
        print(f"Signal: {signal['text'][:120]}...")
        print(f"Source: {signal['url']}")
        email = draft_email(c['name'], signal)
        print(f"Subject: {email['subject']}")
        print(f"Body:\n{email['body']}")
        results.append({
            "company": c['name'],
            "website": c['url'],
            "signal_found": signal['text'],
            "signal_url": signal['url'],
            "email_subject": email['subject'],
            "email_body": email['body'],
        })
    pd.DataFrame(results).to_csv('output.csv', index=False)
    print("\n--- Done. Results saved to output.csv ---")


if __name__ == '__main__':
    main()
