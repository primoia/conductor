# Hunter Agent - Integration Guide

## Overview

The Hunter Agent integrates with Conductor's agent ecosystem to provide B2B prospecting capabilities. This guide shows how Hunter Agent works with other CRM agents and how to build prospecting workflows.

## Agent Ecosystem

### Hunter Agent's Role

```
┌─────────────────────────────────────────────────────────────────┐
│                    B2B SALES WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. PROSPECTING              2. QUALIFICATION         3. ENGAGEMENT
   ┌──────────────┐           ┌──────────────┐         ┌──────────────┐
   │ Hunter_Agent │──────────▶│LeadQualifier │────────▶│EmailAssistant│
   └──────────────┘           │   CRM_Agent  │         │   CRM_Agent  │
        │                     └──────────────┘         └──────────────┘
        │                            │                        │
        ▼                            ▼                        ▼
   Find prospects             BANT Analysis            Send outreach
   Score 0-100               Budget/Authority          Personalized
   Extract contacts          Need/Timeline             Multi-channel

4. DEAL MANAGEMENT          5. ANALYTICS
   ┌──────────────┐           ┌──────────────┐
   │DealPredictor │           │ CRMAnalytics │
   │  CRM_Agent   │           │    Agent     │
   └──────────────┘           └──────────────┘
        │                            │
        ▼                            ▼
   Predict close %            Pipeline metrics
   Risk analysis              Performance insights
```

## Integration Points

### 1. Hunter → LeadQualifier Handoff

**Hunter Agent Output:**
```json
{
  "qualified_leads": [
    {
      "company": {"name": "TechCorp", "size": "80 employees"},
      "contacts": [{"name": "João Silva", "title": "CTO"}],
      "qualification": {
        "score": 85,
        "positive_signals": ["Uses React", "Recent funding"]
      }
    }
  ]
}
```

**LeadQualifier CRM Agent Input:**
Import leads from Hunter and run BANT qualification:
- Budget: Does company have budget? (Hunter provides revenue signals)
- Authority: Is contact a decision-maker? (Hunter identifies titles)
- Need: Does company have pain points? (Hunter finds tech stack gaps)
- Timeline: Is timing right? (Hunter detects urgency signals)

**Workflow:**
```python
# 1. Hunt for leads
hunter_result = conductor.execute_agent("Hunter_Agent",
    "Find 20 B2B SaaS companies in SP with 50-200 employees")

# 2. Import to CRM and qualify
for lead in hunter_result['qualified_leads']:
    crm_lead = crm.create_lead(lead)
    qualification = conductor.execute_agent("LeadQualifier_CRM_Agent",
        f"Qualify lead: {crm_lead.id}")
```

### 2. Hunter → EmailAssistant Workflow

**Use Case:** Generate personalized outreach based on Hunter findings

**Workflow:**
```python
# 1. Hunt and score leads
leads = hunter_agent.find_leads(icp_criteria)

# 2. For high-scoring leads, generate personalized emails
for lead in leads:
    if lead['qualification']['score'] >= 70:
        context = {
            'company': lead['company'],
            'positive_signals': lead['qualification']['positive_signals'],
            'pain_points': lead['qualification']['pain_points']
        }

        email = conductor.execute_agent("EmailAssistant_CRM_Agent",
            f"Write cold outreach email for {context}")
```

### 3. Hunter → DealPredictor Integration

**Use Case:** Predict which hunted leads are most likely to close

**Workflow:**
```python
# 1. Hunt for leads
leads = hunter_agent.find_leads(icp_criteria)

# 2. Import to CRM
crm_leads = [crm.create_lead(l) for l in leads]

# 3. Predict close probability
for crm_lead in crm_leads:
    prediction = conductor.execute_agent("DealPredictor_CRM_Agent",
        f"Predict close probability for lead {crm_lead.id}")

    # Focus on leads with high hunter score + high close prediction
    if crm_lead.hunter_score >= 80 and prediction['probability'] >= 0.7:
        priority_outreach(crm_lead)
```

### 4. Hunter → CRMAnalytics Pipeline

**Use Case:** Analyze prospecting effectiveness over time

**Workflow:**
```python
# Track Hunter Agent performance
analytics = conductor.execute_agent("CRMAnalytics_Agent",
    """
    Analyze prospecting metrics:
    - Total leads found by Hunter Agent (last 30 days)
    - Average lead quality score
    - Conversion rate: Hunter leads → Qualified leads
    - Conversion rate: Hunter leads → Closed deals
    - ROI by industry/segment
    """)
```

