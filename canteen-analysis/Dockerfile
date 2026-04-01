FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /build

COPY pom.xml ./
COPY maven-settings.xml /root/.m2/settings.xml
COPY src ./src

RUN set -eux; \
		ok=0; \
		for i in 1 2 3; do \
			mvn -s /root/.m2/settings.xml -B -DskipTests clean package && ok=1 && break; \
			echo "maven build failed, retrying... ($i/3)"; \
			sleep 10; \
		done; \
		if [ "$ok" -ne 1 ]; then \
			echo "maven build failed after retries"; \
			exit 1; \
		fi

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=builder /build/target/canteen-analysis-0.0.1-SNAPSHOT.jar /app/app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
