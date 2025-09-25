const crypto = require('crypto');
var http = require("http");
let i = 0;
while (i < 1000) {
    i++;
    crypto.randomBytes(4096, (err, buf) => {
    // Prints random bytes of generated data
    console.log("The random data is: "+ buf.toString('hex'));

    var options = {
        host: "127.0.0.1",
        port: 1024,
        path: "/",
        method: "POST",
        headers: {
            "Content-Type": "multipart/form-data"
        }
    };
    var request = http.request(options, function(response) {});
    var requestBody = buf;
    request.write(requestBody);
    request.end();
});
}
