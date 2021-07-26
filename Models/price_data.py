import pandas as pd

from Models.interval import Interval
from Utils.datetime_utils import get_interval_obj_from_string


class PriceData:
    def __init__(self, interval_str, ohlcv: pd.DataFrame):
        self._minimum_interval = get_interval_obj_from_string(interval_str)
        self._interval = get_interval_obj_from_string(interval_str)
        self._ohlcv = ohlcv

    @property
    def minimum_interval(self):
        return self._minimum_interval

    @minimum_interval.setter
    def minimum_interval(self, minimum_interval: Interval):
        self._minimum_interval = minimum_interval

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, interval: Interval):
        self._interval = interval

    @property
    def ohlcv(self):
        return self._ohlcv

    @ohlcv.setter
    def ohlcv(self, ohlcv: pd.DataFrame):
        self._ohlcv = ohlcv
