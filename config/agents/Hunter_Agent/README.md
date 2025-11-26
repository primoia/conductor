# Hunter Agent Configuration

## Overview

The Hunter Agent is a specialized B2B prospecting agent designed to search, qualify, and score potential leads based on Ideal Customer Profile (ICP) criteria. It uses MCP (Model Context Protocol) tools to fetch web pages, search sites, and extract contact information.

## Directory Structure

```
Hunter_Agent/
├── definition.yaml      # Agent configuration and metadata
├── persona.md          # System prompt and behavioral instructions
├── prompts/
│   └── hunt.md         # Example usage prompts and best practices
└── README.md           # This file
```

## Configuration Files

### definition.yaml

Defines the agent's core configuration:

- **name**: Hunter_Agent
- **version**: 1.0.0
- **model**: claude (uses Claude AI for reasoning)
- **timeout**: 600 seconds (10 minutes for web scraping operations)
- **allowed_tools**: Read, Write, Bash, and MCP prospector tools
- **mcp_config_path**: Points to the MCP server configuration

### persona.md

Contains the comprehensive system prompt that defines:

- Agent's role and expertise
- Core competencies (ICP analysis, web prospecting, lead qualification)
- Detailed workflow instructions
- Lead scoring framework (0-100 scale)
- JSON output format specification
- Tool usage best practices
- Ethical guidelines and operational directives

### prompts/hunt.md

Provides example prompts and usage patterns:

- Basic and advanced ICP definitions
- Industry-specific search examples
- Output customization options
- Best practices and tips
- Common use cases (ABM, outbound, market research)

## MCP Tools Integration

The Hunter Agent uses three MCP tools from the Prospector server:

### 1. mcp__prospector__search_site
- **Purpose**: Search business directories and databases
- **Usage**: Find companies matching ICP criteria
- **Returns**: URLs and basic company information

### 2. mcp__prospector__fetch_page
- **Purpose**: Retrieve detailed company information
- **Usage**: Fetch company websites and profiles
- **Returns**: HTML content for analysis

### 3. mcp__prospector__extract_contacts
- **Purpose**: Extract decision-maker contact information
- **Usage**: Find emails, phone numbers, LinkedIn profiles
- **Returns**: Structured contact data

## MCP Configuration

The agent requires an MCP server running at the path specified in `mcp_config_path`.

**Example MCP config** (`/tmp/prospector-mcp-test/mcp-config.json`):

```json
{
  "mcpServers": {
    "prospector": {
      "command": "python3",
      "args": ["/tmp/prospector-mcp-test/server.py"],
      "env": {}
    }
  }
}
```

## Lead Qualification Framework

The Hunter Agent uses a systematic 0-100 scoring system:

| Score Range | Fit Level | Description |
|------------|-----------|-------------|
| 85-100 | Perfect | Meets all ICP criteria |
| 70-84 | Strong | Meets most critical criteria |
| 50-69 | Moderate | Meets some criteria, has potential |
| 30-49 | Weak | Limited match, low priority |
| 0-29 | Poor | Doesn't match ICP |

### Scoring Criteria Distribution

1. **Industry/Sector Match**: 20 points
2. **Company Size Fit**: 15 points
3. **Geographic Match**: 10 points
4. **Technology/Tools Alignment**: 15 points
5. **Decision-Maker Accessibility**: 15 points
6. **Budget/Revenue Indicators**: 15 points
7. **Timing/Urgency Signals**: 10 points

## Output Format

The agent returns structured JSON with:

```json
{
  "search_strategy": {
    "queries_used": [],
    "sources_searched": [],
    "total_prospects_found": 0
  },
  "qualified_leads": [
    {
      "company": { ... },
      "contacts": [ ... ],
      "qualification": {
        "score": 0,
        "fit_level": "",
        "reasoning": "",
        "positive_signals": [],
        "negative_signals": [],
        "next_steps": []
      }
    }
  ],
  "summary": { ... }
}
```

## Usage Examples

### Basic Usage

```
Find me leads matching this ICP:
- Industry: B2B SaaS
- Company size: 20-100 employees
- Location: São Paulo, Brazil
- Target role: CTO or VP Engineering
```

### Advanced Usage

```
I need qualified leads for our DevOps platform.

ICP:
- Industry: B2B SaaS, FinTech
- Company size: 50-500 employees
- Revenue: $5M-$50M ARR
- Tech stack: AWS/GCP, Kubernetes, Python/Go
- Behavioral signals: Recent funding, hiring DevOps engineers

Find 25 leads, score each, include decision-maker contacts.
```

See `prompts/hunt.md` for more examples.

## Integration with Conductor

To use the Hunter Agent in Conductor:

1. Ensure the agent directory is in the correct location:
   ```
   conductor/conductor/config/agents/Hunter_Agent/
   ```

2. Ensure the MCP server is running and accessible at the path specified in `definition.yaml`

3. The agent will be automatically discovered by Conductor's agent discovery service

4. Invoke via Conductor API:
   ```bash
   curl -X POST http://localhost:8000/api/agent/execute \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "Hunter_Agent",
       "message": "Find B2B SaaS CTOs in São Paulo"
     }'
   ```

## Performance Considerations

- **Timeout**: Set to 600 seconds (10 minutes) to accommodate web scraping operations
- **Rate Limiting**: Respect website rate limits and robots.txt
- **Caching**: Consider caching company data to reduce redundant fetches
- **Batch Processing**: Process leads in batches for large ICP searches

## Ethical Guidelines

The Hunter Agent follows strict ethical guidelines:

- Only uses publicly available information
- Respects robots.txt and website terms of service
- Doesn't scrape private or gated content
- Handles contact information with appropriate care
- Complies with data privacy regulations (GDPR, LGPD)

## Troubleshooting

### Agent Not Found
- Verify directory is in correct location under `config/agents/`
- Check that `definition.yaml` exists and is valid YAML

### MCP Tools Not Working
- Verify MCP server is running: `ps aux | grep server.py`
- Check MCP config path in `definition.yaml`
- Ensure MCP server is accessible and responding

### Low Quality Results
- Refine ICP criteria to be more specific
- Check search queries in output for relevance
- Adjust scoring criteria in persona.md if needed

### Timeout Errors
- Increase timeout in `definition.yaml` if needed
- Reduce number of leads requested per query
- Check network connectivity and site responsiveness

## Maintenance

### Updating the Agent

1. **Update version** in `definition.yaml` when making changes
2. **Clear agent cache** in Conductor after updates:
   ```python
   agent_discovery_service.clear_cache()
   ```
3. **Test changes** with sample ICP before production use

### Monitoring

Monitor agent performance metrics:
- Lead relevance rate (target: >80%)
- Data quality accuracy (target: >90%)
- Average scoring alignment
- Tool call success rates
- Query execution times

## Future Enhancements

Potential improvements:

- [ ] Add support for more data sources (Crunchbase, AngelList, etc.)
- [ ] Implement ML-based scoring refinement
- [ ] Add email verification and enrichment
- [ ] Create lead nurturing workflow integration
- [ ] Build historical lead analytics dashboard
- [ ] Add competitive intelligence analysis
- [ ] Implement automated follow-up recommendations

## Support

For issues or questions:
- Review `prompts/hunt.md` for usage examples
- Check Conductor documentation for agent system details
- Verify MCP server logs for tool-related issues
- Consult `persona.md` for behavioral guidelines

## License

Part of PrimoIA Conductor system.

## Version History

- **1.0.0** (2025-11-26): Initial release
  - Basic prospecting functionality
  - MCP tools integration
  - Lead scoring system
  - ICP-based qualification
