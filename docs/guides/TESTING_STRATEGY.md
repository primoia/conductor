# Testing Strategy: Ensuring Quality and Security in the Conductor Framework

**1. Overview and Philosophy:**

*   **Objective:** To ensure the quality, security, robustness, performance, and maintainability of the Conductor Framework across all its layers.
*   **Philosophy:** Testing is an intrinsic part of the development process ("Quality built-in"), not a post-development phase. We aim for early defect detection and continuous validation.

**2. Strategy Pillars (Adapted Testing Pyramid):**

*   **2.1. Unit Tests (The Solid Foundation):**
    *   **Focus:** Validate the smallest unit of code in isolation (functions, methods, classes).
    *   **Where to Apply:** Argument parsing logic, `agent.yaml` loading, schema validation, individual `Toolbelt` functions (e.g., `read_file`, `write_file`), `LLMClient` prompt construction logic, state management (`state.json`).
    *   **Tools:** `pytest`.
    *   **Metric:** High code coverage (target: 80%+ line coverage for business logic).
    *   **Benefit:** Early bug detection, safe refactoring, rapid feedback for developers.

*   **2.2. Integration Tests (Connecting the Pieces):**
    *   **Focus:** Validate the interaction between two or more components.
    *   **Where to Apply:** Full agent loading flows (Conductor loading `agent.yaml`, `persona.md`, `state.json`), tool execution (mocking the file system and LLM API), state persistence (`/save`).
    *   **Tools:** `pytest`.
    *   **Benefit:** Validation of interfaces and contracts.

*   **2.3. System/Functional Tests (End-to-End - E2E):**
    *   **Focus:** Validate complete user flows, simulating the real experience.
    *   **Where to Apply:** Simulation of complete REPL sessions, onboarding, agent creation, problem analysis, plan creation, validation of created/modified files on disk.
    *   **Tools:** `pytest` with input/output simulation, or CLI automation frameworks.
    *   **Benefit:** Validation of user experience and high-level integration.

*   **2.4. Security Tests (Critical and Continuous Layer):**
    *   **Focus:** Identify and mitigate vulnerabilities.
    *   **Where to Apply:**
        *   **`run_shell_command`:** Fuzzing tests with malicious inputs, validation of command `allowlist` and `denylist`.
        *   **`write_file`:** Attempts to write outside allowed directories, path traversal.
        *   **`agent.yaml` / `team_template.yaml` parsing:** Tests with malicious or malformed templates attempting to inject dangerous code or data.
        *   **User Input Validation:** Strict sanitization and validation of all conversational inputs.
    *   **Tools:** Dedicated unit/integration tests, static code analysis tools (SAST), penetration testing (fuzzing).
    *   **Benefit:** Protection against attacks, misuse, and ensuring system integrity.

*   **2.5. Performance and Cost Tests (Scalability and Efficiency):**
    *   **Focus:** LLM response latency, token usage, memory/CPU consumption, execution time of I/O intensive operations.
    *   **Where to Apply:** LLM API calls, intensive I/O operations (reading/writing large files), conversation history management (sliding window impact).
    *   **Tools:** Load scripts, API monitoring, profiling tools.
    *   **Benefit:** Resource optimization, cost control, and ensuring a fluid user experience.

**3. Evolutionary and Maintenance Strategy:**

*   **3.1. Tests as Code:** All tests must be versioned along with the source code.
*   **3.2. Continuous Integration (CI/CD):** Automate the execution of all tests on every push/pull request. CI/CD failures should block the merge.
*   **3.3. Testability by Design:** Encourage writing modular code with low coupling and clear interfaces, facilitating the creation of mocks and unit tests.
*   **3.4. Test Data Management:** Create and maintain a set of realistic and reproducible test data to ensure result consistency.
*   **3.5. Test Environments:** Ensure consistent and isolated test environments to prevent interference.

**4. Responsibilities:**

*   **Developers:** Primarily responsible for writing unit and integration tests for the code they produce.
*   **Project Lead/Architect:** Define the overall strategy, ensure security and performance coverage, and review the quality and scope of tests.

**5. Next Steps (Strategy Implementation):**

*   **Phase 1 (Immediate):**
    *   Review and expand existing unit tests for `src/cli/agent.py` and `Toolbelt`, focusing on edge cases and error handling.
    *   Create integration tests for agent loading and tool calls.
    *   Add security tests for `run_shell_command` (fuzzing dangerous commands and allowlist validation).
*   **Phase 2 (Continuous):**
    *   Integrate E2E tests for the onboarding flow.
    *   Implement performance and cost metrics monitoring.
    *   Expand security test coverage for YAML parsing and input validation.