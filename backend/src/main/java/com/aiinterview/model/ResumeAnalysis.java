package com.aiinterview.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "resume_analysis")
public class ResumeAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    @Column(name = "file_name")
    private String fileName;

    @Column(name = "job_description", columnDefinition = "TEXT")
    private String jobDescription;

    @Column(name = "ats_score")
    private Double atsScore;

    @Column(name = "skill_match_score")
    private Double skillMatchScore;

    @Column(name = "semantic_score")
    private Double semanticScore;

    @Column(name = "before_ats_score")
    private Double beforeAtsScore;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "all_skills_json", columnDefinition = "TEXT")
    private String allSkillsJson;

    @Column(name = "matched_skills_json", columnDefinition = "TEXT")
    private String matchedSkillsJson;

    @Column(name = "missing_skills_json", columnDefinition = "TEXT")
    private String missingSkillsJson;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

    // Default Constructor
    public ResumeAnalysis() {}

    // All Arguments Constructor
    public ResumeAnalysis(Long id, Long userId, String fileName, String jobDescription, Double atsScore,
                          Double skillMatchScore, Double semanticScore, Double beforeAtsScore, Double confidenceScore, String allSkillsJson,
                          String matchedSkillsJson, String missingSkillsJson, LocalDateTime createdAt) {
        this.id = id;
        this.userId = userId;
        this.fileName = fileName;
        this.jobDescription = jobDescription;
        this.atsScore = atsScore;
        this.skillMatchScore = skillMatchScore;
        this.semanticScore = semanticScore;
        this.beforeAtsScore = beforeAtsScore;
        this.confidenceScore = confidenceScore;
        this.allSkillsJson = allSkillsJson;
        this.matchedSkillsJson = matchedSkillsJson;
        this.missingSkillsJson = missingSkillsJson;
        this.createdAt = createdAt;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getJobDescription() {
        return jobDescription;
    }

    public void setJobDescription(String jobDescription) {
        this.jobDescription = jobDescription;
    }

    public Double getAtsScore() {
        return atsScore;
    }

    public void setAtsScore(Double atsScore) {
        this.atsScore = atsScore;
    }

    public Double getSkillMatchScore() {
        return skillMatchScore;
    }

    public void setSkillMatchScore(Double skillMatchScore) {
        this.skillMatchScore = skillMatchScore;
    }

    public Double getSemanticScore() {
        return semanticScore;
    }

    public void setSemanticScore(Double semanticScore) {
        this.semanticScore = semanticScore;
    }

    public Double getBeforeAtsScore() {
        return beforeAtsScore;
    }

    public void setBeforeAtsScore(Double beforeAtsScore) {
        this.beforeAtsScore = beforeAtsScore;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public void setConfidenceScore(Double confidenceScore) {
        this.confidenceScore = confidenceScore;
    }

    public String getAllSkillsJson() {
        return allSkillsJson;
    }

    public void setAllSkillsJson(String allSkillsJson) {
        this.allSkillsJson = allSkillsJson;
    }

    public String getMatchedSkillsJson() {
        return matchedSkillsJson;
    }

    public void setMatchedSkillsJson(String matchedSkillsJson) {
        this.matchedSkillsJson = matchedSkillsJson;
    }

    public String getMissingSkillsJson() {
        return missingSkillsJson;
    }

    public void setMissingSkillsJson(String missingSkillsJson) {
        this.missingSkillsJson = missingSkillsJson;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    // Builder pattern implementation
    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private Long id;
        private Long userId;
        private String fileName;
        private String jobDescription;
        private Double atsScore;
        private Double skillMatchScore;
        private Double semanticScore;
        private Double beforeAtsScore;
        private Double confidenceScore;
        private String allSkillsJson;
        private String matchedSkillsJson;
        private String missingSkillsJson;
        private LocalDateTime createdAt;

        public Builder id(Long id) {
            this.id = id;
            return this;
        }

        public Builder userId(Long userId) {
            this.userId = userId;
            return this;
        }

        public Builder fileName(String fileName) {
            this.fileName = fileName;
            return this;
        }

        public Builder jobDescription(String jobDescription) {
            this.jobDescription = jobDescription;
            return this;
        }

        public Builder atsScore(Double atsScore) {
            this.atsScore = atsScore;
            return this;
        }

        public Builder skillMatchScore(Double skillMatchScore) {
            this.skillMatchScore = skillMatchScore;
            return this;
        }

        public Builder semanticScore(Double semanticScore) {
            this.semanticScore = semanticScore;
            return this;
        }

        public Builder beforeAtsScore(Double beforeAtsScore) {
            this.beforeAtsScore = beforeAtsScore;
            return this;
        }

        public Builder confidenceScore(Double confidenceScore) {
            this.confidenceScore = confidenceScore;
            return this;
        }

        public Builder allSkillsJson(String allSkillsJson) {
            this.allSkillsJson = allSkillsJson;
            return this;
        }

        public Builder matchedSkillsJson(String matchedSkillsJson) {
            this.matchedSkillsJson = matchedSkillsJson;
            return this;
        }

        public Builder missingSkillsJson(String missingSkillsJson) {
            this.missingSkillsJson = missingSkillsJson;
            return this;
        }

        public Builder createdAt(LocalDateTime createdAt) {
            this.createdAt = createdAt;
            return this;
        }

        public ResumeAnalysis build() {
            return new ResumeAnalysis(id, userId, fileName, jobDescription, atsScore, skillMatchScore, 
                                      semanticScore, beforeAtsScore, confidenceScore, allSkillsJson, matchedSkillsJson, 
                                      missingSkillsJson, createdAt);
        }
    }
}
