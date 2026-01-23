# LogWatcher

LogWatcher is a centralized log management system for collecting and analyzing
logs from distributed applications.

This project is being developed as a Senior Engineering Project.

## High-level components
- Log forwarding agent
- Central log server (API + storage)
- Web-based dashboard

## Status
Project setup and architecture phase.

## Running the Demo App
The `demo-app` is a simple Node.js service that continuously emits structured
JSON logs. It is used to test and demonstrate the LogWatcher system.

### Prerequisites
- Node.js 18+ (for local run)
- Docker + Docker Compose (for containerized run)

### Option 1: Run locally
cd demo-app
npm install
node src/server.js

### Option 2: Run with Docker Compose
docker compose up --build


