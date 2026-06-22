package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface RealEstateTargetRepository extends JpaRepository<RealEstateTarget, String> {

    @Query("""
            select new com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse(
                target.id,
                target.targetType,
                target.displayName,
                target.slug,
                target.reviewState,
                target.dataStatus,
                case when target.targetType = 'complex' then 'complex' else region.regionLevel end,
                case when target.targetType = 'complex' then complex.regionTargetId else region.parentRegionId end,
                case when target.targetType = 'complex' then complex.legalDongCode else region.legalDongCode end,
                region.regionCode
            )
            from RealEstateTarget target
            left join RealEstateRegion region on region.targetId = target.id
            left join RealEstateComplex complex on complex.targetId = target.id
            where (:query is null
                or lower(target.displayName) like concat('%', :query, '%')
                or lower(target.normalizedName) like concat('%', :normalizedQuery, '%')
                or lower(target.slug) like concat('%', :normalizedQuery, '%')
                or lower(target.id) like concat('%', :normalizedQuery, '%')
                or region.legalDongCode = :rawQuery
                or complex.legalDongCode = :rawQuery
                or exists (
                    select alias.id
                    from RealEstateAlias alias
                    where alias.targetId = target.id
                      and lower(alias.targetType) = lower(target.targetType)
                      and lower(alias.reviewState) = 'approved'
                      and alias.ambiguous = false
                      and (
                          lower(alias.alias) like concat('%', :query, '%')
                          or lower(alias.normalizedAlias) like concat('%', :aliasQuery, '%')
                      )
                )
            )
            order by
                case
                    when :query is not null and lower(target.normalizedName) = :normalizedQuery then 0
                    when :aliasQuery is not null and exists (
                        select exactAlias.id
                        from RealEstateAlias exactAlias
                        where exactAlias.targetId = target.id
                          and lower(exactAlias.targetType) = lower(target.targetType)
                          and lower(exactAlias.reviewState) = 'approved'
                          and exactAlias.ambiguous = false
                          and lower(exactAlias.normalizedAlias) = :aliasQuery
                    ) then 0
                    when :query is not null and lower(target.displayName) like concat(:query, '%') then 1
                    else 2
                end asc,
                case
                    when target.targetType = 'region' then 0
                    when target.targetType = 'complex' then 1
                    else 2
                end asc,
                case
                    when target.dataStatus = 'ok' then 0
                    when target.dataStatus = 'partial' then 1
                    when target.dataStatus = 'candidate' then 2
                    when target.dataStatus = 'mock' then 3
                    else 4
                end asc,
                target.displayName asc
            """)
    List<RealEstateTargetResponse> searchTargets(
            @Param("query") String query,
            @Param("normalizedQuery") String normalizedQuery,
            @Param("aliasQuery") String aliasQuery,
            @Param("rawQuery") String rawQuery,
            Pageable pageable
    );
}
