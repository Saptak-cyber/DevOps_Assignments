# ---------- Stage 1: compile ----------
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /build
COPY src/ ./src/

RUN mkdir -p classes \
 && javac -d classes src/App.java \
 && jar --create --file app.jar --main-class App -C classes .

# ---------- Stage 2: runtime ----------
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app
COPY --from=builder /build/app.jar ./app.jar

RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 8080

# -XX:MaxRAMPercentage tells the JVM to size its heap from the CONTAINER's
# memory limit rather than the host's. Without it, a JVM in a 512 MB container
# on a 32 GB host may size its heap for 32 GB and get OOM-killed.
CMD ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
