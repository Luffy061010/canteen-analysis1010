FROM maven:3.9.9-eclipse-temurin-17 AS java-builder
WORKDIR /build/java

COPY canteen-analysis/pom.xml ./pom.xml
COPY canteen-analysis/src ./src
COPY docker/backend/maven-settings.xml /root/.m2/settings.xml
RUN set -eux; \
                for i in 1 2 3; do \
                        mvn -s /root/.m2/settings.xml -B -DskipTests clean package && break; \
                        echo "maven build failed, retrying in 10s... ($i/3)"; \
                        sleep 10; \
                done

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=java-builder /build/java/target/canteen-analysis-0.0.1-SNAPSHOT.jar /app/canteen-analysis.jar

EXPOSE 8080

CMD ["java", "-jar", "/app/canteen-analysis.jar"]
