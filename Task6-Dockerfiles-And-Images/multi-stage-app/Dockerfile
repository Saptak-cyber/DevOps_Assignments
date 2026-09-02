#==============================================================================
# MULTI-STAGE DOCKERFILE
#
# Stage 1 "builder": a full JDK. It compiles Main.java and packages a JAR.
#                    Needs javac, jar, and everything the compiler depends on.
#
# Stage 2 "final"  : a JRE-only image. It copies ONLY app.jar out of stage 1.
#                    The compiler, the source code and all intermediate .class
#                    files stay behind in a stage that is never shipped.
#
# Why this matters:
#   - Size:     ~180 MB instead of ~555 MB (no compiler, no source, no tooling)
#   - Security: fewer packages in the final image = smaller attack surface, and
#               the source code is not shipped to production
#   - Speed:    smaller images pull and start faster
#==============================================================================

# ---------- Stage 1: BUILD ----------
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /build

# Copy the source into the build stage.
COPY src/ ./src/

# Compile into ./classes
RUN mkdir -p classes && javac -d classes src/Main.java

# Package into an executable JAR with Main-Class set in the manifest.
RUN jar --create --file app.jar --main-class Main -C classes .

# ---------- Stage 2: RUNTIME ----------
# jre-alpine has no javac, no jar, no source — only what is needed to RUN.
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# The single line that makes this a multi-stage build: reach into the previous
# stage by its name and take just the artifact.
COPY --from=builder /build/app.jar ./app.jar

# Run as a non-root user.
RUN addgroup -S app && adduser -S app -G app
USER app

# The application listens on 8080 inside the container.
EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
