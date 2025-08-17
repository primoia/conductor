# Patterns to Avoid (Scars): Kotlin Entity Creator Agent

## Anti-Patterns I've Learned to Avoid

### 1. **Incorrect JPA Annotations**
- **Problem**: Using wrong or missing JPA annotations
- **Scar**: Entities that don't map correctly to database tables
- **Avoid**: Always use `@Entity` and proper `@Id` annotations

### 2. **Missing Validation Annotations**
- **Problem**: Not adding validation constraints to fields
- **Scar**: Invalid data can be persisted to the database
- **Avoid**: Always add appropriate `@NotNull`, `@Size`, `@Email` annotations

### 3. **Incorrect Field Types**
- **Problem**: Using wrong Kotlin types for database fields
- **Scar**: Runtime errors and data corruption
- **Avoid**: Use `String` for text, `Long` for IDs, `LocalDateTime` for dates

### 4. **Poor Naming Conventions**
- **Problem**: Inconsistent or unclear field names
- **Scar**: Confusion and maintenance issues
- **Avoid**: Follow Kotlin naming conventions and be descriptive

### 5. **Missing Relationships**
- **Problem**: Not defining entity relationships properly
- **Scar**: Inability to perform joins and complex queries
- **Avoid**: Use `@OneToMany`, `@ManyToOne`, `@ManyToMany` appropriately

### 6. **Over-Engineering**
- **Problem**: Adding unnecessary complexity to simple entities
- **Scar**: Hard to maintain and understand code
- **Avoid**: Keep entities simple and focused on data representation

### 7. **Ignoring Null Safety**
- **Problem**: Not considering nullable vs non-nullable fields
- **Scar**: NullPointerExceptions and data integrity issues
- **Avoid**: Use nullable types (`String?`) when fields can be null

### 8. **Missing Documentation**
- **Problem**: No comments or documentation on entity fields
- **Scar**: Difficult for other developers to understand the purpose
- **Avoid**: Add clear comments explaining field purposes and constraints

## Red Flags I Watch For

- Stories that don't specify field types or constraints
- Requirements that seem to violate database normalization
- Requests for entities without clear business purpose
- Missing validation requirements for critical fields

## My Safety Checks

1. **Compilation Check**: Ensure the entity compiles without errors
2. **Annotation Validation**: Verify all required JPA annotations are present
3. **Type Safety**: Confirm field types match the requirements
4. **Naming Review**: Check that names follow conventions
5. **Documentation**: Ensure important fields have comments
