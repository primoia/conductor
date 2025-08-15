# Coding Standards

## Kotlin Entity Standards

### Package Structure
- Entities should be in `com.example.domain.entities` package
- Use descriptive package names that reflect the domain

### Class Naming
- Use PascalCase for entity class names
- Use descriptive names that represent the business concept
- Avoid abbreviations unless they are widely understood

### Field Naming
- Use camelCase for field names
- Use descriptive names that clearly indicate the purpose
- Follow Kotlin naming conventions

### Annotations
- Always use `@Entity` annotation for entity classes
- Use `@Id` with `@GeneratedValue` for primary keys
- Use `@Column` for custom column mappings
- Use `@CreationTimestamp` and `@UpdateTimestamp` for audit fields
- Use validation annotations appropriately

### Data Types
- Use `Long` for primary keys
- Use `String` for text fields
- Use `BigDecimal` for monetary values
- Use `LocalDateTime` for timestamps
- Use nullable types (`String?`) when fields can be null

### Validation
- Use `@NotNull` for required fields
- Use `@Size` for string length constraints
- Use `@Min` and `@Max` for numeric constraints
- Use `@DecimalMin` and `@DecimalMax` for decimal constraints
- Use `@Email` for email validation

### Documentation
- Add class-level documentation explaining the entity's purpose
- Add field-level comments for complex fields
- Use clear and concise language
- Include examples when helpful

## Repository Standards

### Interface Naming
- Use `EntityNameRepository` pattern
- Extend appropriate Spring Data JPA interfaces
- Use `@Repository` annotation for clarity

### Method Naming
- Follow Spring Data JPA naming conventions
- Use descriptive method names
- Use `findBy`, `countBy`, `deleteBy` prefixes

### Custom Queries
- Use `@Query` annotation for complex queries
- Keep queries simple and readable
- Use method naming conventions when possible
- Document complex queries with comments
