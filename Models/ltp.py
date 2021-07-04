class LTP:
    def __init__(self):
        self._timestamp = None
        self._price = None

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price):
        self._price = price
