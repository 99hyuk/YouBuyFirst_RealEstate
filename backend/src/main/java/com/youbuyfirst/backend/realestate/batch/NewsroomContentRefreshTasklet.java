package com.youbuyfirst.backend.realestate.batch;

import com.youbuyfirst.backend.realestate.RealEstateContentService;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentItemRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.StepContribution;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

@Component
public class NewsroomContentRefreshTasklet implements Tasklet {

    private static final Logger log = LoggerFactory.getLogger(NewsroomContentRefreshTasklet.class);

    private final NewsroomContentCollector collector;
    private final RealEstateContentService contentService;
    private final RealEstateBatchUpdatePublisher updatePublisher;

    public NewsroomContentRefreshTasklet(
            NewsroomContentCollector collector,
            RealEstateContentService contentService,
            RealEstateBatchUpdatePublisher updatePublisher
    ) {
        this.collector = collector;
        this.contentService = contentService;
        this.updatePublisher = updatePublisher;
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) {
        List<RealEstateContentItemRequest> items = collector.collect(Instant.now());
        logCollectedItems(items);
        RealEstateContentBatchResponse response = contentService.upsertAll(items);
        contribution.incrementReadCount();
        contribution.incrementWriteCount(response.acceptedItems());
        updatePublisher.publish(new RealEstateBatchUpdateEvent(
                "newsroom",
                null,
                response.acceptedItems(),
                Instant.now()
        ));
        return RepeatStatus.FINISHED;
    }

    private void logCollectedItems(List<RealEstateContentItemRequest> items) {
        if (items.isEmpty()) {
            log.info("newsroom content refresh collected no items");
            return;
        }
        String summary = items.stream()
                .collect(Collectors.groupingBy(
                        item -> "%s/%s/%s".formatted(item.contentType(), item.sourceId(), item.dataStatus()),
                        Collectors.counting()
                ))
                .entrySet()
                .stream()
                .sorted(java.util.Map.Entry.comparingByKey())
                .map(entry -> entry.getKey() + "=" + entry.getValue())
                .collect(Collectors.joining(", "));
        log.info("newsroom content refresh collected {} items: {}", items.size(), summary);
    }
}
