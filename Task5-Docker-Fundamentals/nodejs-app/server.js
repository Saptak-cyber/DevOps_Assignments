// Minimal Hello World web server using only Node's built-in http module.
// No npm dependencies, so the Docker image stays small and the build is fast.
const http = require('http');

const PORT = process.env.PORT || 3000;

const page = `<!doctype html>
<html>
  <head><title>Node.js Hello World</title></head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello World from Node.js!</h1>
    <p>Running inside a Docker container.</p>
    <p>Node version: ${process.version}</p>
  </body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok' }));
  }
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(page);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Node.js server listening on http://0.0.0.0:${PORT}`);
});
