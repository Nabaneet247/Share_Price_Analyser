import pandas as pd

from Constants.constants import *


class LTP:
    def __init__(self):
        self._date_str = None
        self._date = None
        self._price = None

    @property
    def date_str(self):
        return self._date_str

    @date_str.setter
    def date_str(self, date_str):
        self._date_str = date_str
        self._date = pd.to_datetime(date_str, format=DEFAULT_DATE_FORMAT)

    @property
    def date(self):
        return self._date

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price):
        self._price = price
