# Patterns to Avoid (Scars)

This document records approaches that were attempted and proved problematic. I read it before each task to avoid repeating the same mistakes.

---

### 1. Do Not Use `@SpringBootTest` for Isolated Service Tests

-   **Failure Date:** 2025-08-11
-   **Context:** In the initial attempt to create this integration test, the first approach was simply copying `QuotationReceiptTemplateRealTest` and trying to adapt the database.
-   **Problem:** Keeping the `@SpringBootTest` annotation loads the entire application context (beans, configurations, etc.) unnecessarily. This resulted in a slow test, fragile to changes in other parts of the system, and which failed to connect to the Testcontainer MongoDB without complex profile configurations.
-   **Definitive Solution:** Completely abandon loading the Spring context. Instead, manually instantiate the necessary classes (`QuotationReceiptService`, `QuotationService`, repositories) and use mocks for external dependencies. Database connection is managed directly by the `MongoDBTest` class, ensuring complete isolation and control.