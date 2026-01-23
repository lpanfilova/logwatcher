const express = require('express');
const logger = require('./logger');

// 2 second interval between logs
const LOG_INTERVAL_MS = 2000;

const app = express();
const PORT = process.env.PORT || 8888;

app.get('/', (req, res) => res.send('OK'));

app.get('/health', (req, res) => {
  logger.info({ event: 'health_check' }, 'Health check');
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Demo app listening on port ${PORT}`);
});

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick(arr) {
  return arr[randInt(0, arr.length - 1)];
}


function emitDemoLog() {
  const userId = randInt(1, 50);

  // Choose a log "type" randomly
  const r = Math.random();

  // Normal request
  if (r < 0.55) {
    const route = pick(['/api/products', '/api/orders', '/api/login', '/api/profile']);
    const latencyMs = randInt(20, 900);

    logger.info(
      {
        event: 'http_request',
        userId,
        route,
        method: 'GET',
        statusCode: 200,
        latencyMs,
      },
      'Request handled'
    );
    return;
  }

  // 2) User login
  if (r < 0.75) {
    logger.info(
      {
        event: 'user_login',
        userId,
        authProvider: pick(['local', 'google', 'github']),
      },
      'User logged in'
    );
    return;
  }

  // 3) Database connection refused (error)
  if (r < 0.88) {
    const err = new Error('connect ECONNREFUSED 127.0.0.1:5432');
    logger.error(
      {
        event: 'db_connection_failed',
        component: 'database',
        dbHost: '127.0.0.1',
        dbPort: 5432,
        errorCode: 'ECONNREFUSED',
        err,
      },
      'Database connection refused'
    );
    return;
  }

  // 4) Database query slow (warning)
  if (r < 0.97) {
    const durationMs = randInt(800, 5000);
    logger.warn(
      {
        event: 'db_query_slow',
        component: 'database',
        queryName: pick(['getUserById', 'searchProducts', 'listOrders']),
        durationMs,
        userId,
      },
      'Slow database query'
    );
    return;
  }

  // 5) Unauthorized access attempt (warning)
  logger.warn(
    {
      event: 'auth_failed',
      userId,
      route: pick(['/api/admin', '/api/billing', '/api/internal']),
      reason: pick(['missing_token', 'expired_token', 'invalid_token']),
    },
    'Unauthorized access attempt'
  );
}

// Emit logs continuously
setInterval(emitDemoLog, LOG_INTERVAL_MS);

// Graceful shutdown logs
process.on('SIGINT', () => {
  logger.warn({ event: 'shutdown', signal: 'SIGINT' }, 'Shutting down demo app');
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.warn({ event: 'shutdown', signal: 'SIGTERM' }, 'Shutting down demo app');
  process.exit(0);
});