import { createServer } from "node:http";

const PORT = Number(process.env.PORT ?? 8080);

const routes = new Set(["/", "/health", "/admin", "/login", "/api/users", "/api/status", "/.env", "/robots.txt"]);

createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
  if (routes.has(url.pathname)) {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, path: url.pathname }));
    return;
  }
  res.writeHead(404);
  res.end("not found");
}).listen(PORT, "127.0.0.1", () => {
  console.log(`target → http://127.0.0.1:${PORT}`);
});
