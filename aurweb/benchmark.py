from datetime import UTC, datetime


class Benchmark:
    def __init__(self):
        self.start()

    def _timestamp(self) -> float:
        """Generate a timestamp."""
        return float(datetime.now(UTC).timestamp())

    def start(self) -> float:
        """Start a benchmark."""
        self.current = self._timestamp()
        return self.current

    def end(self) -> float:
        """Return the diff between now - start()."""
        n = self._timestamp() - self.current
        self.current = float(0)
        return n