## Complete Sales Pipeline Example

### End-to-End Workflow

```python
from conductor import Conductor

conductor = Conductor()

# STEP 1: DEFINE ICP
icp = """
Find B2B SaaS leads:
- Industry: FinTech, E-commerce
- Size: 50-200 employees
- Location: São Paulo, Rio
- Tech: AWS, React, PostgreSQL
- Role: CTO, VP Engineering
- Signals: Recent funding, hiring engineers
"""

# STEP 2: PROSPECT (Hunter Agent)
print("🔍 Prospecting...")
hunt_result = conductor.execute_agent("Hunter_Agent", icp)
leads = hunt_result['qualified_leads']
print(f"Found {len(leads)} leads, avg score: {hunt_result['summary']['average_score']}")

# STEP 3: IMPORT TO CRM & QUALIFY (LeadQualifier)
print("\n✅ Qualifying...")
for lead in leads:
    if lead['qualification']['score'] >= 70:  # Only high-quality
        # Create CRM lead
        crm_lead = crm.create_lead({
            'company_name': lead['company']['name'],
            'contact_name': lead['contacts'][0]['name'],
            'contact_email': lead['contacts'][0]['email'],
            'hunter_score': lead['qualification']['score'],
            'source': 'Hunter_Agent'
        })

        # Run BANT qualification
        qualification = conductor.execute_agent("LeadQualifier_CRM_Agent",
            f"Qualify lead {crm_lead.id} using BANT methodology")

        crm_lead.update(bant_score=qualification['score'])

# STEP 4: GENERATE OUTREACH (EmailAssistant)
print("\n📧 Generating outreach...")
for crm_lead in crm.get_leads(hunter_score__gte=70, bant_score__gte=60):
    # Generate personalized email
    email = conductor.execute_agent("EmailAssistant_CRM_Agent",
        f"""
        Write cold outreach email for:
        Company: {crm_lead.company_name}
        Contact: {crm_lead.contact_name}, {crm_lead.contact_title}
        Pain points: {crm_lead.pain_points}
        Our solution: DevOps automation platform
        """)

    # Save email template for review
    crm_lead.add_email_template(email['content'])

# STEP 5: PREDICT & PRIORITIZE (DealPredictor)
print("\n🎯 Prioritizing...")
for crm_lead in crm.get_leads(status='qualified'):
    prediction = conductor.execute_agent("DealPredictor_CRM_Agent",
        f"Predict close probability for lead {crm_lead.id}")

    crm_lead.update(
        close_probability=prediction['probability'],
        priority='high' if prediction['probability'] >= 0.7 else 'medium'
    )

# STEP 6: ANALYTICS (CRMAnalytics)
print("\n📊 Analyzing pipeline...")
analytics = conductor.execute_agent("CRMAnalytics_Agent",
    "Generate prospecting campaign report for last 30 days")

print(analytics['summary'])
```

## Data Flow

### Lead Object Structure

```json
{
  "id": "lead_12345",
  "source": "Hunter_Agent",
  "timestamps": {
    "hunted_at": "2025-11-26T10:00:00Z",
    "qualified_at": "2025-11-26T10:15:00Z",
    "contacted_at": "2025-11-26T11:00:00Z"
  },
  "hunter_data": {
    "score": 85,
    "fit_level": "strong",
    "positive_signals": ["Recent funding", "Tech stack match"],
    "data_sources": ["https://company.com", "https://linkedin.com/..."]
  },
  "qualification_data": {
    "bant_score": 75,
    "budget": "confirmed",
    "authority": "decision_maker",
    "need": "high",
    "timeline": "3-6_months"
  },
  "engagement_data": {
    "emails_sent": 1,
    "opened": true,
    "replied": false
  },
  "prediction_data": {
    "close_probability": 0.72,
    "estimated_value": 50000,
    "risk_factors": ["Long sales cycle"]
  }
}
```

## API Integration Examples

### REST API

```bash
# 1. Hunt for leads
curl -X POST http://localhost:8000/api/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "Hunter_Agent",
    "message": "Find 20 B2B SaaS CTOs in São Paulo"
  }' > leads.json

# 2. Import to CRM
curl -X POST http://localhost:8001/api/v1/leads/import \
  -H "Content-Type: application/json" \
  -d @leads.json

# 3. Qualify leads
curl -X POST http://localhost:8000/api/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "LeadQualifier_CRM_Agent",
    "message": "Qualify all new leads from Hunter_Agent"
  }'
```

### Python SDK

