# LogWatcher

LogWatcher is a centralized log management system for collecting and analyzing
logs from distributed applications.

This project is being developed as a Senior Engineering Project.

## High-level components
- Log forwarding agent
- Central log server (API + storage)
- Web-based dashboard

### Prerequisites
- Docker + Docker Compose (for containerized run)
- note Docker Desktop should contain Docker Compose

### Run with Docker Compose
1. download Docker Desktop if not installed
2. start Docker desktop
3. within your terminal open the logwatcher folder
4. run the following command "docker compose up --build"
5. to access the frontend web UI, got to your browser and enter "http://localhost:5173"


