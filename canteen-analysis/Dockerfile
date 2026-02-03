FROM maven:3.9.4-eclipse-temurin-17 AS build
WORKDIR /workspace

# Copy pom first to leverage Docker cache
COPY pom.xml ./
COPY src ./src

RUN mvn -DskipTests package -U

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /workspace/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
