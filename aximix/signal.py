class Signal:
    """Minimalistic signal-slot support."""

    def __init__(self):
        self._slots = []

    def connect(self, callback):
        self._slots.append(callback)
        return callback

    def disconnect(self, connection):
        self._slots.remove(connection)

    def __call__(self, *args, **kwargs):
        for slot in self._slots:
            slot(*args, **kwargs)
