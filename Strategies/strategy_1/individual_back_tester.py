import pandas as pd

from Constants.constants import *
from Services.local_data.data_reader import get_indices_data
from Strategies.strategy_1.entry_exit_checker import entry_condition, exit_condition
from Strategies.utils import calculate_cagr


def run_strategy_for_stocks_independently(target_profit_percent, absolute_stop_loss_percent,
                                          trailing_sl_type, high_type, shares_data):
    symbols = get_indices_data('NIFTY200')['Symbol'].tolist()
    report_data = pd.DataFrame()
    for symbol in symbols:
        # logger.info('Testing for {}', y)
        report_data = report_data.append(
            back_test_strategy_for_single_stock(symbol, target_profit_percent, absolute_stop_loss_percent,
                                                trailing_sl_type, high_type, shares_data))
    report_data.reset_index(inplace=True)
    report_data.rename(columns={"index": "Symbol"}, inplace=True)
    return report_data


def back_test_strategy_for_single_stock(symbol, target_profit_percent, absolute_stop_loss_percent,
                                        trailing_sl_type, high_type, shares_data):
    report_data = pd.DataFrame()
    absolute_stop_loss = 0
    target_exit_price = 0
    # ic(shares_data)
    share = shares_data[symbol]
    starting_capital = 100000
    balance = starting_capital
    net_profit = 0
    entered = False
    entry_price = 0
    units_purchased = 0
    df = share.price_data.ohlcv
    wins = 0
    losses = 0
    if len(df.index.values) == 0:
        return report_data
    for index in df.index.values:
        if entered:
            trailing_stop_loss = df.loc[index][trailing_sl_type]
            exit_reason, price = exit_condition(df, index, trailing_stop_loss, absolute_stop_loss, target_exit_price)
            if exit_reason > 0:
                entered = False
                exit_price = price
                profit = (exit_price - entry_price) * units_purchased
                if profit > 0:
                    wins += 1
                else:
                    losses += 1
                net_profit += profit
                balance += units_purchased * exit_price
                units_purchased = 0
            else:
                pass
        else:
            price = entry_condition(df, index, high_type)
            if price > 0:
                entered = True
                entry_price = price
                units_purchased = balance // entry_price
                balance -= units_purchased * entry_price
                absolute_stop_loss = entry_price * (100 - absolute_stop_loss_percent) / 100
                target_exit_price = entry_price * (100 + target_profit_percent) / 100

    final_balance = balance + units_purchased * df.iloc[-1][CLOSE]
    start_date = df.index.values[0]
    last_date = df.index.values[-1]
    cagr, years = calculate_cagr(start_date, last_date, starting_capital, final_balance)
    win_loss_ratio = round(wins / losses, 2) if losses > 0 else 10000
    report_data.loc[symbol, 'CAGR'] = cagr
    report_data.loc[symbol, 'W/L Ratio'] = win_loss_ratio
    report_data.loc[symbol, 'Trades'] = wins + losses
    report_data.loc[symbol, 'Back Test Duration (in years)'] = years
    report_data.loc[symbol, 'Trades per year'] = round((wins + losses) / years, 2)
    return report_data
