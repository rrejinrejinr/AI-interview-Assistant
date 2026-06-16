package com.aiinterview.controller;

import com.aiinterview.model.ResumeAnalysis;
import com.aiinterview.service.ResumeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/resume")
@CrossOrigin(origins = "${app.cors.allowed-origins:*}", allowedHeaders = "*")
public class ResumeController {

    @Autowired
    private ResumeService service;

    @Value("${ml.service.url:http://localhost:8001}")
    private String mlServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyze(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "jobDescription", required = false, defaultValue = "") String jobDescription,
            @RequestHeader(value = "X-User-Id", required = false) Long userId) {
        
        Map<String, Object> result = service.analyzeResume(file, jobDescription, userId);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/ats-score")
    public ResponseEntity<Map<String, Object>> getAtsScore(@RequestBody Map<String, String> request) {
        String resumeText = request.getOrDefault("resumeText", "");
        String jobDescription = request.getOrDefault("jobDescription", "");
        
        Map<String, Object> result = service.matchSkills(resumeText, jobDescription);
        return ResponseEntity.ok(result);
    }

    @SuppressWarnings("unchecked")
    @PostMapping("/questions")
    public ResponseEntity<List<String>> getQuestions(@RequestBody Map<String, Object> request) {
        List<String> skills = (List<String>) request.get("skills");
        Integer count = request.get("count") != null ? ((Number) request.get("count")).intValue() : 10;
        
        List<String> result = service.generateQuestions(skills, count);
        return ResponseEntity.ok(result);
    }

    @SuppressWarnings("unchecked")
    @PostMapping("/evaluate-answer")
    public ResponseEntity<Map<String, Object>> evaluateAnswer(@RequestBody Map<String, Object> request) {
        String question = (String) request.get("question");
        String answer = (String) request.get("answer");
        List<String> skills = (List<String>) request.get("skills");
        
        Map<String, Object> result = service.evaluateAnswer(question, answer, skills);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/history")
    public ResponseEntity<List<ResumeAnalysis>> getHistory(
            @RequestHeader(value = "X-User-Id", required = false) Long userId) {
        return ResponseEntity.ok(service.getHistory(userId));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> status = new HashMap<>();
        status.put("backend", "UP");
        
        try {
            String url = mlServiceUrl + "/health";
            Map<?, ?> mlHealth = restTemplate.getForObject(url, Map.class);
            if (mlHealth != null && "healthy".equals(mlHealth.get("status"))) {
                status.put("mlService", "UP");
            } else {
                status.put("mlService", "DOWN");
            }
        } catch (Exception e) {
            status.put("mlService", "DOWN");
        }
        
        return ResponseEntity.ok(status);
    }
}
