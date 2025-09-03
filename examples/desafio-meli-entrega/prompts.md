# Key Project Prompts

This file documents the prompts and conversations that guided the architecture and implementation decisions of this project, as requested by the challenge briefing.

---

### 1. Stack Definition and Initial Architecture

**Prompt:**
> "This is the goal of the Meli test, I think I can use Kotlin or Python. Since it's a professional API, we need to make it very good, how about starting to structure a plan? What do you think about making a Kotlin API with Swagger, or Python? The AI knows more about Python and I know more about Kotlin. I thought about creating a Kotlin API and an e2e test project in Python? But you are my planner, what do you suggest?"

**Result:**
This conversation led to the fundamental decision to use **Python with FastAPI** due to its development speed, automatic documentation with Swagger UI, and a unified testing ecosystem with `pytest`. It also established the first version of our layered architecture (API, Services, Repository) and the initial action plan.

---

### 2. Establishment of the "Sagas" Process

**Prompt:**
> "I wouldn't want to think about APIs or products yet, what do you think about setting up a documented and formal plan now for the conception of the new project, maybe even designing a hello world in the container [...], how about an incremental folder structure, 001-project, 002-something.. inside docs as if they were sagas?"

**Result:**
This prompt was crucial in defining our **incremental development process**. The idea of "Architecture Sagas" was born here, establishing the workflow where the Architect (Gemini) formally plans and documents each milestone, and the Implementer (Claude) executes based on that blueprint.

---

### 3. Introduction of Observability and Structured Logging

**Prompt:**
> "Okay, I want to impress but not overcomplicate, what do you suggest? What would be easy and portable? NewRelic, Papertrails or something simple, think carefully"

**Result:**
This question raised the project's level. The discussion led to the decision not to couple the application to any specific tool, but rather to adopt the best practice of **structured logging (JSON) to `stdout`**. This made our application "production-ready" and demonstrated an understanding of "cloud-native" architectures, where the application is agnostic to the execution environment.

---