from datetime import datetime


class Benchmark:
    def __init__(self):
        self.start()

    def _timestamp(self) -> float:
        """ Generate a timestamp. """
        return float(datetime.utcnow().timestamp())

    def start(self) -> int:
        """ Start a benchmark. """
        self.current = self._timestamp()
        return self.current

    def end(self):
        """ Return the diff between now - start(). """
        n = self._timestamp() - self.current
        self.current = float(0)
        return n
