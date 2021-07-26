import yfinance as yf

from Constants.constants import *
from Utils.datetime_utils import convert_date_format


def fetch_daily_price_data_for_a_share(symbol, start_date, end_date):
    df = yf.download(tickers=symbol + YAHOO_NSE_POSTFIX, start=get_yahoo_date_from_default_date(start_date),
                     end=get_yahoo_date_from_default_date(end_date))
    return format_dates(df)


def format_dates(data):
    data.reset_index(inplace=True)
    data[DATE] = data[DATE].apply(get_default_date_from_yahoo_date)
    return data


# todo don't use this when market is open
def fetch_historical_daily_price_data_for_a_share(symbol):
    df = yf.download(tickers=symbol + YAHOO_NSE_POSTFIX, period='max')
    df.dropna(inplace=True)
    return format_dates(df)


def get_yahoo_date_from_default_date(date):
    return convert_date_format(date, DEFAULT_DATE_FORMAT, YAHOO_DATE_FORMAT)


def get_default_date_from_yahoo_date(date):
    return date.strftime(DEFAULT_DATE_FORMAT)


if __name__ == '__main__':
    print(yf.download(tickers='STLTECH' + YAHOO_NSE_POSTFIX, period='max'))
