let hex = 0xA;
while (true) {
    hex = (0xA << 16) + hex;
    fetch("http://localhost:80".concat(new URLSearchParams({howdy: hex})), { method: 'GET'})
}

