package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateRegionRepository extends JpaRepository<RealEstateRegion, String> {

    Optional<RealEstateRegion> findFirstByLegalDongCode(String legalDongCode);

    List<RealEstateRegion> findByParentRegionId(String parentRegionId);

    @Query("""
            select new com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse(
                target.id,
                target.targetType,
                target.displayName,
                target.slug,
                target.reviewState,
                target.dataStatus,
                region.regionLevel,
                region.parentRegionId,
                region.legalDongCode,
                region.regionCode
            )
            from RealEstateRegion region
            join region.target target
            where (:query is null
                or lower(target.displayName) like concat('%', :query, '%')
                or lower(target.normalizedName) like concat('%', :normalizedQuery, '%')
                or region.legalDongCode = :rawQuery
            )
            order by target.displayName asc
            """)
    List<RealEstateTargetResponse> searchTargets(
            @Param("query") String query,
            @Param("normalizedQuery") String normalizedQuery,
            @Param("rawQuery") String rawQuery,
            Pageable pageable
    );
}
