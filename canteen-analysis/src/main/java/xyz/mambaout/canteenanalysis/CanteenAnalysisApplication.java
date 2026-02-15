package xyz.mambaout.canteenanalysis;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

/**
 * Spring Boot 应用入口：启用缓存并启动后端服务。
 */
@EnableCaching
@SpringBootApplication
public class CanteenAnalysisApplication {
    public static void main(String[] args) {
        SpringApplication.run(CanteenAnalysisApplication.class, args);
    }

}
