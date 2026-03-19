import json
from opensearchpy import OpenSearch
from app.config import OPENSEARCH_HOST, OPENSEARCH_PORT, INDEX_NAME

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)


def create_index_if_not_exists():
    if not client.indices.exists(index=INDEX_NAME):
        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "message":   {"type": "text"},
                    "service":   {"type": "keyword"},
                    "source":    {"type": "keyword"},
                    "level":     {"type": "integer"},
                    "event":     {"type": "keyword"},
                    "msg":       {"type": "text"},
                }
            },
        }
        client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"Created index: {INDEX_NAME}")


def build_filters(service: str = None, source: str = None, min_level: int = None) -> list:
    filters = []
    if service:
        filters.append({"term": {"service": service}})
    if source:
        filters.append({"term": {"source": source}})
    if min_level is not None:
        filters.append({"range": {"level": {"gte": min_level}}})
    return filters


def parse_log_message(message: str) -> dict:
    if not message:
        return {}
    try:
        json_start = message.find('{')
        if json_start > 0:
            message = message[json_start:]
        return json.loads(message)
    except (json.JSONDecodeError, ValueError):
        return {}
