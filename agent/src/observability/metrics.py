from prometheus_client import Counter, Gauge, Histogram

logs_collected = Counter(
    "agent_logs_collected_total", 
    "Total number of log events collected from sources."
)

logs_sent = Counter(
    "agent_logs_sent_total", 
    "Total number of log events successfully sent to the backend."
)

send_failures = Counter(
    "agent_send_failures_total", 
    "Total number of failed send attempts."
)

spool_files = Gauge(
    "agent_spool_files", 
    "Number of batch files currently stored on disk."
)

spool_bytes = Gauge(
    "agent_spool_bytes", 
    "Disk space currently used by spool files in bytes."
)

ship_latency = Histogram(
    "agent_shipper_request_seconds", 
    "HTTP request duration for sending a batch to the backend."
)

dropped_batches = Counter(
    "agent_spool_dropped_batches_total", 
    "Total number of dropped batches."
)