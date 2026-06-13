package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateAliasRepository extends JpaRepository<RealEstateAlias, Long> {

    Optional<RealEstateAlias> findByTargetIdAndNormalizedAlias(String targetId, String normalizedAlias);

    List<RealEstateAlias> findByTargetIdAndReviewStateIgnoreCaseAndAmbiguousFalseOrderByAliasAsc(
            String targetId,
            String reviewState
    );

    @Query("""
            select alias
            from RealEstateAlias alias
            where (:targetType is null or lower(alias.targetType) = lower(:targetType))
              and (:reviewState is null or lower(alias.reviewState) = lower(:reviewState))
              and (:ambiguous is null or alias.ambiguous = :ambiguous)
            order by alias.targetType asc, alias.targetId asc, alias.alias asc
            """)
    List<RealEstateAlias> findAliasesForExport(
            @Param("targetType") String targetType,
            @Param("reviewState") String reviewState,
            @Param("ambiguous") Boolean ambiguous,
            Pageable pageable
    );
}
