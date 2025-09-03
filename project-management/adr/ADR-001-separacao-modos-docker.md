# ADR-001: Separation of Docker Execution Modes (Dev vs. Runtime)

**Status:** Proposed
**Date:** 2025-08-31
**Authors:** Gemini (Planner)

---

## 1. Context

Currently, the Conductor project uses a single Docker configuration for all purposes, whether for the development of the framework itself or for its application in third-party projects. The current execution model, defined in `docker-compose.yml`, is based on using **volumes (`-v`)** to mount the entire Conductor source code directory (`/mnt/ramdisk/.../conductor`) into the container (at `/app/projects`).

This model served us well during the initial prototyping phase, as it offers a rapid feedback cycle. However, as Conductor matures, this single design presents significant ambiguities and risks, as it mixes two fundamentally different use cases:

1.  **Framework Development:** The need to modify, debug, and evolve Conductor itself. This use case requires access to metaprogramming tools (like `src/cli/admin.py`) and direct write access to the framework's source code.
2.  **Framework Usage:** The need to apply stable and secure Conductor agents in an "end-user" project, which should not have access to or knowledge of the framework's internal components.

Maintaining a single model for both scenarios results in the following problems:

*   **Security Risk:** Exposing administration tools (`admin.py`) and the ability to self-edit to an end-user environment is dangerous. A user could, accidentally or not, corrupt their own Conductor installation.
*   **Lack of Stability and Versioning:** Users always run the latest version of agents available in the mounted source code, which may be in an unstable development state. There is no way to guarantee a reproducible and stable execution environment for third parties.
*   **High Barrier to Entry:** The end-user is forced to understand Conductor's internal structure, including the distinction between `admin` and `agent`, to use it, which unnecessarily complicates the onboarding experience.

**Relevant Documents for Context:**
*   [Documentation Guide (`docs/DOCUMENTATION_GUIDE.md`)](docs/DOCUMENTATION_GUIDE.md)
*   [Executor Architecture (`docs/architecture/EXECUTOR_ARCHITECTURE.md`)](docs/architecture/EXECUTOR_ARCHITECTURE.md)

---

## 2. Decision

It is decided that Conductor's packaging and distribution strategy will be divided into **two distinct Docker images with clear purposes**, to formally separate the development environment from the execution environment for the end-user.

#### **Image 1: `conductor-dev`**

*   **Purpose:** Exclusively for the development and maintenance of the Conductor framework.
*   **Mechanism:** Will continue to use **`volumes`** to mount the local source code, ensuring a fast development cycle.
*   **Content:** Full access to the source code, including `src/cli/admin.py` and `src/cli/agent.py`.
*   **Dockerfile:** The existing `Dockerfile` at the project root.

#### **Image 2: `conductor-runtime`**

*   **Purpose:** To be distributed to end-users who will apply Conductor agents in their own projects.
*   **Mechanism:** Will use the **`COPY`** instruction in a new `Dockerfile.runtime` to embed components into the image during the build. This ensures the image is a self-contained and immutable artifact.
*   **Content:**
    *   Only the essential code for agent execution.
    *   The entrypoint will be exclusively `src/cli/agent.py`. `src/cli/admin.py` will be **excluded** from the image.
    *   A selected and versioned set of "official" and stable agents will be copied into the image, making them "read-only."
*   **Dockerfile:** A new `Dockerfile.runtime` to be created.

---

## 3. Consequences

The adoption of this decision will have the following implications:

#### Positive

1.  **Enhanced Security:** Completely isolates end-users from the risks of metaprogramming and accidental framework modification. The `runtime` becomes a secure "black box."
2.  **Stability and Reproducibility:** The `conductor-runtime` image will be versioned (e.g., `conductor-runtime:1.0.0`). All users of a specific version will have exactly the same set of agents and behavior, ensuring consistent results.
3.  **Simplified User Experience:** The end-user no longer needs to worry about Conductor's internal structure. They just need to know how to run the `runtime` image, mount their own project, and use the available agents.
4.  **Architectural Clarity:** The formal separation formalizes the distinction between "building the engine" and "driving the car," making the project easier to understand, maintain, and scale.

#### Negative or to Manage

1.  **Increased Build Process Complexity:** The build system will need to be able to generate, test, and manage two different images instead of one.
2.  **Need for a Release Process:** It will no longer be possible to simply use `latest`. A deliberate process will be required to decide when a set of agents is stable enough to be "promoted" to a new version of the `conductor-runtime` image. This introduces release management overhead.