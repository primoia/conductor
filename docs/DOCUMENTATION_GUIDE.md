# 📖 Documentation Guide - Conductor Project

> **Philosophy:** Documentation should be an enabler, not an obstacle. It needs to be easy to find, easy to understand, and, above all, reliable. This guide establishes the guidelines to achieve that.

## 1. Directory Structure

Conductor's documentation is organized into high-level folders, each with a clear purpose:

-   **/conductor (`root`)**: The `README.md` at the root is the **main entry point**. It should provide an overview of the project, links to key executors, and direct to the most important documents.
-   `docs/`: Contains **permanent technical documentation**. It is the consolidated knowledge about the framework's architecture, functionalities, and usage guides.
-   `project-management/`: Contains **process and management documents**. These are temporal artifacts such as milestone plans, bug reports, and new feature planning.
-   `scripts/`: Although it contains code, it may include specific `README.md` files that explain the purpose and use of the main executors.

## 2. Document Categories

To maintain consistency, documents within `docs/` should fall into one of the following categories:

#### a. 🏛️ Architecture (`docs/architecture/`)
-   **Purpose:** Describe high-level decisions, design patterns, and the fundamental structure of the framework.
-   **Examples:** `GEMINI_ARCH_SPEC.md`, `EXECUTOR_ARCHITECTURE.md`.
-   **Nomenclature:** Descriptive names in UPPERCASE_WITH_UNDERSCORE.md or kebab-case.md.

#### b. ✨ Features (`docs/features/`)
-   **Purpose:** Document specific functionalities and how they work.
-   **Examples:** `interactive-sessions.md`, `multi-provider-ai.md`.
-   **Nomenclature:** `feature-name.md`.

#### c. 🏁 Guides and Tutorials (`docs/guides/`) 
-   **Purpose:** Provide step-by-step instructions for common tasks.
-   **Examples:** `project-onboarding.md`, `AGENT_DESIGN_PATTERNS.md`.
-   **Nomenclature:** Descriptive and clear names.

#### d. 📜 Architectural Decisions (`project-management/adr/`)
-   **Purpose:** Record important architectural decisions (Architectural Decision Records).
-   **Nomenclature:** `ADR-XXX-decision-description.md`.

## 3. Documentation Lifecycle

To avoid outdated and conflicting information, we follow a lifecycle:

1.  **Creation:**
    -   Whenever a new feature, architectural decision, or process is introduced, a new document should be created in the appropriate category.
    -   Use templates (to be defined) to ensure consistency.

2.  **Review:**
    -   Documentation must be reviewed as part of the code review process. If a PR changes behavior, the corresponding documentation **must** be updated in the same PR.

3.  **Archiving (not deletion):**
    -   Documents that become obsolete (e.g., completed milestone plans, old architectures) should not be deleted.
    -   They should be moved to an `_archive/` subdirectory within their respective folders (e.g., `docs/architecture/_archive/`, `project-management/_archive/`).
    -   This preserves history without cluttering the main structure.

4.  **Conflict Flagging:**
    -   If you find a document that contradicts a more recent one, the newer one always takes precedence.
    -   The old document should be immediately marked for archiving, and an issue should be opened to resolve the inconsistency.

## 4. The `README.md` as a Map
The `README.md` of each directory (`docs/README.md`, `project-management/README.md`) should serve as an index or map to the content of that section, highlighting the most important documents and briefly explaining the purpose of each subfolder.