package com.example.domain.repositories

import com.example.domain.entities.Product
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.math.BigDecimal
import java.util.*

/**
 * Repository interface for Product entity operations.
 * 
 * Provides CRUD operations and custom query methods for Product entities.
 * Extends JpaRepository to provide full JPA functionality including
 * pagination and batch operations.
 */
@Repository
interface ProductRepository : JpaRepository<Product, Long> {

    /**
     * Find products by category.
     * 
     * @param category the product category to search for
     * @return list of products in the specified category
     */
    fun findByCategory(category: String): List<Product>

    /**
     * Find products by name containing the specified text (case-insensitive).
     * 
     * @param name the text to search for in product names
     * @return list of products with names containing the search text
     */
    fun findByNameContainingIgnoreCase(name: String): List<Product>

    /**
     * Find products within a price range.
     * 
     * @param minPrice the minimum price (inclusive)
     * @param maxPrice the maximum price (inclusive)
     * @return list of products within the specified price range
     */
    fun findByPriceBetween(minPrice: BigDecimal, maxPrice: BigDecimal): List<Product>

    /**
     * Find products by category and price range.
     * 
     * @param category the product category
     * @param minPrice the minimum price (inclusive)
     * @param maxPrice the maximum price (inclusive)
     * @return list of products matching category and price criteria
     */
    fun findByCategoryAndPriceBetween(
        category: String,
        minPrice: BigDecimal,
        maxPrice: BigDecimal
    ): List<Product>

    /**
     * Find products with price greater than specified amount.
     * 
     * @param price the minimum price threshold
     * @return list of products with price greater than the specified amount
     */
    fun findByPriceGreaterThan(price: BigDecimal): List<Product>

    /**
     * Find products with price less than specified amount.
     * 
     * @param price the maximum price threshold
     * @return list of products with price less than the specified amount
     */
    fun findByPriceLessThan(price: BigDecimal): List<Product>

    /**
     * Count products by category.
     * 
     * @param category the product category
     * @return number of products in the specified category
     */
    fun countByCategory(category: String): Long

    /**
     * Check if a product exists with the given name.
     * 
     * @param name the product name to check
     * @return true if a product with the name exists, false otherwise
     */
    fun existsByName(name: String): Boolean

    /**
     * Find the most expensive product in a category.
     * 
     * @param category the product category
     * @return optional containing the most expensive product in the category
     */
    @Query("SELECT p FROM Product p WHERE p.category = :category ORDER BY p.price DESC LIMIT 1")
    fun findMostExpensiveInCategory(@Param("category") category: String): Optional<Product>

    /**
     * Find the least expensive product in a category.
     * 
     * @param category the product category
     * @return optional containing the least expensive product in the category
     */
    @Query("SELECT p FROM Product p WHERE p.category = :category ORDER BY p.price ASC LIMIT 1")
    fun findLeastExpensiveInCategory(@Param("category") category: String): Optional<Product>
}