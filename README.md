# SDR Research Agent

A prototype AI agent that researches target companies and drafts personalized cold outreach emails. Built in 2 hours as a demo for an AI Automation Engineer application.

## What It Does

For each company in a target list, the agent:

1. Uses the Exa API to find a recent, specific signal — a press release, hiring announcement, product launch, or parent-company news.
2. Filters out low-signal sources (Crunchbase, ZoomInfo, and similar profile aggregators).
3. Calls Groq (Llama 3.3 70B) to draft a 3-4 sentence cold email that uses the signal as the hook and references the company's specific vertical.
4. Outputs results to `output.csv` and prints each email to the terminal as it runs.

## Stack

Plain Python, one file. Deliberately no orchestration framework — for a prototype with two tool calls per iteration, raw Python ships faster and is easier to debug live.

- `exa-py` for web research
- `groq` for the LLM (Llama 3.3 70B)
- `pandas` for CSV output

## Run It

```bash
pip install -r requirements.txt
# Add EXA_API_KEY and GROQ_API_KEY to a .env file
python agent.py
```

## Sample Output

**NedFOX** (retail POS software, Netherlands)

> **Subject:** Valsoft Acquires NedFox
>
> Saw Valsoft acquired NedFox last week — retail POS rollouts post-acquisition usually mean a spike in new merchant onboarding with the same support headcount. I build AI agents for vertical SaaS teams that handle tier-1 onboarding tickets and setup walkthroughs end-to-end, typically replacing 20-30 hours of manual support per week within a 4-6 week engagement. Are your support reps currently handling onboarding steps that a well-trained agent could own?

**Ampliphi** (AI-powered hotel revenue management)

> **Subject:** Ampliphi CMS Partnership
>
> Saw Ampliphi partner with CMS Hospitality recently — hotel tech companies often struggle with manual tier-1 customer support during rapid growth. I build AI agents that replace 20-30 hours of manual support per week. Are your customer support reps currently handling ticket volumes that could be automated?

## Edge Cases Observed

Servico, a small Belgian company, returned no English-language news during testing. The agent fell back to a generic vertical-level hook. In production this would be handled with language detection and a separate research path for non-English sources.

Three companies in the test set (Jazzware, CoreCashless, CMS Hospitality) had been recently acquired by Valsoft, which caused the agent to converge on similar hook phrasing across them. Production fix: a deduplication step that detects shared signals across the target list and forces angle diversity.

## What I'd Add Next

- Approval queue: drop drafts into a Google Sheet with approve/reject columns before any send action
- CRM logging: write approved emails to HubSpot or Salesforce via API
- Signal scoring: rank multiple signals per company and pick the strongest, not just the first
- Send integration: Gmail API send, with rate limiting and bounce handling
- Eval harness: track approval rate as the quality metric over time
- Angle deduplication: when multiple companies share a signal source (e.g., same parent acquisition), force the LLM to vary the hook angle

---

Built by Fawaz Ahmad — [portfolio](https://your-portfolio-url) | [github](https://github.com/your-handle)