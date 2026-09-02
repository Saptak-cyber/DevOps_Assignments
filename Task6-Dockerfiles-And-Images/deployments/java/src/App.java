import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A small Java web service deployed with Docker.
 *
 * Uses a thread pool executor rather than the default single-threaded one, so
 * concurrent requests are actually handled in parallel.
 */
public class App {

    private static final int PORT =
            Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
    private static final Instant STARTED = Instant.now();
    private static final AtomicLong REQUESTS = new AtomicLong();

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);

        server.createContext("/", App::index);
        server.createContext("/info", App::info);
        server.createContext("/health", App::health);

        server.setExecutor(Executors.newFixedThreadPool(8));
        server.start();
        System.out.println("Java service listening on http://0.0.0.0:" + PORT);
    }

    private static void index(HttpExchange ex) throws java.io.IOException {
        REQUESTS.incrementAndGet();
        String body = "<!doctype html>\n"
                + "<html><head><title>Java Service</title></head>\n"
                + "<body style=\"font-family: system-ui, sans-serif; padding: 40px; max-width: 640px; margin: auto;\">\n"
                + "  <h1>Java Service</h1>\n"
                + "  <p>Deployed with Docker using a multi-stage build.</p>\n"
                + "  <p>Java runtime: " + System.getProperty("java.version") + "</p>\n"
                + "  <ul>\n"
                + "    <li><code>GET /info</code> — runtime metrics as JSON</li>\n"
                + "    <li><code>GET /health</code> — health check</li>\n"
                + "  </ul>\n"
                + "</body></html>";
        send(ex, 200, "text/html", body);
    }

    private static void info(HttpExchange ex) throws java.io.IOException {
        REQUESTS.incrementAndGet();
        Runtime rt = Runtime.getRuntime();
        String json = String.format(
                "{\"javaVersion\":\"%s\",\"processors\":%d,\"maxMemoryMB\":%d,"
                        + "\"usedMemoryMB\":%d,\"startedAt\":\"%s\",\"requests\":%d}",
                System.getProperty("java.version"),
                rt.availableProcessors(),
                rt.maxMemory() / (1024 * 1024),
                (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024),
                STARTED,
                REQUESTS.get());
        send(ex, 200, "application/json", json);
    }

    private static void health(HttpExchange ex) throws java.io.IOException {
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
