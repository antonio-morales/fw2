const http = require("http");

const PORT = 3000; // use 3000 to avoid root privileges
http.createServer((req, res) => {
	let body = "";
	req.on("data", chunk => body += chunk);
	req.on("end", () => {
		res.writeHead(200, { "Content-Type": "text/plain" });
		res.end(body || "No input received");
	});
}).listen(PORT, "127.0.0.1", () => {
	console.log(`Server listening on http://127.0.0.1:${PORT}`);
});

