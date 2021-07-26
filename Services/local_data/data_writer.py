import pandas as pd
from loguru import logger

from Constants.constants import *
from Services.local_data.data_reader import get_share_ohlcv_data
from Services.local_data.file_locations import *


def save_daily_share_ohlcv_data(symbol, data):
    return save_share_ohlcv_data(symbol=symbol, interval='1D', data=data)


def save_share_ohlcv_data(symbol, interval, data):
    file_name = OHLCV_DATA_FOLDER + '{}\\{}'.format(interval, symbol)
    existing_data = get_share_ohlcv_data(symbol, interval)
    if existing_data is not None:
        # omitted_dates = find_difference_between_two_lists(existing_data[DATE].tolist(), data[DATE].tolist())
        # if len(omitted_dates) > 0:
        #     logger.error('New data file has {} dates omitted - {}', len(omitted_dates), omitted_dates)
        #     return False
        data = data.append(existing_data)
        data.sort_values(by=[DATE], inplace=True, key=lambda x: pd.to_datetime(x, format='%d-%m-%Y'))
        data.drop_duplicates(subset=[DATE], inplace=True)
    save_data_as_csv(file_name, data)
    return True


def save_data_as_csv(file_name, data):
    file_name += '.csv'
    data.to_csv(file_name, index=False)
    logger.success('Data has been saved at {}', file_name)


def save_data_as_excel(file_name, data):
    file_name += '.xlsx'
    data.to_excel(file_name, index=False)
    logger.success('Data has been saved at {}', file_name)
