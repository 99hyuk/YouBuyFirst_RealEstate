package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RealEstateDailyBriefingRepository extends JpaRepository<RealEstateDailyBriefing, String> {

    Optional<RealEstateDailyBriefing> findFirstByOrderByGeneratedAtDescIdDesc();
}
