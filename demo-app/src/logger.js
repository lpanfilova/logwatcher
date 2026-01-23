const pino = require('pino');

const logger = pino({
  level: 'info',
  base: {
    service: 'demo-app',
    env: 'development',
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: {
    service: 'demo-app',
  },
});

module.exports = logger;