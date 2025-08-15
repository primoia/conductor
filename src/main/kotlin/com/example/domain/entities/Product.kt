package com.example.domain.entities

import org.hibernate.annotations.CreationTimestamp
import org.hibernate.annotations.UpdateTimestamp
import java.math.BigDecimal
import java.time.LocalDateTime
import jakarta.persistence.*
import jakarta.validation.constraints.*

/**
 * Product entity representing items in the e-commerce system.
 * Contains product information including name, description, price, and category.
 */
@Entity
@Table(name = "products")
data class Product(
    
    /**
     * Unique identifier for the product (primary key)
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    val id: Long = 0,
    
    /**
     * Product name - required field with maximum 100 characters
     */
    @Column(name = "name", nullable = false, length = 100)
    @field:NotNull(message = "Product name cannot be null")
    @field:Size(min = 1, max = 100, message = "Product name must be between 1 and 100 characters")
    val name: String,
    
    /**
     * Product description - optional field with maximum 500 characters
     */
    @Column(name = "description", length = 500)
    @field:Size(max = 500, message = "Description cannot exceed 500 characters")
    val description: String? = null,
    
    /**
     * Product price - required field with minimum value of 0.01
     */
    @Column(name = "price", nullable = false, precision = 10, scale = 2)
    @field:NotNull(message = "Price cannot be null")
    @field:DecimalMin(value = "0.01", message = "Price must be greater than zero")
    val price: BigDecimal,
    
    /**
     * Product category - required field with maximum 50 characters
     */
    @Column(name = "category", nullable = false, length = 50)
    @field:NotNull(message = "Category cannot be null")
    @field:Size(min = 1, max = 50, message = "Category must be between 1 and 50 characters")
    val category: String,
    
    /**
     * Timestamp when the product was created - automatically set on creation
     */
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),
    
    /**
     * Timestamp when the product was last updated - automatically updated on modification
     */
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    val updatedAt: LocalDateTime = LocalDateTime.now()
)