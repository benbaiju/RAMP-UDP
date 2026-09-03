import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ProtocolMetrics:
    messages_sent: int = 0
    messages_delivered: int = 0
    retransmissions: int = 0
    duplicates: int = 0
    out_of_order_packets: int = 0
    authentication_failures: int = 0
    successful_transmissions: int = 0
    transmission_failures: int = 0
    latency_seconds: list[float] = field(default_factory=list)

    def record_latency(self, started_at: float) -> None:
        self.latency_seconds.append(time.monotonic() - started_at)

    def write(self, path: str | None = None) -> None:
        output_path = path or os.environ.get("RAMP_METRICS_FILE")
        if output_path is None:
            return
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            json.dumps(asdict(self), indent=2) + "\n",
            encoding="utf-8",
        )
