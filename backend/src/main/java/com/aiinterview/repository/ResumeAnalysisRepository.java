package com.aiinterview.repository;

import com.aiinterview.model.ResumeAnalysis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ResumeAnalysisRepository extends JpaRepository<ResumeAnalysis, Long> {
    List<ResumeAnalysis> findTop10ByOrderByCreatedAtDesc();
    List<ResumeAnalysis> findTop10ByUserIdOrderByCreatedAtDesc(Long userId);
}
