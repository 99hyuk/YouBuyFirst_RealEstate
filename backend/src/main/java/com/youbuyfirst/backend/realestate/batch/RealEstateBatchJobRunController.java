package com.youbuyfirst.backend.realestate.batch;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.time.YearMonth;

@RestController
public class RealEstateBatchJobRunController {

    private final JobLauncher jobLauncher;
    private final Job newsroomContentRefreshJob;
    private final Job marketDataScheduleRefreshJob;
    private final Job rebWeeklyPriceIndexRefreshJob;

    public RealEstateBatchJobRunController(
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

    @PostMapping("/internal/realestate/batch-jobs/{jobName}/run")
    public RealEstateBatchJobRunResponse runJob(
            @PathVariable String jobName,
            @RequestParam(required = false) String month,
            @RequestParam(required = false) String asOf
    ) throws Exception {
        Job job = jobFor(jobName);
        JobParametersBuilder parameters = new JobParametersBuilder()
                .addString("manualRunId", jobName + "-" + Instant.now().toEpochMilli());
        if ("marketDataScheduleRefreshJob".equals(jobName)) {
            parameters.addString("month", normalizeMonth(month));
        }
        if ("rebWeeklyPriceIndexRefreshJob".equals(jobName)) {
            parameters.addString("asOf", normalizeAsOf(asOf));
        }

        JobExecution execution = jobLauncher.run(job, parameters.toJobParameters());
        return new RealEstateBatchJobRunResponse(
                jobName,
                execution.getStatus().name(),
                execution.getExitStatus().getExitCode(),
                execution.getJobParameters().getString("month"),
                execution.getStartTime() == null ? null : execution.getStartTime().atZone(java.time.ZoneOffset.UTC).toInstant(),
                execution.getEndTime() == null ? null : execution.getEndTime().atZone(java.time.ZoneOffset.UTC).toInstant()
        );
    }

    private Job jobFor(String jobName) {
        return switch (jobName) {
            case "newsroomContentRefreshJob" -> newsroomContentRefreshJob;
            case "marketDataScheduleRefreshJob" -> marketDataScheduleRefreshJob;
            case "rebWeeklyPriceIndexRefreshJob" -> rebWeeklyPriceIndexRefreshJob;
            default -> throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Unknown real estate batch job: " + jobName);
        };
    }

    private String normalizeMonth(String month) {
        if (month == null || month.isBlank()) {
            return YearMonth.now(java.time.ZoneId.of("Asia/Seoul")).toString();
        }
        return YearMonth.parse(month).toString();
    }

    private String normalizeAsOf(String asOf) {
        if (asOf == null || asOf.isBlank()) {
            return Instant.now().toString();
        }
        return Instant.parse(asOf).toString();
    }
}
