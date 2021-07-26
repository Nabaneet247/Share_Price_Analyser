import pandas as pd
from loguru import logger

from Services.local_data.file_locations import *


def read_csv_file(file_name, dtypes=None):
    file_name += '.csv'
    if dtypes is None:
        return pd.read_csv(file_name)
    else:
        return pd.read_csv(file_name, dtype=dtypes)


def get_indices_data(index_name):
    file_name = INDICES_FOLDER_PATH + index_name
    df = read_csv_file(file_name)
    return df


def get_share_ohlcv_data(symbol, interval, generate_index=True):
    file_name = OHLCV_DATA_FOLDER + '{}\\{}'.format(interval, symbol)
    try:
        data = read_csv_file(file_name)
        # if generate_index:
        #     data[OHLCV_INDEX] = data[DATE].apply(get_index_from_date)
        #     data.set_index(OHLCV_INDEX, inplace=True)
        return data.dropna()
    except FileNotFoundError:
        logger.error('OHLCV data file not found for {}', symbol)
