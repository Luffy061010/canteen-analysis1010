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

FROM eclipse-temurin:17-jre AS java-runtime

FROM python:3.11-slim
WORKDIR /app

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

COPY --from=java-runtime /opt/java/openjdk /opt/java/openjdk

COPY --from=java-builder /build/java/target/canteen-analysis-0.0.1-SNAPSHOT.jar /app/backend/canteen-analysis.jar
COPY canteen-analysis-python /app/python
COPY docker/backend/start.sh /app/start.sh

RUN chmod +x /app/start.sh \
        && python3 -m pip install --no-cache-dir -r /app/python/requirements.txt

EXPOSE 8080 8000

CMD ["/app/start.sh"]
