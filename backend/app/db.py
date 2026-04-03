# Database module — manages the OpenSearch client and index lifecycle.
import json
from opensearchpy import OpenSearch
from app.config import OPENSEARCH_HOST, OPENSEARCH_PORT, INDEX_NAME

# Shared OpenSearch client instance used across all routes.
client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    http_compress=True,  # Compress request/response bodies to reduce network overhead.
    use_ssl=False,
    verify_certs=False,
)


def create_index_if_not_exists():
    """Creates the log index with its field mappings if it does not already exist."""
    if not client.indices.exists(index=INDEX_NAME):
        index_body = {
            "settings": {
                "number_of_shards": 1,    # Single shard — suitable for a single-node setup.
                "number_of_replicas": 0,  # No replicas — avoids unassigned shard warnings on one node.
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},     # ISO 8601 log timestamp.
                    "message":   {"type": "text"},     # Full-text searchable log message.
                    "service":   {"type": "keyword"},  # Exact-match service name filter.
                    "source":    {"type": "keyword"},  # Exact-match log source/host filter.
                    "level":     {"type": "integer"},  # Numeric log level (e.g. 10=DEBUG, 40=ERROR).
                    "event":     {"type": "keyword"},  # Structured event name from JSON logs.
                    "msg":       {"type": "text"},     # Full-text message field from structured logs.
                }
            },
        }
        client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"Created index: {INDEX_NAME}")


def build_filters(service: str = None, source: str = None, min_level: int = None) -> list:
    """Builds a list of OpenSearch bool-query filter clauses from optional query parameters."""
    filters = []
    if service:
        # Exact keyword match on the service field.
        filters.append({"term": {"service": service}})
    if source:
        # Exact keyword match on the source field.
        filters.append({"term": {"source": source}})
    if min_level is not None:
        # Include only logs at or above the specified numeric level.
        filters.append({"range": {"level": {"gte": min_level}}})
    return filters


def parse_log_message(message: str) -> dict:
    """Attempts to extract and parse a JSON object from a log message string.

    Handles log lines where a JSON payload is preceded by plain-text (e.g. a timestamp prefix)
    by scanning for the first '{' character before attempting to deserialize.
    Returns an empty dict if the message is empty or cannot be parsed.
    """
    if not message:
        return {}
    try:
        # Strip any leading plain-text prefix before the JSON object begins.
        json_start = message.find('{')
        if json_start > 0:
            message = message[json_start:]
        return json.loads(message)
    except (json.JSONDecodeError, ValueError):
        return {}
