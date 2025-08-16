package com.example.demo

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@SpringBootApplication
class DemoApplication

fun main(args: Array<String>) {
    runApplication<DemoApplication>(*args)
}

@RestController
class HelloController {
    
    @GetMapping("/")
    fun hello(): String {
        return "🎼 Hello from Conductor! Your {{team_name}} is ready to go!"
    }
    
    @GetMapping("/health")
    fun health(): Map<String, String> {
        return mapOf(
            "status" to "UP",
            "conductor" to "ACTIVE",
            "message" to "Team agents configured successfully",
            "project" to "{{project_name}}",
            "environment" to "{{environment}}"
        )
    }
}