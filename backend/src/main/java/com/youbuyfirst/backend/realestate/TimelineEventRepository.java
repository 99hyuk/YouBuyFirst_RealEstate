package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface TimelineEventRepository extends JpaRepository<TimelineEvent, String> {

    @Query("""
            select event
            from TimelineEvent event
            where event.targetId = :targetId
              and (:eventType is null or event.eventType = :eventType)
            order by event.occurredAt desc, event.id asc
            """)
    List<TimelineEvent> searchByTarget(
            @Param("targetId") String targetId,
            @Param("eventType") String eventType,
            Pageable pageable
    );
}
