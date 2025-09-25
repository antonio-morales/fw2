// server.js
const express = require('express');
const app = express();
const PORT = 3000;

// Middleware to parse JSON
app.use(express.json());

// POST endpoint
app.post('/api/data', (req, res) => {
  const { value } = req.body;

  if (typeof value !== 'number') {
    console.log('Invalid payload:', req.body);
    return res.status(400).json({ error: 'Invalid value type. Expected number.' });
  }

  console.log('Received value:', value);

  if (value > 10) {
    console.error('Value is too big! Crashing the server...');
    process.exit(1); // Crash the server
  }

  res.status(200).json({ message: 'Value received OK' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