```python
from conductor_sdk import ConductorClient
from crm_sdk import CRMClient

conductor = ConductorClient(api_url="http://localhost:8000")
crm = CRMClient(api_url="http://localhost:8001")

# Hunt
leads = conductor.agents.hunter.find_leads(
    industry="B2B SaaS",
    size="50-200",
    location="São Paulo",
    min_score=70
)

# Import to CRM
for lead in leads:
    crm.leads.create(lead)

# Qualify
crm.leads.qualify_all(method="BANT")
```

## Monitoring & Metrics

### Key Metrics to Track

```python
# Hunter Agent Metrics
metrics = {
    'prospecting': {
        'leads_found': 150,
        'avg_score': 72,
        'score_distribution': {
            'perfect': 12,  # 85-100
            'strong': 45,   # 70-84
            'moderate': 68, # 50-69
            'weak': 25      # 30-49
        },
        'time_per_lead': '45s',
        'data_quality': '94%'
    },
    'conversion': {
        'hunter_to_crm': '85%',      # Leads imported
        'hunter_to_qualified': '62%', # Passed BANT
        'hunter_to_deal': '18%',      # Created opportunity
        'hunter_to_closed': '4%'      # Closed won
    },
    'efficiency': {
        'cost_per_lead': '$2.50',
        'time_saved_vs_manual': '85%',
        'data_accuracy': '91%'
    }
}
```

### Dashboard Queries

```python
# Prospecting performance
analytics = conductor.execute_agent("CRMAnalytics_Agent", """
    Analyze Hunter Agent performance:
    - Total leads found (last 30 days)
    - Quality score trends
    - Best performing industries
    - Conversion rates by source
    - ROI analysis
""")
```

## Best Practices

### 1. Score Calibration
Regularly calibrate Hunter scores against actual conversion:

```python
# Compare Hunter score vs. actual outcomes
calibration = crm.analyze("""
    SELECT
        hunter_score_range,
        COUNT(*) as leads,
        SUM(CASE WHEN status='closed_won' THEN 1 ELSE 0 END) as closed,
        ROUND(100.0 * closed / leads, 2) as conversion_rate
    FROM leads
    WHERE source = 'Hunter_Agent'
    GROUP BY hunter_score_range
""")

# Adjust scoring thresholds based on results
```

### 2. ICP Refinement
Use Hunter + Analytics to refine ICP:

```python
# Find patterns in high-converting leads
patterns = conductor.execute_agent("CRMAnalytics_Agent", """
    Analyze characteristics of leads that converted:
    - Common industries
    - Company size sweet spot
    - Technology patterns
    - Geographic clusters
    - Title/role patterns
""")

# Update ICP based on findings
updated_icp = refine_icp_based_on_patterns(patterns)
```

### 3. A/B Testing
Test different ICPs and search strategies:

```python
# Test A: Broad ICP
leads_a = hunter.find_leads(broad_icp)

# Test B: Narrow ICP
leads_b = hunter.find_leads(narrow_icp)

# Compare results
compare_results(leads_a, leads_b, metrics=['quality', 'conversion', 'roi'])
```

## Error Handling

```python
try:
    leads = conductor.execute_agent("Hunter_Agent", icp)
except TimeoutError:
    # Reduce scope
    leads = conductor.execute_agent("Hunter_Agent",
        icp + "\nFind only 10 leads")
except NoResultsError:
    # Broaden criteria
    leads = conductor.execute_agent("Hunter_Agent",
        simplified_icp)
except DataQualityError as e:
    # Log quality issues
    log_data_quality_issue(e)
    leads = e.partial_results
```

## Scaling Considerations

### High-Volume Prospecting

```python
# For large campaigns, batch process
async def prospect_at_scale(icp, total_target=1000):
    batch_size = 50
    batches = total_target // batch_size

    results = []
    for i in range(batches):
        batch_icp = f"{icp}\nFind {batch_size} leads"
        batch_leads = await conductor.execute_agent_async(
            "Hunter_Agent",
            batch_icp
        )
        results.extend(batch_leads['qualified_leads'])

        # Rate limit
        await asyncio.sleep(60)

    return results
```

## Next Steps

1. **Deploy Hunter Agent** - Follow QUICKSTART.md
2. **Test Integration** - Run end-to-end workflow
3. **Monitor Metrics** - Track quality and conversion
4. **Refine ICP** - Iterate based on results
5. **Scale Up** - Automate prospecting pipelines

## Support

For integration questions:
- Check CRM API docs: `/api/v1/docs`
- Review Conductor agent docs
- See example workflows in this guide
