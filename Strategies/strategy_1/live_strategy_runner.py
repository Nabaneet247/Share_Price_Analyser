import json
import os

import openpyxl
from loguru import logger

from Services.local_data.file_locations import BACKTEST_DATA_FOLDER
from Strategies.strategy_1.entry_exit_checker import *
from Strategies.strategy_1.shares_data_provider import load_shares_data

DIRECTORY_PATH = BACKTEST_DATA_FOLDER + 'Strategy 1\\Live\\'


def get_low_type(value=30):
    return {30: LOW_30D}[value]


def get_high_type(value=100):
    return {100: HIGH_100D}[value]


def run_strategy_screener(existing_portfolio, cash_balance, date):
    shares_data = load_shares_data()
    shares = []
    for symbol in shares_data.keys():
        shares.append(shares_data[symbol])
    with open(DIRECTORY_PATH + 'Live Parameters.json') as json_data:
        param = json.load(json_data)
    trailing_sl_type = get_low_type(param['Trailing Stop Loss'])
    high_type = get_high_type(param['High Type'])
    max_positions = param['Max Positions']
    target_profit_percent = param['Target %']
    absolute_stop_loss_percent = param['Stop Loss %']
    available_positions = max_positions - len(existing_portfolio)

    file_name = DIRECTORY_PATH + 'Trading Suggestions.xlsx'
    trading_suggestions = pd.DataFrame()

    for share in shares:
        df = share.price_data.ohlcv
        try:
            x = df.loc[date, CLOSE]
        except KeyError:
            logger.info('Close not found for {}', share.symbol)
            continue

        close_price = round(df.loc[date, CLOSE], 2)
        if share.symbol in existing_portfolio.keys():
            entry_data = existing_portfolio[share.symbol]
            entry_price = entry_data[ENTRY_PRICE]
            absolute_stop_loss = entry_price * (100 - absolute_stop_loss_percent) / 100
            target_exit_price = entry_price * (100 + target_profit_percent) / 100
            trailing_stop_loss = df.loc[date, trailing_sl_type]

            if abs(1 - absolute_stop_loss / close_price) <= 0.03:
                logger.warning('Closing price({}) of {} is near the absolute stop loss of {}', close_price,
                               share.symbol, round(absolute_stop_loss, 2))
                data = pd.DataFrame(
                    {DATE: date, SYMBOL: share.symbol, 'Type': 'EXIT', CLOSE: close_price, 'Entry Price': entry_price,
                     'Exit Price': round(absolute_stop_loss, 2), 'Exit Type': 'Absolute Stop Loss'},
                    index=[0])
                trading_suggestions = trading_suggestions.append(data)

            if abs(1 - trailing_stop_loss / close_price) <= 0.03:
                logger.warning('Closing price({}) of {} is near the {} trailing stop loss of {}',
                               close_price, share.symbol,
                               trailing_sl_type, round(trailing_stop_loss, 2))
                data = pd.DataFrame(
                    {DATE: date, SYMBOL: share.symbol, 'Type': 'EXIT', CLOSE: close_price, 'Entry Price': entry_price,
                     'Exit Price': round(trailing_stop_loss, 2), 'Exit Type': 'Trailing Stop Loss'},
                    index=[0])
                trading_suggestions = trading_suggestions.append(data)

            if abs(1 - target_exit_price / close_price) <= 0.03:
                logger.success('Closing price of({}) {} is near the target exit price of {}', close_price,
                               share.symbol, round(target_exit_price, 2))
                data = pd.DataFrame(
                    {DATE: date, SYMBOL: share.symbol, 'Type': 'EXIT', CLOSE: close_price, 'Entry Price': entry_price,
                     'Exit Price': round(target_exit_price, 2), 'Exit Type': 'Target Reached'},
                    index=[0])
                trading_suggestions = trading_suggestions.append(data)

        elif available_positions > 0:
            high_price = df.loc[date, high_type]
            if abs(1 - high_price / close_price) <= 0.03:
                units_recommended = (cash_balance / available_positions) // high_price
                if units_recommended > 0:
                    logger.debug('Closing price of({}) {} is near the {} of {}. \nQuantity: {}, Purchase Amount: {}',
                                 close_price, share.symbol, high_type, round(high_price, 2),
                                 units_recommended, round(high_price * units_recommended, 2))
                    data = pd.DataFrame({DATE: date, SYMBOL: share.symbol, 'Type': 'ENTRY', CLOSE: close_price,
                                         'Entry Price': round(high_price, 2), 'Units': units_recommended,
                                         'Purchase Amount': round(high_price * units_recommended, 2)}, index=[0])
                    trading_suggestions = trading_suggestions.append(data)

    writer = pd.ExcelWriter(file_name, engine='openpyxl')

    if os.path.exists(file_name):
        book = openpyxl.load_workbook(file_name)
        if date in book.sheetnames:
            del book[date]
        writer.book = book

    trading_suggestions.to_excel(writer, sheet_name=date, index=False)

    writer.save()
    writer.close()


if __name__ == '__main__':
    # existing_portfolio = {'SBIN': {UNITS: 0,
    #                                 ENTRY_PRICE: 0}}

    existing_portfolio = {}
    cash_balance = 20000
    start_date = '20-08-2021'
    last_date = '20-08-2021'
    start_date_obj = pd.to_datetime(start_date, format=DEFAULT_DATE_FORMAT)
    last_date_obj = pd.to_datetime(last_date, format=DEFAULT_DATE_FORMAT)
    dates = list(
        map(lambda y: y.strftime(DEFAULT_DATE_FORMAT),
            pd.bdate_range(start=start_date_obj, end=last_date_obj, freq='B')))
    for date in dates:
        run_strategy_screener(existing_portfolio, cash_balance, date)
