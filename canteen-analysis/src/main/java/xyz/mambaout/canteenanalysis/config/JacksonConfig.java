package xyz.mambaout.canteenanalysis.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializer;

@Configuration
public class JacksonConfig {

    @Bean
    public RedisSerializer<Object> redisSerializer() {
        ObjectMapper objectMapper = new ObjectMapper();
        // 注册 JSR310 模块，支持 LocalDateTime 序列化
        objectMapper.registerModule(new JavaTimeModule());
        // 其他配置...
        return new GenericJackson2JsonRedisSerializer(objectMapper);
    }
}