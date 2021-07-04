from Models.interval import Interval


class PriceData:
    def __init__(self):
        self._minimum_interval = Interval()
        self._interval = None
        self._ohlcv = None
