from prometheus_client import Counter, Gauge, Histogram

logs_collected = Counter("agent_logs_collected_total", "Total logs collected from containers")

logs_sent = Counter("agent_logs_sent_total", "Total logs successfully sent")

send_failures = Counter("agent_send_failures_total", "Total failed send attempts")

spool_files = Gauge("agent_spool_files", "Number of batch files currently on disk (backlog)")

spool_bytes = Gauge("agent_spool_bytes", "Disk spool usage in bytes")

ship_latency = Histogram("agent_shipper_request_seconds", "HTTP request duration when sending a batch")

dropped_batches = Counter("agent_spool_dropped_batches_total", "Dropped batches")