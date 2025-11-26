# Hunter Agent - Quick Start Guide

## What is Hunter Agent?

Hunter Agent is your AI-powered B2B prospecting assistant that finds, qualifies, and scores leads based on your Ideal Customer Profile (ICP).

## Quick Setup

1. **Verify Agent Location**
   ```bash
   ls -la conductor/conductor/config/agents/Hunter_Agent/
   ```

2. **Check MCP Server**
   ```bash
   # Ensure MCP server is running
   ps aux | grep prospector
   ```

3. **Test the Agent**
   ```bash
   curl -X POST http://localhost:8000/api/agent/execute \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "Hunter_Agent",
       "message": "Find 5 B2B SaaS companies in São Paulo with 20-100 employees"
     }'
   ```

## 60-Second Usage

### Simple Search
```
Find CTOs at FinTech companies in Brazil with 50-200 employees
```

### With ICP Criteria
```
Find leads matching:
- Industry: B2B SaaS
- Size: 20-100 employees
- Location: São Paulo
- Tech: React, Node.js
- Role: CTO, VP Engineering
```

### Get Scored Results
```
Search for DevOps tool prospects:
- E-commerce companies
- 100-500 employees
- Using AWS/Kubernetes
- Recent funding
Score each lead 0-100, include contacts
```

## What You Get Back

```json
{
  "qualified_leads": [
    {
      "company": {
        "name": "TechCorp Inc",
        "size": "80 employees",
        "industry": "B2B SaaS"
      },
      "contacts": [
        {
          "name": "João Silva",
          "title": "CTO",
          "email": "joao@techcorp.com"
        }
      ],
      "qualification": {
        "score": 85,
        "fit_level": "strong",
        "reasoning": "Perfect ICP match...",
        "next_steps": ["Connect on LinkedIn", "Email intro"]
      }
    }
  ]
}
```

## Lead Scoring Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 85-100 | Perfect fit | High priority outreach |
| 70-84 | Strong fit | Good prospect |
| 50-69 | Moderate fit | Consider for nurture |
| 30-49 | Weak fit | Low priority |
| 0-29 | Poor fit | Skip |

## Common Use Cases

### 1. ABM Campaign
```
Find 50 target accounts for Q1 ABM:
- Industry: FinTech
- Revenue: $10M+
- Location: Brazil
- Decision-makers: CFO, CTO
```

### 2. Outbound Lead Gen
```
Generate 100 qualified leads:
- B2B SaaS companies
- 20-200 employees
- Using Python/Django
- Include warm intro paths
```

### 3. Market Research
```
Analyze e-commerce market in São Paulo:
- Companies using Shopify/Magento
- Revenue $5M+
- Map competitive landscape
```

### 4. Partnership Prospecting
```
Find integration partners:
- Complementary products
- Same customer base
- Not competitors
```

## Pro Tips

1. **Be Specific**: More criteria = better qualification
2. **Include Pain Points**: Helps agent find relevant leads
3. **Define Disqualifiers**: Save time by excluding bad fits
4. **Request Next Steps**: Get actionable recommendations
5. **Start Small**: Test with 10-20 leads before scaling

## ICP Template

```
Find leads for [YOUR PRODUCT]:

Firmographics:
- Industry: [industry]
- Size: [employee count]
- Revenue: [revenue range]
- Location: [geography]

Technographics:
- Uses: [tools/platforms]
- Tech stack: [languages/frameworks]

Behavioral Signals:
- [funding, hiring, growth indicators]

Target Personas:
- [job titles and roles]

Pain Points:
- [business challenges]

Disqualifiers:
- [what makes them NOT a fit]

Goal: Find [number] leads scored 70+
```

## Output Formats

### JSON (Default)
Structured data ready for CRM import

### CSV
```
Export as CSV: Company, Contact, Email, Score
```

### Markdown Summary
```
Provide markdown report with top 10 leads
```

### Prioritized List
```
Rank by score, show top 5 with detailed profiles
```

## Troubleshooting

**No results found?**
- Broaden your criteria
- Check geography/location filters
- Verify industry categories

**Low quality leads?**
- Add more specific criteria
- Include technology requirements
- Define clearer pain points

**Timeout errors?**
- Reduce number of leads requested
- Split into multiple smaller searches
- Check network connectivity

**Missing contact info?**
- Some companies don't publish contacts
- Try LinkedIn for decision-makers
- Use company emails (info@, contact@)

## Need Help?

- **Examples**: See `prompts/hunt.md`
- **Full Guide**: See `README.md`
- **Persona**: See `persona.md`
- **Config**: See `definition.yaml`

## API Integration

### Python
```python
import requests

response = requests.post('http://localhost:8000/api/agent/execute', json={
    'agent_id': 'Hunter_Agent',
    'message': 'Find 10 B2B SaaS CTOs in Brazil'
})

leads = response.json()
```

### cURL
```bash
curl -X POST http://localhost:8000/api/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "Hunter_Agent", "message": "YOUR ICP HERE"}'
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/agent/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 'Hunter_Agent',
    message: 'Find 10 FinTech leads in São Paulo'
  })
});

const leads = await response.json();
```

## Best Results Formula

```
Good ICP Definition
+ Clear Criteria (3-5 key filters)
+ Specific Pain Points
+ Defined Disqualifiers
+ Actionable Output Request
= High Quality Leads (70+ score)
```

## Next Steps

1. ✅ Read this quickstart
2. ✅ Test with sample search
3. ✅ Define your ICP
4. ✅ Run first real search
5. ✅ Review and refine results
6. ✅ Export to CRM
7. ✅ Start outreach!

---

**Ready to hunt? Start with a simple search and iterate based on results!**
