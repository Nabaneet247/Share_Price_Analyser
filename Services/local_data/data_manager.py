import multiprocessing as mp

from loguru import logger

from Models.share import Share
from Services.local_data.data_reader import get_indices_data
from Services.local_data.data_reader import get_share_ohlcv_data
from Services.local_data.data_writer import save_daily_share_ohlcv_data
from Services.yahoo_finance.data_provider import fetch_historical_daily_price_data_for_a_share
from Utils.general_utils import print_running_duration

nifty500 = get_indices_data('NIFTY500')


@print_running_duration
@logger.catch
def generate_data_files_for_nifty500(max_processes=1):
    symbols = nifty500['Symbol'].tolist()
    with mp.Pool(processes=max_processes) as process:
        process.map(fetch_and_save_historical_daily_price_data_for_a_share, symbols)


def fetch_and_save_historical_daily_price_data_for_a_share(symbol):
    data = fetch_historical_daily_price_data_for_a_share(symbol)
    status = save_daily_share_ohlcv_data(symbol, data)
    if not status:
        logger.error('Couldn\'t save data for {}', symbol)


def get_share_object_for_symbol(symbol):
    name = nifty500[nifty500['Symbol'] == symbol]['Company Name']
    return Share(symbol, name, '1D', get_share_ohlcv_data(symbol, '1D'))


if __name__ == '__main__':
    # generate_data_files_for_nifty500(max_processes=3)
    fetch_and_save_historical_daily_price_data_for_a_share('BASF')
