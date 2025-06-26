const { FuzzedDataProvider } = require('@jazzer.js/core');
const moment = require('moment');

// Set locale to one with vulnerable standalone month parsing
moment.locale('be');

/**
 * The fuzz target: Jazzer.js will call this function with arbitrary input.
 */
function fuzz(data) {

  const provider = new FuzzedDataProvider(data);

  const fmtString = provider.consumeRemainingAsString();

  try {
    moment().format(fmtString);
  } catch (e) {
    // Ignore errors; we're interested in performance slowdown
  }
}

module.exports = { fuzz };

