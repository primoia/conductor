# Orchestrator Sequence Template

## Objective
{Description of what this orchestration sequence should achieve}

## Scenario
{Context and background of the problem being solved}

## Agents Involved
- **{agent-name-1}**: {summary function}
- **{agent-name-2}**: {summary function}
- **{agent-name-n}**: {summary function}

## Execution Flow

### Phase 1: {Phase Name}
**Objective**: {What this phase should achieve}

#### Step 1.1: {Step Name}
- **Trigger**: {agent-name}
- **Command**: `{specific command}`
- **Expected Input**: {input type}
- **Expected Output**: {output type}
- **Dependencies**: {none or list}
- **Success Criteria**: {how to know if it worked}

#### Step 1.2: {Step Name}
- **Trigger**: {agent-name}
- **Command**: `{specific command}`
- **Expected Input**: {input type}
- **Expected Output**: {output type}
- **Dependencies**: {none or list}
- **Success Criteria**: {how to know if it worked}

### Phase 2: {Phase Name}
**Objective**: {What this phase should achieve}

#### Step 2.1: {Step Name}
- **Trigger**: {agent-name}
- **Command**: `{specific command}`
- **Expected Input**: {input type}
- **Expected Output**: {output type}
- **Dependencies**: {result of Phase 1}
- **Success Criteria**: {how to know if it worked}

## Validations

### Coordination Test
- [ ] {Specific validation 1}
- [ ] {Specific validation 2}
- [ ] {Specific validation N}

### Persistence Test
- [ ] States maintained after interruption
- [ ] Agents recover context correctly
- [ ] Possible to continue execution from the stopping point

### Failure Test
- [ ] Resilient system to individual agent failure
- [ ] Rollback works when necessary
- [ ] Adequate error handling

## Global Success Criteria
- [ ] {Main objective achieved}
- [ ] {Quality metric}
- [ ] {Performance metric}
- [ ] {Usability criterion}

## Contingencies

### If Agent X Fails
- **Action**: {what to do}
- **Rollback**: {how to revert if necessary}
- **Retry**: {conditions for trying again}

### If Timeout Exceeded
- **Timeout**: {maximum acceptable time}
- **Action**: {what to do when exceeded}
- **Escalation**: {when to involve a human}

### If Data is Inconsistent
- **Detection**: {how to identify inconsistency}
- **Correction**: {correction process}
- **Prevention**: {how to avoid in the future}

## Execution Metrics
- **Total expected time**: {X minutes}
- **Expected success rate**: {X%}
- **Required resources**: {CPU, memory, etc}
- **Checkpoint points**: {where to save progress}

## Post-Execution
- **Cleanup**: {what to clean up afterwards}
- **Reporting**: {what reports to generate}
- **Lessons learned**: {how to capture learnings}
- **Next steps**: {next actions if successful}