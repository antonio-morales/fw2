const crypto = require('crypto');
var http = require("http");
let i;
while (i < 100) {
    i++;
    crypto.randomBytes(512, (err, buf) => {
    // Prints random bytes of generated data
    console.log("The random data is: "+ buf.toString('hex'));

    var options = {
        host: "127.0.0.1",
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
