# Agent Template

## Agent: {AGENT_NAME}

## Function
{Concise description of the agent's main responsibility}

## Responsibilities
- {Specific list of what the agent should do}
- {One responsibility per line}
- {Be specific and measurable}

## Rules
1. {Behavior and execution rules}
2. {Activation conditions}
3. {Communication protocol}
4. {Execution frequency}

## Restrictions
- {What the agent should NOT do}
- {Scope limitations}
- {Boundaries with other agents}
- {Maximum allowed resources}

## Expected Inputs
- Command: "{example command that activates the agent}"
- Data: {expected data type}
- Context: {necessary context}

## Outputs
- Status: {SUCCESS/FAILURE/PENDING}
- Data: {format of the returned data}
- Metrics: {relevant metrics}
- Logs: {logging level}

## Persistent State
- {field1}: {description of what is stored}
- {field2}: {description of what is stored}
- {fieldN}: {description of what is stored}

## Dependencies
- Predecessor agents: {list or "none"}
- Successor agents: {list or "none"}
- External resources: {APIs, databases, etc}

## Success Criteria
- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}
- [ ] {Measurable criterion N}

## Error Handling
- **Timeout**: {behavior if it takes too long}
- **Resource failure**: {behavior if a dependency fails}
- **Invalid input**: {behavior with bad data}
- **Inconsistent state**: {behavior with corrupted state}

## Metrics and Monitoring
- **Performance**: {expected execution time}
- **Success rate**: {expected success rate}
- **Resource usage**: {expected CPU, memory, storage}
- **Health check**: {how to check if the agent is healthy}