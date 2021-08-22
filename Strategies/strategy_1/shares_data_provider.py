from loguru import logger

from Indicators.trend.high_low import *
from Services.local_data.data_manager import get_share_object_for_symbol
from Services.local_data.data_reader import get_indices_data


def load_shares_data(symbols=None):
    shares_data = {}
    if symbols is None:
        symbols = get_indices_data('NIFTY200')['Symbol'].tolist()
    logger.info('Loading share price data')
    for symbol in symbols:
        share = get_share_object_for_symbol(symbol)
        add_indicators(share)
        share.price_data.ohlcv.set_index(DATE, inplace=True)
        shares_data[symbol] = share
    logger.success('Loading Complete')
    return shares_data


def add_indicators(share):
    add_50_day_high(share)
    add_100_day_high(share)
    add_200_day_high(share)
    add_30_day_low(share)
    add_20_day_low(share)
    add_10_day_low(share)
