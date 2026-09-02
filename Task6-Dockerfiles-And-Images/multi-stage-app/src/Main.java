import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

/**
 * Multi-stage build demo application.
 *
 * Serves "Hello World from Docker multi-stage build" on port 8080.
 * Compiled by a JDK in stage 1; run by a JRE-only image in stage 2.
 */
public class Main {

    private static final String MESSAGE = "Hello World from Docker multi-stage build";
    private static final int PORT =
            Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);
        server.createContext("/", Main::handleRoot);
        server.createContext("/health", Main::handleHealth);
        server.setExecutor(null);
        server.start();
        System.out.println(MESSAGE);
        System.out.println("Server started on http://0.0.0.0:" + PORT);
    }

    private static void handleRoot(HttpExchange ex) throws java.io.IOException {
        String body = "<!doctype html>\n"
                + "<html>\n"
                + "  <head><title>Docker Multi-Stage Build</title></head>\n"
                + "  <body style=\"font-family: system-ui, sans-serif; text-align: center; padding: 60px;\">\n"
                + "    <h1>" + MESSAGE + "</h1>\n"
                + "    <p>Built with a JDK stage, shipped on a JRE-only stage.</p>\n"
                + "    <p>Java runtime: " + System.getProperty("java.version") + "</p>\n"
                + "    <p>Listening on port " + PORT + "</p>\n"
                + "  </body>\n"
                + "</html>";
        send(ex, 200, "text/html", body);
    }

    private static void handleHealth(HttpExchange ex) throws java.io.IOException {
        send(ex, 200, "application/json", "{\"status\":\"ok\"}");
    }

    private static void send(HttpExchange ex, int code, String type, String body)
            throws java.io.IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", type + "; charset=utf-8");
        ex.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }
}
