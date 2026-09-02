import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

/**
 * Hello World web server using the JDK's built-in com.sun.net.httpserver.
 * No Maven, no Gradle, no Spring — one file, compiled with javac.
 */
public class HelloWorld {

    private static final int PORT =
            Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);

        server.createContext("/", HelloWorld::handleRoot);
        server.createContext("/health", HelloWorld::handleHealth);

        server.setExecutor(null); // default single-threaded executor
        server.start();
        System.out.println("Java server listening on http://0.0.0.0:" + PORT);
    }

    private static void handleRoot(HttpExchange exchange) throws java.io.IOException {
        String body = "<!doctype html>\n"
                + "<html>\n"
                + "  <head><title>Java Hello World</title></head>\n"
                + "  <body style=\"font-family: system-ui, sans-serif; text-align: center; padding: 60px;\">\n"
                + "    <h1>Hello World from Java!</h1>\n"
                + "    <p>Running inside a Docker container.</p>\n"
                + "    <p>Java version: " + System.getProperty("java.version") + "</p>\n"
                + "  </body>\n"
                + "</html>";
        send(exchange, 200, "text/html", body);
    }

    private static void handleHealth(HttpExchange exchange) throws java.io.IOException {
        send(exchange, 200, "application/json", "{\"status\":\"ok\"}");
    }

    private static void send(HttpExchange exchange, int code, String type, String body)
            throws java.io.IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", type + "; charset=utf-8");
        exchange.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
