package com.youbuyfirst.backend.realestate.batch;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.support.DefaultBatchConfiguration;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

@Configuration
@EnableConfigurationProperties(NewsroomContentProperties.class)
public class RealEstateBatchConfiguration extends DefaultBatchConfiguration {

    @Override
    protected String getDatabaseType() {
        return "MYSQL";
    }

    @Bean
    public Job newsroomContentRefreshJob(
            JobRepository jobRepository,
            Step newsroomContentRefreshStep
    ) {
        return new JobBuilder("newsroomContentRefreshJob", jobRepository)
                .start(newsroomContentRefreshStep)
                .build();
    }

    @Bean
    public Step newsroomContentRefreshStep(
            JobRepository jobRepository,
            PlatformTransactionManager transactionManager,
            NewsroomContentRefreshTasklet tasklet
    ) {
        return new StepBuilder("newsroomContentRefreshStep", jobRepository)
                .tasklet(tasklet, transactionManager)
                .build();
    }

    @Bean
    public Job marketDataScheduleRefreshJob(
            JobRepository jobRepository,
            Step marketDataScheduleRefreshStep
    ) {
        return new JobBuilder("marketDataScheduleRefreshJob", jobRepository)
                .start(marketDataScheduleRefreshStep)
                .build();
    }

    @Bean
    public Step marketDataScheduleRefreshStep(
            JobRepository jobRepository,
            PlatformTransactionManager transactionManager,
            MarketDataScheduleRefreshTasklet tasklet
    ) {
        return new StepBuilder("marketDataScheduleRefreshStep", jobRepository)
                .tasklet(tasklet, transactionManager)
                .build();
    }

    @Bean
    public Job rebWeeklyPriceIndexRefreshJob(
            JobRepository jobRepository,
            Step rebWeeklyPriceIndexRefreshStep
    ) {
        return new JobBuilder("rebWeeklyPriceIndexRefreshJob", jobRepository)
                .start(rebWeeklyPriceIndexRefreshStep)
                .build();
    }

    @Bean
    public Step rebWeeklyPriceIndexRefreshStep(
            JobRepository jobRepository,
            PlatformTransactionManager transactionManager,
            RebWeeklyPriceIndexRefreshTasklet tasklet
    ) {
        return new StepBuilder("rebWeeklyPriceIndexRefreshStep", jobRepository)
                .tasklet(tasklet, transactionManager)
                .build();
    }
}
