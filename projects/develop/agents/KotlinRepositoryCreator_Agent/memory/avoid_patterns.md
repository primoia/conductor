# Patterns to Avoid (Scars): Kotlin Repository Creator Agent

## Anti-Patterns I've Learned to Avoid

### 1. **Wrong Base Interface**
- **Problem**: Extending the wrong Spring Data JPA interface
- **Scar**: Missing methods or unnecessary complexity
- **Avoid**: Use JpaRepository for full CRUD, CrudRepository for basic operations

### 2. **Incorrect Method Names**
- **Problem**: Not following Spring Data JPA naming conventions
- **Scar**: Methods that don't work or cause compilation errors
- **Avoid**: Follow the exact naming patterns: findBy[Property], countBy[Property], etc.

### 3. **Missing Type Parameters**
- **Problem**: Not specifying entity and ID types in interface declaration
- **Scar**: Compilation errors and type safety issues
- **Avoid**: Always specify Repository<EntityType, IdType>

### 4. **Over-Complex Queries**
- **Problem**: Creating overly complex @Query annotations
- **Scar**: Hard to maintain and debug queries
- **Avoid**: Use method naming conventions when possible, keep @Query simple

### 5. **Ignoring Performance**
- **Problem**: Creating inefficient query methods
- **Scar**: Slow database operations and poor application performance
- **Avoid**: Use appropriate indexes and consider query complexity

### 6. **Missing Documentation**
- **Problem**: No comments explaining custom methods
- **Scar**: Difficult for other developers to understand the purpose
- **Avoid**: Add clear comments explaining what each custom method does

### 7. **Incorrect Return Types**
- **Problem**: Using wrong return types for query methods
- **Scar**: Runtime errors and unexpected behavior
- **Avoid**: Use List<T> for multiple results, Optional<T> for single results

### 8. **Not Handling Null Values**
- **Problem**: Not considering null values in query methods
- **Scar**: Unexpected query results and data inconsistencies
- **Avoid**: Use Optional or nullable types appropriately

## Red Flags I Watch For

- Entities without clear primary key definitions
- Requirements for complex queries that should be in services
- Requests for repository methods that violate separation of concerns
- Missing entity relationships that affect query design

## My Safety Checks

1. **Compilation Check**: Ensure the repository compiles without errors
2. **Interface Validation**: Verify the correct base interface is extended
3. **Method Naming**: Check that custom methods follow conventions
4. **Type Safety**: Confirm entity and ID types are correctly specified
5. **Documentation**: Ensure custom methods have clear comments
