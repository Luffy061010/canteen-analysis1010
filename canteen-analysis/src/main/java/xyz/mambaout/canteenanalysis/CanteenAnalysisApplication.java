package xyz.mambaout.canteenanalysis;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@EnableCaching
@SpringBootApplication
public class CanteenAnalysisApplication {
    public static void main(String[] args) {
        SpringApplication.run(CanteenAnalysisApplication.class, args);
    }

}
