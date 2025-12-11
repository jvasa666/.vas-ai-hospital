package com.hospital.clinical.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import java.util.*;
import java.time.LocalDateTime;

@RestController
@RequestMapping("/api")
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "clinical-service");
        response.put("timestamp", LocalDateTime.now().toString());
        response.put("version", "1.0.0");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/patients")
    public ResponseEntity<Map<String, Object>> getPatients() {
        Map<String, Object> response = new HashMap<>();
        List<Map<String, Object>> patients = new ArrayList<>();
        
        Map<String, Object> patient1 = new HashMap<>();
        patient1.put("id", "P001");
        patient1.put("name", "John Doe");
        patient1.put("age", 45);
        patient1.put("status", "stable");
        patients.add(patient1);
        
        Map<String, Object> patient2 = new HashMap<>();
        patient2.put("id", "P002");
        patient2.put("name", "Jane Smith");
        patient2.put("age", 62);
        patient2.put("status", "critical");
        patients.add(patient2);
        
        response.put("patients", patients);
        response.put("total", patients.size());
        return ResponseEntity.ok(response);
    }

    @PostMapping("/patients")
    public ResponseEntity<Map<String, Object>> createPatient(@RequestBody Map<String, Object> patient) {
        Map<String, Object> response = new HashMap<>();
        response.put("id", "P" + String.format("%03d", new Random().nextInt(999)));
        response.putAll(patient);
        response.put("created", LocalDateTime.now().toString());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/appointments")
    public ResponseEntity<Map<String, Object>> getAppointments() {
        Map<String, Object> response = new HashMap<>();
        List<Map<String, Object>> appointments = new ArrayList<>();
        
        Map<String, Object> apt1 = new HashMap<>();
        apt1.put("id", "A001");
        apt1.put("patientId", "P001");
        apt1.put("doctor", "Dr. Williams");
        apt1.put("time", "2025-10-21T10:00:00");
        apt1.put("type", "checkup");
        appointments.add(apt1);
        
        response.put("appointments", appointments);
        response.put("total", appointments.size());
        return ResponseEntity.ok(response);
    }
}
