package com.aiinterview.service;

import com.aiinterview.model.ResumeAnalysis;
import com.aiinterview.repository.ResumeAnalysisRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class ResumeService {

    @Autowired
    private ResumeAnalysisRepository repository;

    @Value("${ml.service.url:http://localhost:8001}")
    private String mlServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @SuppressWarnings("unchecked")
    public Map<String, Object> analyzeResume(MultipartFile file, String jobDescription, Long userId) {
        String url = mlServiceUrl + "/analyze-resume";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        try {
            ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            };
            body.add("file", fileResource);
        } catch (IOException e) {
            throw new RuntimeException("Failed to read bytes from uploaded resume file", e);
        }
        body.add("job_description", jobDescription);

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> responseEntity = restTemplate.postForEntity(url, requestEntity, Map.class);
        Map<String, Object> mlResult = responseEntity.getBody();

        if (mlResult == null) {
            throw new RuntimeException("Empty response from ML service");
        }

        // Save analysis to database
        try {
            Double atsScore = mlResult.get("atsScore") != null ? ((Number) mlResult.get("atsScore")).doubleValue() : 0.0;
            Double skillMatchScore = mlResult.get("skillMatchScore") != null ? ((Number) mlResult.get("skillMatchScore")).doubleValue() : 0.0;
            Double semanticScore = mlResult.get("semanticScore") != null ? ((Number) mlResult.get("semanticScore")).doubleValue() : 0.0;
            Double beforeAtsScore = mlResult.get("beforeAtsScore") != null ? ((Number) mlResult.get("beforeAtsScore")).doubleValue() : null;
            Double confidenceScore = mlResult.get("confidenceScore") != null ? ((Number) mlResult.get("confidenceScore")).doubleValue() : null;
            
            String allSkillsJson = objectMapper.writeValueAsString(mlResult.get("allSkills"));
            String matchedSkillsJson = objectMapper.writeValueAsString(mlResult.get("matchedSkills"));
            String missingSkillsJson = objectMapper.writeValueAsString(mlResult.get("missingSkills"));

            ResumeAnalysis analysis = ResumeAnalysis.builder()
                    .userId(userId)
                    .fileName(file.getOriginalFilename())
                    .jobDescription(jobDescription)
                    .atsScore(atsScore)
                    .skillMatchScore(skillMatchScore)
                    .semanticScore(semanticScore)
                    .beforeAtsScore(beforeAtsScore)
                    .confidenceScore(confidenceScore)
                    .allSkillsJson(allSkillsJson)
                    .matchedSkillsJson(matchedSkillsJson)
                    .missingSkillsJson(missingSkillsJson)
                    .build();

            ResumeAnalysis savedEntity = repository.save(analysis);

            // Include the saved record ID and creation time in return mapping
            mlResult.put("id", savedEntity.getId());
            mlResult.put("createdAt", savedEntity.getCreatedAt());

        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize skill list to JSON", e);
        }

        return mlResult;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> matchSkills(String resumeText, String jobDescription) {
        String url = mlServiceUrl + "/match-skills";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("resume_text", resumeText);
        requestBody.put("job_description", jobDescription);

        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);
        ResponseEntity<Map> responseEntity = restTemplate.postForEntity(url, requestEntity, Map.class);
        
        return responseEntity.getBody();
    }

    @SuppressWarnings("unchecked")
    public List<String> generateQuestions(List<String> skills, Integer count) {
        String url = mlServiceUrl + "/generate-questions";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("skills", skills);

        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);
        ResponseEntity<Map> responseEntity = restTemplate.postForEntity(url, requestEntity, Map.class);
        
        Map<String, Object> responseBody = responseEntity.getBody();
        if (responseBody == null || !responseBody.containsKey("questions")) {
            throw new RuntimeException("Invalid response from ML questions generator");
        }

        List<String> questions = (List<String>) responseBody.get("questions");
        
        if (count != null && count > 0 && count < questions.size()) {
            return questions.subList(0, count);
        }
        return questions;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> evaluateAnswer(String question, String answer, List<String> skills) {
        String url = mlServiceUrl + "/evaluate-answer";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("question", question);
        requestBody.put("answer", answer);
        requestBody.put("skills", skills);

        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);
        ResponseEntity<Map> responseEntity = restTemplate.postForEntity(url, requestEntity, Map.class);
        
        return responseEntity.getBody();
    }

    public List<ResumeAnalysis> getHistory(Long userId) {
        if (userId != null) {
            return repository.findTop10ByUserIdOrderByCreatedAtDesc(userId);
        }
        return repository.findTop10ByOrderByCreatedAtDesc();
    }
}
