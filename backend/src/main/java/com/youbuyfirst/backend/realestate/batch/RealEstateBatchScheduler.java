package com.youbuyfirst.backend.realestate.batch;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.YearMonth;
import java.time.ZoneId;

@Component
@ConditionalOnProperty(prefix = "app.realestate.batch", name = "scheduling-enabled", havingValue = "true", matchIfMissing = true)
public class RealEstateBatchScheduler {

    private static final Logger logger = LoggerFactory.getLogger(RealEstateBatchScheduler.class);
    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");

    private final JobLauncher jobLauncher;
    private final Job newsroomContentRefreshJob;
    private final Job marketDataScheduleRefreshJob;
    private final Job rebWeeklyPriceIndexRefreshJob;

    public RealEstateBatchScheduler(
            JobLauncher jobLauncher,
            @Qualifier("newsroomContentRefreshJob") Job newsroomContentRefreshJob,
            @Qualifier("marketDataScheduleRefreshJob") Job marketDataScheduleRefreshJob,
            @Qualifier("rebWeeklyPriceIndexRefreshJob") Job rebWeeklyPriceIndexRefreshJob
    ) {
        this.jobLauncher = jobLauncher;
        this.newsroomContentRefreshJob = newsroomContentRefreshJob;
        this.marketDataScheduleRefreshJob = marketDataScheduleRefreshJob;
        this.rebWeeklyPriceIndexRefreshJob = rebWeeklyPriceIndexRefreshJob;
    }

    @Scheduled(cron = "${app.realestate.batch.newsroom-cron:0 20 */2 * * *}", zone = "${app.realestate.batch.zone:Asia/Seoul}")
    public void runNewsroomContentRefresh() {
        launch(newsroomContentRefreshJob, new JobParametersBuilder()
                .addString("runAt", Instant.now().toString())
                .toJobParameters());
    }

    @Scheduled(cron = "${app.realestate.batch.schedule-cron:0 10 4 * * *}", zone = "${app.realestate.batch.zone:Asia/Seoul}")
    public void runMarketDataScheduleRefresh() {
        launch(marketDataScheduleRefreshJob, new JobParametersBuilder()
                .addString("runAt", Instant.now().toString())
                .addString("month", YearMonth.now(SEOUL_ZONE).toString())
                .toJobParameters());
    }

    @Scheduled(cron = "${app.realestate.batch.reb-weekly-price-index-cron:0 30 8 * * THU}", zone = "${app.realestate.batch.zone:Asia/Seoul}")
    public void runRebWeeklyPriceIndexRefresh() {
        Instant now = Instant.now();
        launch(rebWeeklyPriceIndexRefreshJob, new JobParametersBuilder()
                .addString("runAt", now.toString())
                .addString("asOf", now.toString())
                .toJobParameters());
    }

    private void launch(Job job, JobParameters parameters) {
        try {
            jobLauncher.run(job, parameters);
        } catch (Exception exc) {
            logger.warn("real-estate batch job failed; job={}", job.getName(), exc);
        }
    }
}
