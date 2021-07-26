import pandas as pd

from Constants.constants import *
from Models.ltp import LTP
from Models.price_data import PriceData
from Utils.general_utils import find_difference_between_two_lists

required_columns = [DATE, OPEN, HIGH, LOW, CLOSE, VOLUME]


class Share:

    def __init__(self, symbol, name, interval: str, ohlcv: pd.DataFrame):
        if len(find_difference_between_two_lists(required_columns, ohlcv.columns.values)) > 0 or len(symbol) == 0:
            raise ValueError  # todo use custom error
        self._symbol = symbol
        self._name = name
        self._price_data = PriceData(interval, ohlcv)
        self._ltp = LTP()
        self.update_ltp()

    def update_ltp(self):
        if self._price_data.ohlcv.dropna().empty:
            return
        self._ltp.price = self._price_data.ohlcv.iloc[-1].loc[CLOSE]
        self._ltp.date_str = self._price_data.ohlcv.iloc[-1].loc[DATE]

    @property
    def symbol(self):
        return self._symbol

    @property
    def name(self):
        return self._name

    @property
    def price_data(self):
        return self._price_data

    @property
    def ltp(self):
        return self._ltp
