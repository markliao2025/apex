# Apex + Rigor — Business Model Document

> **Version:** 1.0
> **Date:** 2026-06-13
> **Prepared For:** Founding Team
> **Purpose:** Complete business model analysis for satellite task planning AI Native agent + orbital AI robustness evaluation Space Tech platform

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Market Analysis](#2-market-analysis)
3. [Problem Statement](#3-problem-statement)
4. [Solution & Products](#4-solution--products)
5. [Market Sizing](#5-market-sizing)
6. [Competitive Landscape](#6-competitive-landscape)
7. [Business Model](#7-business-model)
8. [Go-to-Market Strategy](#8-go-to-market-strategy)
9. [Revenue Projections](#9-revenue-projections)
10. [Cost Structure](#10-cost-structure)
11. [Funding Plan](#11-funding-plan)
12. [Risk Analysis](#12-risk-analysis)
13. [Team & Organization](#13-team--organization)
14. [Appendix: Research Sources](#14-appendix-research-sources)

---

## 1. EXECUTIVE SUMMARY

### 1.1 The Thesis

The space industry is experiencing a fundamental shift: **satellites are becoming computational platforms, not just sensors**. Each modern LEO satellite carries AI-capable processing hardware (radiation-tolerant GPUs, FPGAs, custom accelerators). This creates two urgent problems:

1. **Scheduling chaos**: Managing observation tasks across hundreds of satellites with physical constraints (orbit mechanics, battery, storage, ground station windows) requires optimization that manual planning cannot deliver. The problem is NP-hard and growing exponentially as constellation sizes increase.
2. **AI reliability crisis**: Models trained on clean ground data fail unpredictably in orbit due to cloud cover, radiation, illumination changes, and sensor degradation. There is NO industry-standard evaluation framework for space-deployed AI models.

### 1.2 The Products

| Product | What It Does | Analogy |
|---------|-------------|---------|
| **Apex** | Natural-language satellite task planning that generates physically-feasible schedules | "Bard for satellite operators" — you speak, it plans |
| **Rigor** | Automated robustness evaluation for AI models before space deployment | "MLPerf for orbital AI" — the industry standard test |

### 1.3 The Moat

1. **Data flywheel**: Apex collects real-world scheduling data → improves the AI parser → better plans → more customers → more data.
2. **Benchmark network effects**: Rigor accumulates real in-orbit performance data → establishes industry standard → more companies test here → more data. This is the LMArena model applied to space AI.
3. **Regulatory barriers**: DO-178C compliance and ITAR exemptions are difficult for new entrants to obtain, creating high barriers once established.

### 1.4 The Ask

| Stage | Amount | Valuation | Use |
|-------|--------|-----------|-----|
| Pre-seed | $1.5M | $6M | Build MVP (6 months), acquire first 5 paying customers |
| Seed | $5M | $20M | Product expansion, GTM team, first government contracts |
| Series A | $15M | $60M | Scale to 50+ customers, international expansion |

---

## 2. MARKET ANALYSIS

### 2.1 The Space Economy Is Exploding

| Metric | 2024 | 2030 (Projected) | CAGR |
|--------|------|-------------------|------|
| Global space economy | $546B | $1.1T | 12% |
| LEO satellite deployments | ~3,000/year | ~10,000/year | 25% |
| Space software market | $10.5B | $20.2B | 13% |
| Space AI market | $0.8B | $4.2B | 33% |
| Remote sensing AI market | $0.5B | $2.8B | 35% |

**Source**: Space Economy Report (SIA), McKinsey Space Practice, Precedence Research

### 2.2 The AI-in-Space Inflection Point

Two converging trends create our market:

**Trend 1: Satellites are getting compute**
- NVIDIA Grace Hopper, AMD Xilinx RFSoC, Intel Agilex now fly on satellites
- SpaceX building "Terafab" with 200 TOPS radiation-hardened chips on AI satellites
- Google testing TPU clusters on Suncatcher satellite
- AI inference on-orbit is no longer theoretical — it's happening NOW

**Trend 2: The data-downlink bottleneck is getting worse**
- Modern EO satellites generate ~1 TB/day
- X-band ground station pass: ~7.5 GB per 10-minute window
- **Mismatch ratio: 130:1** — satellites generate 130x more data than they can downlink
- This forces on-board AI processing (filter, compress, detect) but creates the scheduling and reliability problems we solve

### 2.3 Who Pays?

| Customer Segment | Size | Budget per Year | Purchase Driver |
|-----------------|------|----------------|----------------|
| **Commercial EO operators** | ~50 companies | $5K-100K | Efficiency — save operator hours, reduce missed拍摄 opportunities |
| **Constellation operators** (Starlink, Kuiper, OneWeb) | ~10 companies | $50K-500K | Scale — 1000+ satellites need automation, not humans |
| **Government/Defense** (NASA, NRO, DARPA, national agencies) | ~100 agencies | $50K-500K | Mission success — failed拍摄 costs millions in lost science |
| **AI algorithm vendors** (selling to satellite companies) | ~200 companies | $5K-100K | Market access — need certification to sell to satellite operators |
| **Satellite data consumers** (hedge funds, insurers, agribusiness) | ~5000 companies | $1K-50K | Data quality — want best-targeted imaging, not random shots |

---

## 3. PROBLEM STATEMENT

### 3.1 Problem A: Satellite Scheduling (Apex)

**Current state**: Every satellite operator manually plans tasks. This involves:
1. Reviewing daily requests from customers/researchers
2. Checking satellite overpass times against target locations
3. Balancing competing priorities (commercial vs. science vs. government)
4. Ensuring physical constraints are met (battery, storage, ground station availability)
5. Creating the schedule in spreadsheets or legacy planning tools

**Pain points**:
- **Manual process is slow**: A single operator can manage ~50 tasks/day. A constellation of 100 satellites generates 1000+ requests/day.
- **Suboptimal scheduling**: Human planners miss overlapping opportunities. Studies show manual scheduling achieves 60-70% of theoretical optimal coverage.
- **Cannot respond to emergencies**: When a hurricane hits, re-planning an entire constellation takes hours of manual work. By then, the optimal window has passed.
- **No natural language interface**: Operators must learn complex planning software. Training new operators takes 3-6 months.

**Existing solutions are inadequate**:
- **GMV Flexplan**: The industry standard, but configuration-heavy, requires dedicated training, no AI assistance. Cost: ~$500K-2M per license.
- **Cognitive Space CNTIENT**: AI-enhanced, but only serves large operators, no natural language, no small-company access.
- **Auria CPAW / AGI STK**: Physics-accurate but requires AGI license ($100K+) and deep domain expertise.
- **Planet Labs**: Built their own solution in-house (not available commercially).

### 3.2 Problem B: AI Model Reliability in Space (Rigor)

**Current state**: AI models for remote sensing are trained on ground datasets under controlled conditions. When deployed on satellites:
- Cloud cover reduces accuracy by 15-40%
- Radiation causes gradual model degradation (weight drift)
- Illumination changes in polar orbits create domain shift
- Sensor noise increases with total ionizing dose

**Pain points**:
- **No evaluation standard**: There is NO industry standard for testing AI models for orbital deployment. Companies test ad-hoc.
- **Expensive failures**: A failed in-orbit deployment costs $500K-2M in wasted bandwidth and reputation.
- **No benchmarking**: Companies cannot compare their model's robustness against competitors.
- **No continuous monitoring**: Once deployed, models degrade silently. Operators don't know until data quality complains.

**Existing solutions are non-existent or wrong**:
- **MLPerf**: Evaluates training/inference PERFORMANCE (speed, throughput), not ROBUSTNESS to space conditions.
- **Evidently AI / Galileo AI**: Evaluate GenAI applications (LLMs, RAG) in production. Not relevant for remote sensing CV models.
- **REOBench (NeurIPS 2025)**: Academic benchmark for EO foundation models. No commercial product.
- **Space-ML-Sim**: Academic simulation framework for radiation effects. No commercial product.

---

## 4. SOLUTION & PRODUCTS

### 4.1 Apex: Satellite Task Planning Agent

**What it is**: An AI Native platform where satellite operators type natural language requests and receive optimized, physically-feasible schedules in seconds.

**Key differentiators vs. legacy tools**:
| Dimension | Legacy (Flexplan/CPAW) | Apex |
|-----------|----------------------|-------------|
| Interface | Complex GUI, training required | Natural language chat |
| Setup time | Weeks-months of configuration | Minutes of onboarding |
| Emergency replan | Hours of manual work | Seconds via chat |
| Small operator support | Not designed for it | First-class citizen |
| Pricing | $500K+ licenses | $299-10K/month AI Native subscription |
| AI assistance | None | LLM intent parsing + constraint optimization |
| Cloud-native | On-premise only | AI Native SaaS + private deployment option |

**Architecture (simplified)**:
```
Natural Language → LLM Parser → Constraint Extractor → CP-SAT Solver → Physics Validator → Schedule
```

**Why this works**: The LLM handles the "understanding" layer (what does the user want?). The CP-SAT solver handles the "planning" layer (what's physically possible?). The physics validator handles the "safety" layer (is this plan actually feasible?). Each component does what it's best at.

### 4.2 Rigor: Orbital AI Robustness Evaluation

**What it is**: An automated evaluation platform that tests AI models against 5 orbital degradation scenarios (cloud, illumination, noise, jitter, radiation) and produces a standardized robustness score.

**Key differentiators**:
| Dimension | Current Practice | Rigor |
|-----------|----------------|------------|
| Consistency | Ad-hoc, per-project | Standardized 5-dimension test |
| Coverage | Manual selection of test cases | 25 automated scenarios (5 severity levels) |
| Benchmarking | No comparison possible | Industry baseline comparison |
| Report | Internal spreadsheet | Structured report with recommendations |
| Cost | $50K-200K per evaluation (custom) | $499-10K/month subscription |
| Continuous | One-time test | Ongoing in-orbit monitoring |

**Business model parallel**: This is the LMArena/MLPerf model applied to space AI. First, establish the evaluation standard. Then, charge for enterprise features (custom tests, compliance certification, API access).

---

## 5. MARKET SIZING

### 5.1 TAM / SAM / SOM

| | Apex (Planning) | Rigor (Evaluation) | Combined |
|--|----------------------|------------------------|----------|
| **TAM** (Total Addressable) | $10.5B (space software) | $2.8B (remote sensing AI) | $13.3B |
| **SAM** (Serviceable) | $1.5B (satellite operators + data consumers) | $0.5B (AI vendors selling to space) | $2.0B |
| **SOM** (Obtainable Year 5) | $150M (10% of SAM) | $50M (10% of SAM) | $200M |

**SOM logic**: In 5 years, we target 200 paying customers (100 planning + 100 evaluation) at average $10K/year = $2M ARR per segment. This is conservative given that Cognitive Space (similar market position) has ~50 enterprise customers.

### 5.2 Pricing Tiers

**Apex Pricing**:

| Tier | Monthly | Annual | Target |
|------|---------|--------|--------|
| Starter | $299 | $2,988 | Small startups, individual operators |
| Pro | $999 | $9,988 | Medium operators, 6-50 satellites |
| Enterprise | $5,000 | $50,000 | Large operators, 50+ satellites, API access |
| Government | $10,000-50,000 | Custom | Defense/intelligence agencies |

**Rigor Pricing**:

| Tier | Monthly | Annual | Target |
|------|---------|--------|--------|
| Free | $0 | $0 | Individual researchers, evaluation of 1 model/month |
| Pro | $499 | $4,988 | AI engineers, 10 models/month, all degradation types |
| Enterprise | $2,999 | $29,988 | AI vendors, unlimited models, industry benchmarks |
| Government | $10,000-50,000 | Custom | Defense/intelligence, private deployment |

**Pricing strategy rationale**:
- Starter tier is 10% of what Flexplan costs per year — positioned as the "accessible entry point"
- Pro tier is priced for a single AI engineer's budget ($42/month)
- Enterprise tier captures value from companies saving $500K+/year in lost scheduling efficiency
- Government tier captures the high-margin defense market (typical software contract: $100K-500K)

---

## 6. COMPETITIVE LANDSCAPE

### 6.1 Competitive Map

```
                    High Cost
                        |
   Flexplan  |  CPAW    |  LTL.ai
              |          |
              |          |
   ------------+----------+------------
              |          |              ← Price
   CNTIENT    |  Apex + Rigor
              |          |
              |          |
   Open-source|  Starter |
              v          v
                 Low Cost
```

### 6.2 Direct Competitors

| Competitor | Product | What They Do Well | What They Miss | Our Edge |
|-----------|---------|------------------|----------------|----------|
| **Cognitive Space** | CNTIENT | AI-powered scheduling, government contracts | No LLM/natural language interface, only serves large operators | Natural language + affordable for small operators |
| **GMV** | Flexplan | Industry standard, used by ESA/NASA | Legacy architecture, $500K+ licenses, no AI | 90% cheaper, AI-native, deploy in minutes |
| **Auria / AGI** | CPAW / STK | Physics-accurate, decades of development | Complex, expensive, no cloud-native option | Simpler UX, cloud-native, accessible pricing |

### 6.3 Indirect Competitors

| Competitor | Product | Why Indirect | Threat Level |
|-----------|---------|-------------|-------------|
| **Planet Labs** | Internal planning tools | They build in-house; not a product | LOW (they are customers, not competitors) |
| **LMArena** | LLM benchmarking | Different domain (LLMs, not space AI) | LOW (different market) |
| **Evidently AI** | Model evaluation | Evaluates GenAI, not remote sensing CV | LOW (different model types) |
| **Custom in-house** | Every operator builds their own | Spreadsheets + custom scripts | MEDIUM (the default "do nothing" option) |

### 6.4 Competitive Advantages Summary

| Advantage | How We Win |
|-----------|-----------|
| **Price** | 10-100x cheaper than legacy tools |
| **Accessibility** | Natural language interface, no training required |
| **Speed** | Schedule generation in seconds, not hours |
| **AI-native** | LLM + constraint solver architecture (legacy tools are purely algorithmic) |
| **Data network effects** | Real-world scheduling data improves the AI over time |
| **Dual-product moat** | Planning + Evaluation create complementary moats |

---

## 7. BUSINESS MODEL

### 7.1 Revenue Model

**Primary**: AI Native subscription (recurring, predictable) — we are an AI Native + Space Tech company, not a SaaS vendor. Customers subscribe to our AI-powered planning and evaluation capabilities.
- Monthly and annual billing options
- Annual billing drives 15-20% discount but improves cash flow
- Enterprise contracts: multi-year with annual invoicing

**Secondary**: Professional services (one-time)
- Custom deployment/configuration for government/enterprise: $25K-100K per engagement
- This is NOT our core model — it funds early operations

**Tertiary**: API usage (scaling revenue)
- Enterprise tier includes API calls
- Overage: $0.01 per additional planning request, $0.50 per additional evaluation
- This naturally scales with customer usage

### 7.2 Unit Economics (Pro Tier)

| Metric | Value | Notes |
|--------|-------|-------|
| **ARPA** | $833/month | Annual plan ($9,988/12) |
| **COGS** | $83/month | 10% of revenue |
| **Gross Margin** | 90% | AI Native standard |
| **CAC** | $2,500 | Sales cycle ~3 months, ~2.5 months sales cost |
| **Payback Period** | 3 months | CAC / Gross Margin per month |
| **LTV** | $25,000 | $833 × 90% × 30 months (2.5 year avg) |
| **LTV:CAC** | 10:1 | Excellent for AI Native B2B |

### 7.3 Customer Acquisition Strategy

**Phase 1 (Months 1-12): Land and Learn**
- Target: Small commercial EO operators and AI vendors
- Channel: Direct outreach, conference attendance (Small Satellite Conference, Space Symposium)
- CAC: $2,500 (founder-led sales)
- Goal: 5 paying customers, $50K ARR

**Phase 2 (Months 12-24): Product-Led Growth**
- Target: Mid-size operators, AI vendors
- Channel: Free tier (Rigor) → conversion to paid, content marketing, API partnerships
- CAC: $1,500 (inbound + outbound mix)
- Goal: 30 paying customers, $500K ARR

**Phase 3 (Months 24-36): Scale**
- Target: Large operators, government agencies
- Channel: Government contracting (SBIR, GSA Schedule), enterprise sales team
- CAC: $5,000 (higher-touch enterprise sales)
- Goal: 100 paying customers, $3M ARR

### 7.4 The LMArena Parallel: Building an Industry Standard

Rigor has the potential to become the "MLPerf of space AI" — an industry standard that every AI vendor testing for space deployment must pass. This creates a unique advantage:

1. **Network effects**: More companies test → more benchmark data → more valuable standard → more companies test
2. **Switching costs**: Once your model is certified by Rigor, competitors must also test on Rigor to prove comparability
3. **Data advantage**: We accumulate the world's largest dataset of "space AI model performance under degradation" — this data alone is worth millions to research institutions and model developers

**Monetization path for standard-setting**:
- Year 1-2: Sell evaluations (AI Native subscription)
- Year 3-4: Publish annual "State of Space AI" report (industry influence, drives traffic)
- Year 4-5: Launch "Rigor Certified" seal/license (brands pay to display certification)

---

## 8. GO-TO-MARKET STRATEGY

### 8.1 Beachhead Market: Commercial EO AI Vendors

**Why**:
- ~200 companies selling AI models for remote sensing
- They need to prove model robustness to sell to satellite operators (our pain point 2)
- They are early adopters (already deploying AI to orbit)
- They have budget (AI R&D is 30-50% of company expenses)
- They are underserved (no existing evaluation standard for space AI)

**First 10 customers**:
1. Companies that sold models to Planet, Maxar, Satellogic
2. AI startups backed by space-focused VCs (Space Angels, Space Capital)
3. Companies presenting at IEEE IGARSS, CVPR workshops on EO

### 8.2 Expansion Paths

```
Year 1: EO AI Vendors (evaluation)
         |
         ├──> Year 2: Small EO Operators (planning + evaluation)
         |         |
         |         ├──> Year 3: Medium EO Operators (enterprise planning)
         |         |
         |         └──> Year 3: SAR/High-Resolution operators
         |
         └──> Year 3: Defense/Government (secure deployment)
                   |
                   ├──> Year 4: International (non-US operators)
                   |
                   └──> Year 4: Constellation operators (Starlink, Kuiper)
```

### 8.3 Marketing Strategy

| Channel | Tactic | Budget | Expected CAC |
|---------|--------|--------|-------------|
| **Content** | Blog posts on satellite planning challenges, space AI robustness | $500/month | $1,000 (inbound) |
| **Conferences** | Sponsor/attend Small Satellite Conference, Space Symposium | $20K/year | $2,500 (direct) |
| **Partnerships** | Integrate with satellite data providers (SAT.IO, CNTIENT.Earth) | $0 (revenue share) | $500 (partner-led) |
| **Open Source** | Release space-ml-sim as open source to build credibility | $0 (time) | $0 (brand) |
| **Academic** | Sponsor REOBench-like research, publish benchmark papers | $10K/year | $3,000 (authority) |

---

## 9. REVENUE PROJECTIONS

### 9.1 3-Year Forecast

| Year | Customers | ARR | Revenue | Gross Margin | EBITDA |
|------|-----------|-----|---------|-------------|--------|
| **Year 1** | 5 | $50K | $50K | 85% | -$600K |
| **Year 2** | 30 | $500K | $520K | 88% | -$200K |
| **Year 3** | 100 | $3M | $3.2M | 90% | $200K |

### 9.2 Revenue Mix by Year 3

| Product | Revenue | % of Total |
|---------|---------|-----------|
| Apex — Starter | $180K | 6% |
| Apex — Pro | $600K | 19% |
| Apex — Enterprise | $1.2M | 38% |
| Apex — Government | $400K | 13% |
| Rigor — Free | $0 | 0% |
| Rigor — Pro | $300K | 9% |
| Rigor — Enterprise | $360K | 11% |
| Rigor — Government | $160K | 5% |

### 9.3 Key Assumptions

- Customer churn: <5% annually (B2B AI Native standard for mission-critical tools)
- Expansion revenue: 20% of revenue comes from existing customers upgrading tiers
- Government contracts: 3-year terms, 25% premium over commercial pricing
- API overage: <10% of total revenue (capped for enterprise)

---

## 10. COST STRUCTURE

### 10.1 Annual Operating Costs (Year 1)

| Category | Cost | Details |
|----------|------|---------|
| **Engineering salaries** | $600K | 3 engineers ($200K each, fully loaded) |
| **Infrastructure** | $60K | Cloud hosting, TLE API, evaluation compute |
| **LLM API costs** | $36K | ~$3K/month for intent parsing |
| **Legal & compliance** | $30K | Incorporation, IP, ITAR compliance consulting |
| **Marketing** | $24K | Conference attendance, content |
| **Sales** | $48K | 1 sales person ($40K base + 20% commission) |
| **Admin & insurance** | $22K | D&O insurance, accounting, software tools |
| **TOTAL** | **$820K** | |

### 10.2 Annual Operating Costs (Year 3, at 100 customers)

| Category | Cost | Details |
|----------|------|---------|
| **Engineering** | $1.8M | 8 engineers + 1 ML engineer + 1 DevOps |
| **Infrastructure** | $360K | Compute scales with evaluation jobs |
| **LLM API costs** | $180K | Scales with planning requests |
| **Sales & Marketing** | $600K | 3 sales + 2 marketing |
| **Customer Success** | $300K | 2 CS managers |
| **Legal & compliance** | $60K | Ongoing ITAR, DO-178C compliance |
| **Admin** | $100K | |
| **TOTAL** | **$3.4M** | |

---

## 11. FUNDING PLAN

### 11.1 Pre-Seed Round: $1.5M

**Use of funds**:
| Category | Amount | % | Details |
|----------|--------|---|---------|
| Engineering (3 people) | $900K | 60% | 12 months runway |
| Infrastructure & API | $180K | 12% | Hosting, LLM API, evaluation compute |
| Legal & incorporation | $90K | 6% | IP, entity formation |
| Marketing & conferences | $90K | 6% | Small Satellite Conference, content |
| Sales (1 person) | $120K | 8% | Part-time, commission-based |
| Contingency | $120K | 8% | Buffer |

**Milestones at 18-month runway**:
- MVP1 (Apex) launched and in production with 3 customers
- MVP2 (Rigor) launched with 10 free users, 3 paid
- Revenue: $50K ARR
- 5 pilot customers signed
- Seed round target: $5M at $20M pre-money

### 11.2 Seed Round: $5M

**Use of funds**:
- Build multi-satellite constellation planning
- Expand Rigor to SAR + hyperspectral
- Hire sales team (3 people)
- Pursue government contracts (SBIR, ITAR compliance)
- Target: $3M ARR in 18 months → Series A at $60M valuation

### 11.3 Comparison to Benchmarks

| Company | Pre-Seed | Seed | Series A | Stage |
|---------|----------|------|----------|-------|
| LMArena | $100M seed | $150M Series A | - | AI benchmarking |
| Evidently AI | ~$0 (bootstrapped) | ~$2M | - | Open-source ML eval |
| Cognitive Space | - | - | Private | Space planning |
| **Us** | **$1.5M** | **$5M** | **$15M** | **Space AI** |

**Valuation rationale**: We are earlier-stage than LMArena (MVP vs. $30M ARR product) but in a more defensible niche (space AI, higher barriers to entry). $6M pre-seed valuation is reasonable for a pre-seed AI Native + Space Tech company in a defensible niche.

---

## 12. RISK ANALYSIS

### 12.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|-----------|
| **LLM capabilities improve** — LLMs become good at physics-constrained planning, reducing need for CP-SAT | MEDIUM | HIGH | Our architecture already uses LLM only for intent parsing; the solver is the product, not the LLM. LLM improvement makes the interface layer better, not worse. |
| **SpaceX/OneWeb build internal tools** — Constellation operators build in-house | HIGH | MEDIUM | They serve themselves, not the market. Our TAM is the 200+ smaller operators who can't afford in-house teams. |
| **Cognitive Space pivots to LLM Agent** — They already have AI + scheduling | MEDIUM | MEDIUM | Our natural language interface + accessible pricing + smaller-operator focus is a different position. They serve enterprises; we serve everyone. |
| **Satellite failure rate affects adoption** — LEO satellite loss rates are high (~5-10% per launch) | LOW | HIGH | Our products don't depend on satellite survival. If satellites fail, operators need US MORE (planning alternatives, model re-evaluation). |
| **Regulatory changes** — ITAR/EAR restrictions limit international customers | MEDIUM | MEDIUM | Build ITAR-compliant version from Day 1. Focus on non-ITAR markets (commercial EO, academic, Asia). |
| **Team execution risk** — AI coding may not produce production-quality code | MEDIUM | HIGH | Use AI coding for initial MVP, then hire senior engineers for hard parts (CP-SAT solver, physics validation). |
| **Market timing** — Space AI is not mature enough | LOW | MEDIUM | The data-downlink bottleneck (130:1) exists NOW. Operators need solutions NOW. We are early but not too early. |

### 12.2 Best Case / Worst Case

| Scenario | Outcome | Timeline |
|----------|---------|----------|
| **Best case** | Become the "MLPerf of space AI" — every satellite AI vendor tests on Rigor. Apex becomes the default planning tool for non-hermetic operators. $50M ARR by Year 5. | 5 years |
| **Base case** | Solid AI Native + Space Tech company with 100 customers, $3M ARR, profitable by Year 4. Acquired by a space software company (GMV, Auria) for $20-50M. | 5 years |
| **Worst case** | MVP launches but market adoption is slow. Run out of runway at Month 15. Pivot to consulting or sell IP. | 15 months |

---

## 13. TEAM & ORGANIZATION

### 13.1 Founding Team Roles

| Role | Responsibilities | Key Skills |
|------|-----------------|-----------|
| **CEO** | Vision, fundraising, GTM, partnerships | Space industry experience, B2B sales |
| **CTO** | Technical architecture, AI/ML, satellite software | Python, LLMs, constraint optimization, orbital mechanics |
| **Head of Product** | UX, frontend, customer feedback | React, design systems, AI Native products |

### 13.2 First 10 Hires (Months 6-18)

| Hire | When | Role |
|------|------|------|
| 1 | Month 6 | Backend Engineer (CP-SAT, APIs) |
| 2 | Month 8 | ML Engineer (degradation engine, model evaluation) |
| 3 | Month 10 | Frontend Engineer (React, maps, charts) |
| 4 | Month 12 | Sales Engineer (customer success, demos) |
| 5 | Month 14 | DevOps Engineer (deployment, monitoring) |
| 6 | Month 16 | Customer Success Manager |
| 7-10 | Months 18-24 | Additional engineers, marketing, government relations |

### 13.3 Advisors (Target)

| Advisor | Domain | Why |
|---------|--------|-----|
| Former satellite operations manager | Operations | Understands real pain points, connects us to first customers |
| Satellite AI researcher (academic) | Research | Lends credibility, helps with Rigor methodology |
| Space industry VC | Fundraising | Introduces us to space-focused investors |
| Constraint optimization expert | Algorithm | Advises on CP-SAT model design |

---

## 14. APPENDIX: RESEARCH SOURCES

### 14.1 Market Data Sources

- Space Economy Report, Space Foundation / SIA (2024)
- "The Space Economy: Past, Present, and Future," McKinsey (2024)
- Precedence Research: Model Evaluation & Benchmarking Tools Market (2025)
- DataIntelo: Space Software CI/CD Platform Market (2024)
- MarketIntelo: Space Quality Assurance Market (2024)

### 14.2 Technical Sources

- **AstroReason-Bench** (Wang et al., 2026.01): "Evaluating Unified Agentic Planning across Heterogeneous Space Planning Problems" — arXiv:2601.11354
- **CAE** (Mitra, 2026.03): "Constraint-Aware Execution Planning for Hybrid Space-Ground Compute Workloads" — arXiv:2605.04052
- **SpaceMutation** (2026): "An LLM-assisted mutation testing framework for DNNs in distributed LEO satellites" — ScienceDirect
- **Glass Box at Orbit** (2026.06): "A Constitutional AI Verification Framework for Trustworthy Autonomous CubeSat Intelligence" — arXiv:2606.02967
- **REOBench** (2025): "Benchmarking Robustness of Earth Observation Foundation Models" — NeurIPS 2025
- **EarthShift** (2025): "A benchmark for measuring robustness to real-world distribution shifts in Earth observation" — arXiv:2605.29330
- **CVPR 2025**: "Benchmarking Object Detectors under Real-World Distribution Shifts in Satellite Imagery"
- **space-ml-sim**: "Simulation framework for AI inference on orbital satellite constellations" — PyPI
- **MLSpace Robustness** (IEEE Space 2025): "Machine Learning in Space: Surveying the Robustness of on-board ML models to Radiation"

### 14.3 Competitive Sources

- GMV Flexplan: gmv.com/en/products/space/gmv-flexplan
- Auria CPAW / Astro Scheduler: auria.space
- Cognitive Space CNTIENT: cognitivespace.com
- LMArena: techcrunch.com/2026/01/06/lmarena-lands-1-7b-valuation
- Evidently AI: evidentlyai.com
- Galileo AI: galileo.ai
- Orbit Logic CPAW: orbitlogic.com

### 14.4 Industry Sources

- LeoLabs: leolabs.space (space situational awareness)
- Satellogic: satellogic.com (commercial EO)
- Planet Labs: planet.com (largest EO constellation)
- Synspective: synspective.com (SAR satellite, JPX-listed)
- Capella Space: capellaspace.com (SAR AI)
- ADSR Space: adsrspace.com (collision avoidance)
- CNTIENT.Earth: cognitivespace.com/cntient-earth (AI-powered tasking)
