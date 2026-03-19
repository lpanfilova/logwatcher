import os

# OpenSearch connection settings — defaults to localhost for local development.
# Override via environment variables in docker-compose or deployment config.
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))

# Credentials for the OpenSearch admin user.
# Must be set via environment variables — never hardcoded.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Name of the OpenSearch index where logs are stored.
INDEX_NAME = "logs"
