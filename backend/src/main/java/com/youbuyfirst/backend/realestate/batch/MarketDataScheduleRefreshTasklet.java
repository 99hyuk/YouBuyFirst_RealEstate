package com.youbuyfirst.backend.realestate.batch;

import com.youbuyfirst.backend.realestate.MarketDataScheduleService;
import org.springframework.batch.core.StepContribution;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.stereotype.Component;

import java.time.YearMonth;

@Component
public class MarketDataScheduleRefreshTasklet implements Tasklet {

    private final MarketDataScheduleService scheduleService;
    private final RealEstateBatchUpdatePublisher updatePublisher;

    public MarketDataScheduleRefreshTasklet(
            MarketDataScheduleService scheduleService,
            RealEstateBatchUpdatePublisher updatePublisher
    ) {
        this.scheduleService = scheduleService;
        this.updatePublisher = updatePublisher;
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) {
        String month = (String) chunkContext.getStepContext()
                .getJobParameters()
                .getOrDefault("month", scheduleService.currentMonth().toString());
        YearMonth targetMonth = YearMonth.parse(month);
        int acceptedItems = scheduleService.refreshMonth(targetMonth);
        contribution.incrementReadCount();
        contribution.incrementWriteCount(acceptedItems);
        updatePublisher.publish(new RealEstateBatchUpdateEvent(
                "market-data-schedules",
                targetMonth.toString(),
                acceptedItems,
                java.time.Instant.now()
        ));
        return RepeatStatus.FINISHED;
    }
}
