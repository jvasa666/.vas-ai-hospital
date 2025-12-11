package com.hospital.clinical;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.time.LocalDateTime;
import java.util.*;

@SpringBootApplication
@RestController
public class ClinicalServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(ClinicalServiceApplication.class, args);
        System.out.println("Clinical Service started successfully");
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("service", "clinical-service");
        response.put("timestamp", LocalDateTime.now().toString());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> ready() {
        Map<String, Object> response = new HashMap<>();
        response.put("ready", true);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/api/v1/clinical/encounters")
    public ResponseEntity<Map<String, Object>> getEncounters() {
        Map<String, Object> response = new HashMap<>();
        response.put("encounters", new ArrayList<>());
        response.put("total", 0);
        response.put("message", "Clinical service operational");
        return ResponseEntity.ok(response);
    }
}
