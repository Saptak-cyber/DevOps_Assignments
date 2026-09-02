# eclipse-temurin is the standard OpenJDK distribution image.
# The full JDK is needed here because we compile inside the image.
# (Task 6 shows the multi-stage version that ships only a JRE.)
FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app

COPY HelloWorld.java ./

# Compile at build time so startup is instant at run time.
RUN javac HelloWorld.java

EXPOSE 8080

CMD ["java", "HelloWorld"]
