package com.youbuyfirst.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class YouBuyFirstApplication {

    public static void main(String[] args) {
        SpringApplication.run(YouBuyFirstApplication.class, args);
    }
}
