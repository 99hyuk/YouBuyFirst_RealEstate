package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RealEstateEvidenceLogRepository extends JpaRepository<RealEstateEvidenceLog, String> {

    List<RealEstateEvidenceLog> findByTarget_IdOrderByEvaluatedAtDescIdAsc(String targetId, Pageable pageable);
}
