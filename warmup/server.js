const http = require("http");

http.createServer(function (req, res) {
  console.log("request received");
  res.writeHead(200, {'Content-Type': 'text/plain'});
  res.end('Hello World\n');
}).listen(1024, "127.0.0.1");