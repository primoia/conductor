# Create Implementation Plan

## Purpose
Generate a structured implementation plan in YAML format that can be consumed and executed by the conductor system.

## When to Use
- After a story has been approved and is ready for implementation
- When you need to break down complex implementation into manageable tasks
- When you want to delegate execution to specialized conductor agents

## Prerequisites
- Story file with clear acceptance criteria
- Project architecture documentation
- Coding standards and conventions
- Available conductor agents for the specific tasks

## Workflow

### Step 1: Analyze Story and Context
1. Read the story file completely
2. Identify all acceptance criteria
3. Review related architecture documents
4. Understand the current codebase structure
5. Identify dependencies and constraints

### Step 2: Break Down Implementation
1. List all required changes (new files, modifications, deletions)
2. Group related changes into logical tasks
3. Determine task dependencies and execution order
4. Identify which conductor agents are best suited for each task
5. Define input and output files for each task

### Step 3: Create YAML Plan
1. Use the template from `projects/develop/workspace/implementation-plan-template.yaml`
2. Fill in all required fields:
   - `storyId`: Path to the story file
   - `description`: Brief overview of the implementation
   - `tasks`: List of all implementation tasks
   - `validationCriteria`: How to verify successful completion
3. Ensure all tasks have:
   - Clear name and description
   - Appropriate agent assignment
   - Specific input and output files
   - Dependencies if needed
   - Validation criteria

### Step 4: Validate Plan
1. Review the plan for completeness
2. Ensure all acceptance criteria are covered
3. Verify task dependencies are correct
4. Check that all referenced files exist
5. Confirm agent names match available conductor agents

### Step 5: Save and Document
1. Save the plan as `implementation-plan.yaml` in the project workspace
2. Update the story file to reference the implementation plan
3. Document any assumptions or special considerations

## Output
- `implementation-plan.yaml`: Structured plan ready for conductor execution
- Updated story file with reference to the implementation plan

## Validation
- All story acceptance criteria are covered by tasks
- Task dependencies form a valid execution graph
- All referenced files and agents exist
- Plan follows the YAML template structure
- Validation criteria are specific and measurable

## Notes
- Keep tasks focused and atomic
- Use descriptive names for tasks and agents
- Include rollback considerations for critical changes
- Consider parallel execution opportunities
- Document any environment or configuration requirements
