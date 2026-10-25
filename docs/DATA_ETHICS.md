# IntimaGuard — Data Ethics & Privacy Policy

> **Research archive note:** This document describes the data ethics and privacy policy designed for the IntimaGuard evaluation platform. The platform was never publicly launched, and no evaluation data was collected under this policy. It is published as a record of the intended data governance design — useful if this work is continued or adapted.

**Version:** 0.1 (Phase 0)  
**Scope:** Platform evaluation data collected via intimaguard.dev (and any staging environments)  
**Last updated:** April 2026

---

## Summary

IntimaGuard collects human evaluation data to build a validated dataset for assessing AI behavior in intimate and relational contexts. This document explains what we collect, what we never collect, why geographic scope is restricted, how data is stored, and how the public dataset is structured.

---

## 1. Geographic Scope

**Phase 0–2 (current): United States residents only.**

The platform geo-blocks requests originating from the European Union and Brazil. This is a deliberate legal boundary, not a technical limitation:

- **EU**: GDPR (Regulation (EU) 2016/679) imposes data subject rights, consent requirements, and cross-border transfer restrictions that require a legal structure we have not yet established. We will revisit EU access at Phase 2 when governance, a DPA, and legal counsel are in place.
- **Brazil**: LGPD (Lei Geral de Proteção de Dados, Law 13,709/2018) creates parallel obligations. Same rationale as EU.
- **Other jurisdictions**: US-only scope is enforced by IP-based geo-blocking. VPN use to circumvent the geo-block violates the Terms of Use.

Self-attestation is required: evaluators must confirm they are US residents before beginning a session. This is not identity verification — it is a terms-of-use agreement that creates a legal basis for our US-only data collection posture.

---

## 2. What We Collect

### Per evaluation session:

| Field | What is stored | Notes |
|---|---|---|
| Scores | Per-dimension score (1–5) for each AI response | Core dataset |
| Emotional response | Affect checkbox selection (Supported / Comfortable / Uneasy / Unsettled / Concerned) | Per response |
| Open concern flag | Optional free-text field at session end | Stored as-is; not linked to identity |
| Session metadata | Timestamp, scenario ID, model evaluated, framework version | Required for dataset validity |
| Evaluator context (optional) | Age range (decade buckets: 18–24, 25–34, etc.), relationship status category, AI familiarity level, companion AI app use (yes/no) | Voluntary; demographic ranges only — never exact age |

### Via the SDK (developer use):

| Field | What is stored | Notes |
|---|---|---|
| SDK evaluation results | Scores, flags, composite score, model ID, framework version | Stored in `sdk_evaluations` table |
| Conversation content | The conversation submitted for evaluation | Stored to support audit and research use |
| API key identifier | Hashed key ID | For rate limiting and abuse prevention; not linked to identity |

---

## 3. What We Never Collect

- **Name, email, or any identity-linked field** — the platform has no login, no account creation, and no persistent user identity
- **Exact age** — only decade-bucket ranges (18–24, 25–34, etc.)
- **Precise location** — IP address is used for geo-blocking and then discarded; city/region/ZIP are never stored
- **Device fingerprints** — no cross-session tracking
- **Conversation content from the human evaluation platform** — evaluators score pre-written scenarios; their own words are not collected except in the optional open concern field

---

## 4. Data Storage

All platform data is stored in Supabase (US-East region) with Row-Level Security (RLS) enabled on all tables. No evaluation record is linkable to an individual. Supabase stores data in the United States.

SDK evaluation data is stored in the same Supabase instance. Developers who submit conversation data via the SDK are responsible for ensuring they have appropriate consent from the users whose conversations they submit.

---

## 5. Public Dataset

IntimaGuard publishes aggregated evaluation results as an open dataset. The public dataset:

- **Contains:** Aggregated per-dimension scores by model, scenario type, and evaluator demographic range; distribution statistics; flag frequency counts
- **Does not contain:** Any individual evaluation record, any free-text open concern responses, any data that could identify an individual evaluator
- **Release cadence:** Quarterly (beginning Phase 1)
- **License:** Apache 2.0 — the public dataset is freely usable for research and commercial purposes with attribution

Raw evaluation records are never made public. Researchers who want access to non-aggregated data for academic research should contact us — we will evaluate requests against IRB requirements and data minimization principles.

---

## 6. Retention

| Data type | Retention |
|---|---|
| Platform evaluation records | Indefinite (core research dataset) |
| SDK evaluation records | 2 years from submission, then purged |
| Open concern free-text | 2 years from submission, then purged |
| IP addresses (geo-block check) | Not stored after the request is processed |

Retention policy will be reviewed at Phase 2 when legal counsel reviews the full data governance framework.

---

## 7. Developer Responsibilities (SDK)

If you use the IntimaGuard SDK or API to evaluate conversations from your users:

1. You are the data controller for those conversations. IntimaGuard is a data processor.
2. You are responsible for obtaining appropriate consent from your users before submitting their conversations for evaluation.
3. You should not submit conversations containing sensitive personal data (health information, financial information, government IDs) beyond what is necessary for the evaluation.
4. You must comply with applicable law in your jurisdiction — including CCPA if you operate in California, which you likely do given SB 243.

---

## 8. California SB 243 Alignment

California SB 243 (effective January 1, 2026) requires companion chatbot operators to implement evidence-based suicidal ideation measurement and publish crisis-prevention protocols. IntimaGuard's Distress Routing dimension directly addresses this requirement.

If you are using IntimaGuard certification as SB 243 compliance evidence:
- The audit report documents your crisis-referral methodology and is designed to be presentable to CDPH.
- Annual reporting to CDPH begins July 1, 2027 — your audit report should include crisis-referral logging methodology sufficient for that reporting obligation.

---

## 9. Changes to This Policy

Material changes will be announced via the project's GitHub repository. The version number and date at the top of this document will be updated. Prior versions are preserved in git history.

---

## Contact

Data ethics questions, researcher data access requests, and security disclosures:  
Open an issue at `github.com/belencito27/intimaguard` with the `[data-ethics]` label, or email the project maintainer via the contact listed in the repository.
