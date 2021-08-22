import matplotlib.pyplot as plt

from Constants.constants import *
from Models.share import Share
from Services.local_data.data_reader import get_share_ohlcv_data


def add_50_day_high(share: Share):
    price_data = share.price_data.ohlcv
    price_data[HIGH_50D] = price_data[CLOSE].rolling(50).max()


def add_50_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_50D] = price_data[CLOSE].rolling(50).min()


def add_100_day_high(share: Share):
    price_data = share.price_data.ohlcv
    price_data[HIGH_100D] = price_data[CLOSE].rolling(100).max()


def add_100_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_100D] = price_data[CLOSE].rolling(100).min()


def add_200_day_high(share: Share):
    price_data = share.price_data.ohlcv
    price_data[HIGH_200D] = price_data[CLOSE].rolling(200).max()


def add_200_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_200D] = price_data[CLOSE].rolling(200).min()


def add_20_day_high(share: Share):
    price_data = share.price_data.ohlcv
    price_data[HIGH_20D] = price_data[CLOSE].rolling(20).max()


def add_30_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_30D] = price_data[CLOSE].rolling(30).min()


def add_20_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_20D] = price_data[CLOSE].rolling(20).min()


def add_10_day_low(share: Share):
    price_data = share.price_data.ohlcv
    price_data[LOW_10D] = price_data[CLOSE].rolling(10).min()


if __name__ == '__main__':
    sbin = Share('TCS', 'State BIN', '1D', get_share_ohlcv_data('SBIN', '1D'))
    # add_200_day_low(sbin)
    add_50_day_high(sbin)
    sbin.price_data.ohlcv.set_index(DATE)[[CLOSE, HIGH_100D, LOW_200D]].plot.line()
    plt.show()
