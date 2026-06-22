package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateContentItemRepository extends JpaRepository<RealEstateContentItem, String> {

    Optional<RealEstateContentItem> findByUrl(String url);

    @Query("""
            select item
            from RealEstateContentItem item
            where (:contentType is null or item.contentType = :contentType)
            order by case
                when item.dataStatus in ('curated', 'ok') then 0
                when item.dataStatus = 'candidate' then 2
                else 1
            end,
            item.publishedAt desc nulls last,
            item.ingestedAt desc,
            item.id asc
            """)
    List<RealEstateContentItem> searchNewsroom(
            @Param("contentType") String contentType,
            Pageable pageable
    );
}
