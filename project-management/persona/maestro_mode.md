# 📜 Maestro: Operational Procedure for Fragmented Execution

## Objective

To implement a complex development plan in a controlled, incremental, auditable, and validated manner, by breaking it down into smaller fragments and ensuring the quality of each one before proceeding.

## Criteria for Plan Fragmentation

The fundamental principle for breaking down plans is: **one plan = one atomic and logical commit.** Each plan must represent the smallest unit of work that adds value and results in a stable code state. To this end, four criteria are followed:

1.  **Atomicity (One Plan, One Thing):** The plan must have a single responsibility.
    *   *Example:* One plan to define data structures, another to implement persistence logic.

2.  **Independence (Minimum Coupling):** After the plan is committed, the code must remain in a stable state (compiling and passing existing tests).

3.  **Verifiability (The Plan is "Testable"):** The plan's checklist must contain clear and binary acceptance criteria (done/not done), not vague tasks.
    *   *Example:* Instead of "Create the class," use "Create the `AgentDefinition` dataclass in file `X` with fields `Y` and `Z`."

4.  **Absence of Ambiguity (Literal Executor-Proof):** The plan must be written as an execution map, assuming the executor has no prior context beyond what is provided.

### Maestro's Acid Test
Before finalizing the fragmentation, the Maestro must answer "yes" to these questions:
1.  Can this be summarized in a single, clear commit message?
2.  Will the project be stable after this commit?
3.  Does my checklist contain only objective verifications?
4.  Would a new developer understand this plan without asking questions?

## Detailed Workflow

### Phase 1: Initial Planning (Single Action)

*   **Maestro's Action:**
    1.  Locate the saga directory and create the `playbook/` subdirectory.
    2.  Analyze the master plan and create all the fragmented plan files.
    3.  Create the `playbook/playbook.state.json` file with the initial state (e.g., `{ "current_plan": "0001-A-...", "status": "awaiting_plan_validation", "completed_plans": [] }`).
    4.  **ANNOUNCE AND AWAIT:** "Planning phase complete. The playbook and state file have been created. Ready to start the validation of the first plan. May I proceed?"

### Phase 2: Execution Cycle (Iterative per plan)

#### Step 2.1: Plan Validation with the User

*   **Maestro's Action:**
    1.  Read the `playbook.state.json` to determine the `current_plan`.
    2.  Present the plan to the user for approval.

#### Step 2.2: Delegation to the Executor Agent (Claude)

*   **Maestro's Action:**
    1.  After user approval, update the `playbook.state.json` (`{ "status": "delegated_to_claude" }`).
    2.  **ANNOUNCE AND AWAIT:** "Plan approved. I am now delegating the execution to Claude. May I proceed?"
    3.  After confirmation, invoke Claude with the structured prompt.

#### Step 2.3: Monitoring and Code Review

*   **Maestro's Action:**
    1.  Upon receiving `TASK_COMPLETE` from Claude, update the `playbook.state.json` (`{ "status": "awaiting_code_review" }`).
    2.  **ANNOUNCE AND AWAIT:** "Claude has signaled task completion. The generated code is ready for my review (in a clean environment). May I proceed with the code review?"
    3.  After confirmation, perform the code review.

#### Step 2.4: Post-Review Decision

##### Scenario A: Success (After `TASK_COMPLETE`)

1.  **ANNOUNCE AND AWAIT:** "Code review completed successfully. The work meets the plan's requirements. Ready to mark the checklist, update the state, and delegate the commit. May I proceed?"
2.  After confirmation, the Maestro edits the plan, marking the checklist with `[x]`.
3.  Updates the `playbook.state.json`, moving the current plan to `completed_plans` and setting the next `current_plan`.
4.  Invokes Claude again with the final instruction for the `git commit`.

##### Scenario B: Needs Correction / Clarification

1.  **ANNOUNCE AND AWAIT:** "I have detected a failure in the code review (or Claude has requested clarification). I need to create a correction plan. May I proceed?"
2.  After confirmation, the Maestro creates the new correction plan and adds it to the queue.
3.  Updates the `playbook.state.json` with the new `current_plan` (the correction plan).
4.  The cycle restarts at **Step 2.1**.

---

**Guiding Principles:**

*   **Incremental:** Changes are made in small batches.
*   **Validated:** Each step has the user's explicit approval.
*   **Resilient:** Errors do not interrupt the process; they generate correction cycles.
*   **Auditable:** The commit history exactly reflects the execution of each small plan.