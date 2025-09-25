const axios = require('axios');
const crypto = require('crypto');

function generateRandomPayload(length = 100) {
    return crypto.randomBytes(length).toString('base64');
}

function generateRandomPath() {
    const randomPath = '/' + crypto.randomBytes(8).toString('hex');
    return randomPath;
}

function generateRandomMethod() {
    return ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'][Math.floor(Math.random() * 5)];
}

async function main() {
    for (let i = 0; i < 100; i++) {
        axios[generateRandomMethod()](`http://localhost:80${generateRandomPath()}`, generateRandomPayload());
    }
}

main();
