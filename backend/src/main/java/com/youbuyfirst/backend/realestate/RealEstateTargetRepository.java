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

    @Query(value = """
            select
                target.id as targetId,
                target.target_type as targetType,
                target.display_name as displayName,
                target.slug as slug,
                target.review_state as reviewState,
                target.data_status as dataStatus,
                case when target.target_type = 'complex' then 'complex' else region.region_level end as regionLevel,
                case when target.target_type = 'complex' then complex.region_target_id else region.parent_region_id end as parentTargetId,
                case when target.target_type = 'complex' then coalesce(complex.legal_dong_code, parent_region.legal_dong_code) else region.legal_dong_code end as legalDongCode,
                case when target.target_type = 'complex' then parent_region.region_code else region.region_code end as regionCode
            from (
                select matched.target_id, min(matched.score) as score
                from (
                    select exact_target.id as target_id, 0 as score
                    from real_estate_targets exact_target
                    where exact_target.normalized_name = :normalizedQuery
                       or exact_target.slug = :normalizedQuery
                       or exact_target.id = :normalizedQuery
                    union all
                    select exact_region.target_id as target_id, 0 as score
                    from real_estate_regions exact_region
                    where exact_region.legal_dong_code = :rawQuery
                    union all
                    select exact_complex.target_id as target_id, 0 as score
                    from real_estate_complexes exact_complex
                    where exact_complex.legal_dong_code = :rawQuery
                    union all
                    select exact_alias.target_id as target_id, 0 as score
                    from real_estate_aliases exact_alias
                    where exact_alias.review_state = 'approved'
                      and exact_alias.ambiguous = false
                      and exact_alias.normalized_alias = :aliasQuery
                    union all
                    select prefix_target.id as target_id, 1 as score
                    from real_estate_targets prefix_target
                    where prefix_target.normalized_name like concat(:normalizedQuery, '%')
                       or prefix_target.slug like concat(:normalizedQuery, '%')
                       or prefix_target.id like concat(:normalizedQuery, '%')
                    union all
                    select prefix_region.target_id as target_id, 1 as score
                    from real_estate_regions prefix_region
                    where prefix_region.legal_dong_code like concat(:rawQuery, '%')
                    union all
                    select prefix_complex.target_id as target_id, 1 as score
                    from real_estate_complexes prefix_complex
                    where prefix_complex.legal_dong_code like concat(:rawQuery, '%')
                    union all
                    select prefix_alias.target_id as target_id, 1 as score
                    from real_estate_aliases prefix_alias
                    where prefix_alias.review_state = 'approved'
                      and prefix_alias.ambiguous = false
                      and prefix_alias.normalized_alias like concat(:aliasQuery, '%')
                    union all
                    select contains_region_target.id as target_id, 1 as score
                    from real_estate_targets contains_region_target
                    where contains_region_target.target_type = 'region'
                      and contains_region_target.normalized_name like concat('%', :normalizedQuery, '%')
                ) matched
                group by matched.target_id
            ) ranked
            join real_estate_targets target on target.id = ranked.target_id
            left join real_estate_regions region on region.target_id = target.id
            left join real_estate_complexes complex on complex.target_id = target.id
            left join real_estate_regions parent_region on parent_region.target_id = complex.region_target_id
            order by
                ranked.score asc,
                case
                    when target.target_type = 'region' then 0
                    when target.target_type = 'complex' then 1
                    else 2
                end asc,
                case
                    when target.data_status = 'ok' then 0
                    when target.data_status = 'partial' then 1
                    when target.data_status = 'candidate' then 2
                    when target.data_status = 'mock' then 3
                    else 4
                end asc,
                target.display_name asc
            """, nativeQuery = true)
    List<RealEstateTargetSearchRow> searchTargetsIndexed(
            @Param("normalizedQuery") String normalizedQuery,
            @Param("aliasQuery") String aliasQuery,
            @Param("rawQuery") String rawQuery,
            Pageable pageable
    );

    @Query(value = """
            select
                target.id as targetId,
                target.target_type as targetType,
                target.display_name as displayName,
                target.slug as slug,
                target.review_state as reviewState,
                target.data_status as dataStatus,
                case when target.target_type = 'complex' then 'complex' else region.region_level end as regionLevel,
                case when target.target_type = 'complex' then complex.region_target_id else region.parent_region_id end as parentTargetId,
                case when target.target_type = 'complex' then coalesce(complex.legal_dong_code, parent_region.legal_dong_code) else region.legal_dong_code end as legalDongCode,
                case when target.target_type = 'complex' then parent_region.region_code else region.region_code end as regionCode
            from (
                select matched.target_id, min(matched.score) as score
                from (
                    select exact_target.id as target_id, 0 as score
                    from real_estate_targets exact_target
                    left join real_estate_regions exact_region on exact_region.target_id = exact_target.id
                    left join real_estate_complexes exact_complex on exact_complex.target_id = exact_target.id
                    where exact_target.normalized_name = :normalizedQuery
                       or exact_target.slug = :normalizedQuery
                       or exact_target.id = :normalizedQuery
                       or exact_region.legal_dong_code = :rawQuery
                       or exact_complex.legal_dong_code = :rawQuery
                    union all
                    select exact_alias.target_id as target_id, 0 as score
                    from real_estate_aliases exact_alias
                    where exact_alias.review_state = 'approved'
                      and exact_alias.ambiguous = false
                      and exact_alias.normalized_alias = :aliasQuery
                    union all
                    select prefix_target.id as target_id, 1 as score
                    from real_estate_targets prefix_target
                    left join real_estate_regions prefix_region on prefix_region.target_id = prefix_target.id
                    left join real_estate_complexes prefix_complex on prefix_complex.target_id = prefix_target.id
                    where prefix_target.display_name like concat(:query, '%')
                       or prefix_target.normalized_name like concat(:normalizedQuery, '%')
                       or prefix_target.slug like concat(:normalizedQuery, '%')
                       or prefix_target.id like concat(:normalizedQuery, '%')
                       or prefix_region.legal_dong_code like concat(:rawQuery, '%')
                       or prefix_complex.legal_dong_code like concat(:rawQuery, '%')
                    union all
                    select prefix_alias.target_id as target_id, 1 as score
                    from real_estate_aliases prefix_alias
                    where prefix_alias.review_state = 'approved'
                      and prefix_alias.ambiguous = false
                      and (
                          prefix_alias.alias like concat(:query, '%')
                          or prefix_alias.normalized_alias like concat(:aliasQuery, '%')
                      )
                    union all
                    select contains_target.id as target_id, 2 as score
                    from real_estate_targets contains_target
                    left join real_estate_regions contains_region on contains_region.target_id = contains_target.id
                    left join real_estate_complexes contains_complex on contains_complex.target_id = contains_target.id
                    where contains_target.display_name like concat('%', :query, '%')
                       or contains_target.normalized_name like concat('%', :normalizedQuery, '%')
                       or contains_target.slug like concat('%', :normalizedQuery, '%')
                       or contains_target.id like concat('%', :normalizedQuery, '%')
                       or contains_region.legal_dong_code = :rawQuery
                       or contains_complex.legal_dong_code = :rawQuery
                    union all
                    select contains_alias.target_id as target_id, 2 as score
                    from real_estate_aliases contains_alias
                    where contains_alias.review_state = 'approved'
                      and contains_alias.ambiguous = false
                      and (
                          contains_alias.alias like concat('%', :query, '%')
                          or contains_alias.normalized_alias like concat('%', :aliasQuery, '%')
                      )
                ) matched
                group by matched.target_id
            ) ranked
            join real_estate_targets target on target.id = ranked.target_id
            left join real_estate_regions region on region.target_id = target.id
            left join real_estate_complexes complex on complex.target_id = target.id
            left join real_estate_regions parent_region on parent_region.target_id = complex.region_target_id
            order by
                ranked.score asc,
                case
                    when target.target_type = 'region' then 0
                    when target.target_type = 'complex' then 1
                    else 2
                end asc,
                case
                    when target.data_status = 'ok' then 0
                    when target.data_status = 'partial' then 1
                    when target.data_status = 'candidate' then 2
                    when target.data_status = 'mock' then 3
                    else 4
                end asc,
                target.display_name asc
            """, nativeQuery = true)
    List<RealEstateTargetSearchRow> searchTargetsOptimized(
            @Param("query") String query,
            @Param("normalizedQuery") String normalizedQuery,
            @Param("aliasQuery") String aliasQuery,
            @Param("rawQuery") String rawQuery,
            Pageable pageable
    );

    interface RealEstateTargetSearchRow {
        String getTargetId();

        String getTargetType();

        String getDisplayName();

        String getSlug();

        String getReviewState();

        String getDataStatus();

        String getRegionLevel();

        String getParentTargetId();

        String getLegalDongCode();

        String getRegionCode();
    }
}
