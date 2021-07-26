import math
import multiprocessing as mp
from datetime import datetime
from glob import glob

import pandas as pd
from icecream import ic
from loguru import logger
from sklearn.model_selection import ParameterGrid

from Indicators.trend.high_low import *
from Services.local_data.data_manager import get_share_object_for_symbol
from Services.local_data.data_reader import get_indices_data
from Services.local_data.file_locations import BACKTEST_DATA_FOLDER

DIRECTORY_PATH = BACKTEST_DATA_FOLDER + 'Strategy 1\\'


def load_shares_data():
    shares_data = {}
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
    add_20_day_low(share)
    add_10_day_low(share)


def get_high_days_value(high_type):
    return {HIGH_50D: 50, HIGH_100D: 100, HIGH_200D: 200}[high_type]


@logger.catch
def back_test_strategy_for_a_stock(symbol, starting_capital, target_profit_percent, absolute_stop_loss_percent,
                                   trailing_sl_type, high_type, shares_data):
    report_data = pd.DataFrame()
    absolute_stop_loss = 0
    target_exit_price = 0
    # ic(shares_data)
    share = shares_data[symbol]
    balance = starting_capital
    net_profit = 0
    entered = False
    entry_price = 0
    units_purchased = 0
    df = share.price_data.ohlcv[get_high_days_value(high_type):]
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


def calculate_cagr(start_date, last_date, starting_capital, final_balance):
    start_date_obj = pd.to_datetime(start_date, format=DEFAULT_DATE_FORMAT)
    end_date_obj = pd.to_datetime(last_date, format=DEFAULT_DATE_FORMAT)
    years = round((end_date_obj - start_date_obj).days / 365, 3)
    cagr = round(math.pow(final_balance / starting_capital, 1 / years) - 1, 4) * 100
    return cagr, years


def entry_condition(df, index, high_type):
    if df.loc[index, CLOSE] >= df.loc[index, high_type]:
        return df.loc[index, CLOSE]
    return 0


def exit_condition(df, index, trailing_stop_loss, absolute_stop_loss, target_exit_price):
    if df.loc[index, OPEN] < trailing_stop_loss:
        return 1, df.loc[index, OPEN]
    if df.loc[index, CLOSE] < trailing_stop_loss:
        return 1, trailing_stop_loss

    if df.loc[index, OPEN] >= target_exit_price:
        return 2, df.loc[index, OPEN]
    if df.loc[index, CLOSE] >= target_exit_price:
        return 2, target_exit_price

    if df.loc[index, OPEN] <= absolute_stop_loss:
        return 3, df.loc[index, OPEN]
    if df.loc[index, CLOSE] <= absolute_stop_loss:
        return 3, absolute_stop_loss

    return 0, 0


def run_strategy_for_individual_stocks(starting_capital, target_profit_percent, absolute_stop_loss_percent,
                                       trailing_sl_type, high_type, shares_data):
    # logger.info('Generating individual report for {} - {} - {} - {}', starting_capital, target_profit_percent,
    #             absolute_stop_loss_percent, trailing_sl_type)
    symbols = get_indices_data('NIFTY200')['Symbol'].tolist()
    report_data = pd.DataFrame()
    for symbol in symbols:
        # logger.info('Testing for {}', y)
        report_data = report_data.append(
            back_test_strategy_for_a_stock(symbol, starting_capital, target_profit_percent, absolute_stop_loss_percent,
                                           trailing_sl_type, high_type, shares_data))
    report_data.reset_index(inplace=True)
    report_data.rename(columns={"index": "Symbol"}, inplace=True)
    return report_data


def generate_test_cases():
    param_grid = {'trailing_sl_type': [LOW_20D, LOW_10D],
                  'starting_capital': [1000, 10000, 25000, 50000],
                  'target_loss_params': [(60, 20), (30, 10), (45, 15), (40, 10), (20, 5), (80, 20),
                                         (100, 30), (50, 25), (40, 20), (40, 5), (90, 30)],
                  'high_type': [HIGH_50D, HIGH_100D, HIGH_200D]
                  }
    params_list = list(ParameterGrid(param_grid))
    df = pd.DataFrame(params_list)
    df.to_csv(DIRECTORY_PATH + 'tests.csv', index=False)


def run_strategy_for_multiple_stocks_in_parallel(max_processes=1):
    param_grid = {'trailing_sl_type': [LOW_20D, LOW_10D],
                  'starting_capital': [1000, 10000, 25000, 50000],
                  'target_loss_params': [(60, 20), (30, 10), (45, 15), (40, 10), (20, 5), (80, 20),
                                         (100, 30), (50, 25), (40, 20), (40, 5), (90, 30)],
                  'high_type': [HIGH_50D, HIGH_100D, HIGH_200D],
                  'shares_data': [load_shares_data()]
                  }
    # param_grid = {'trailing_sl_type': [LOW_20D],
    #               'starting_capital': [25000],
    #               'target_loss_params': [(60, 20)],
    #               'high_type': [HIGH_50D],
    #               'shares_data': [load_shares_data()]
    #               }
    params_list = list(ParameterGrid(param_grid))
    # run_strategy_for_multiple_stocks(params_list[0])
    with mp.Pool(processes=max_processes) as process:
        process.map(run_strategy_for_multiple_stocks, params_list)


def combine_stats():
    list_of_files = glob(DIRECTORY_PATH + 'BTest Report - *.xlsx')
    strategy_summary = pd.DataFrame()
    for name in list_of_files:
        strategy_summary = strategy_summary.append(pd.read_excel(name, sheet_name='Stats'))
    strategy_summary.to_excel(DIRECTORY_PATH + 'Strategy Stats Compilation.xlsx', index=False)
    logger.success('Combined Stats have been saved')


@logger.catch
def run_strategy_for_multiple_stocks(param):
    trailing_sl_type = param['trailing_sl_type']
    starting_capital = param['starting_capital']
    target_profit_percent = param['target_loss_params'][0]
    absolute_stop_loss_percent = param['target_loss_params'][1]
    high_type = param['high_type']
    shares_data = param['shares_data']

    individual_report_file_name = DIRECTORY_PATH + 'Individual Report - tp{} asl{} tsl{} hi{} sc{}.xlsx'.format(
        target_profit_percent, absolute_stop_loss_percent, trailing_sl_type[:2], get_high_days_value(high_type),
        starting_capital)

    try:
        individual_report = pd.read_excel(individual_report_file_name)
    except FileNotFoundError:
        individual_report = run_strategy_for_individual_stocks(starting_capital, target_profit_percent,
                                                               absolute_stop_loss_percent, trailing_sl_type,
                                                               high_type, shares_data)
        individual_report.to_excel(individual_report_file_name, index=False)
        logger.success('{} has been saved', individual_report_file_name)

    cases = [1, 2, 3, 4, 5, 6]
    for case in cases:
        if case == 1:
            symbols = get_indices_data('NIFTY50')['Symbol'].tolist()
            case_label = 'NIFTY 50'
        elif case == 2:
            symbols = get_indices_data('NIFTY100')['Symbol'].tolist()
            case_label = 'NIFTY 100'
        elif case == 3:
            symbols = get_indices_data('NIFTY200')['Symbol'].tolist()
            case_label = 'NIFTY 200'
        elif case == 4:
            df = individual_report[individual_report['W/L Ratio'] >= 0.8]
            symbols = df['Symbol'].tolist()
            case_label = 'W/L(0.8) Filter'
        elif case == 5:
            df = individual_report[individual_report['CAGR'] >= 10]
            symbols = df['Symbol'].tolist()
            case_label = 'CAGR(10) Filter'
        else:
            df = individual_report[individual_report['W/L Ratio'] >= 0.8]
            df = df[df['CAGR'] >= 10]
            symbols = df['Symbol'].tolist()
            case_label = 'W/L(0.8) and CAGR(10) Filter'
        if len(symbols) == 0:
            continue

        positions = [5, 10, 20]
        for max_positions in positions:
            report_number = 'tp{} asl{} tsl{} hi{} sc{} p{} c{}'.format(target_profit_percent,
                                                                        absolute_stop_loss_percent,
                                                                        trailing_sl_type[:2],
                                                                        get_high_days_value(high_type),
                                                                        starting_capital, max_positions, case)
            report_file_name = DIRECTORY_PATH + 'BTest Report - {}.xlsx'.format(report_number)
            try:
                x = pd.read_excel(report_file_name)
                continue
            except FileNotFoundError:
                pass

            # ic(target_profit_percent, absolute_stop_loss_percent, starting_capital, max_positions, trailing_sl_type,
            #    high_type)
            start_time = datetime.now()
            try:
                trade_log, daily_log, stats_log = back_test_for_multiple_shares(symbols, target_profit_percent,
                                                                                absolute_stop_loss_percent,
                                                                                starting_capital, max_positions,
                                                                                trailing_sl_type, high_type,
                                                                                shares_data)
                duration = datetime.now() - start_time
                stats_log.loc[0, 'Time Taken'] = '{}:{}'.format(round(duration.total_seconds() // 60, 0),
                                                                round(duration.total_seconds() % 60, 0))

                stats_log.loc[0, 'Case Type'] = case_label
                stats_log.loc[0, 'Report Number'] = report_number
                with pd.ExcelWriter(report_file_name) as writer:
                    trade_log.to_excel(writer, sheet_name="Trade Logs", index=False)
                    daily_log.to_excel(writer, sheet_name="Daily Logs", index=False)
                    stats_log.to_excel(writer, sheet_name="Stats", index=False)
                    symbols_df = pd.DataFrame(symbols, columns=['Symbols'])
                    symbols_df.to_excel(writer, sheet_name="Symbols", index=False)
                    individual_report.to_excel(writer, sheet_name="Individual Test Report", index=False)
                    logger.success('{} has been saved', report_file_name)
            except Exception as e:
                logger.error('Exception: {} - {}', type(e), e)
                ic(target_profit_percent, absolute_stop_loss_percent, starting_capital, max_positions, trailing_sl_type,
                   high_type)


@logger.catch
def back_test_for_multiple_shares(symbols, target_profit_percent, absolute_stop_loss_percent, starting_capital,
                                  max_positions, trailing_sl_type, high_type, shares_data):
    trade_log = pd.DataFrame()
    daily_log = pd.DataFrame()
    shares = []
    for symbol in symbols:
        shares.append(shares_data[symbol])

    for share in shares:
        share.price_data.ohlcv = share.price_data.ohlcv.iloc[get_high_days_value(high_type):]

    start_date = '01-01-1996'
    last_date = '30-06-2021'
    start_date_obj = pd.to_datetime(start_date, format=DEFAULT_DATE_FORMAT)
    last_date_obj = pd.to_datetime(last_date, format=DEFAULT_DATE_FORMAT)
    dates = list(
        map(lambda y: y.strftime(DEFAULT_DATE_FORMAT),
            pd.bdate_range(start=start_date_obj, end=last_date_obj, freq='B')))
    portfolio = {}
    balance = starting_capital
    trades_entered = 0
    trades_exited = 0
    trailing_sl_exits = 0
    abs_sl_exits = 0
    target_exits = 0
    win = 0
    loss = 0
    total_profit = 0
    total_loss = 0
    avg_profit_percent = 0
    avg_loss_percent = 0
    portfolio_value_today = balance
    for date in dates:
        # if date == '08-11-2005':
        #     print(1)
        avl_positions = max_positions - len(portfolio)
        # logger.info('Testing for {}', date)
        possible_entries = {}
        positions_exited_today = 0
        positions_entered_today = 0
        balance_cleared = 0
        portfolio_value_today = 0
        cash_balance_today = balance
        for share in shares:
            df = share.price_data.ohlcv
            try:
                x = df.loc[date, CLOSE]
            except KeyError:
                continue

            if share.symbol in portfolio.keys():
                entry_data = portfolio[share.symbol]
                trailing_stop_loss = df.loc[date, trailing_sl_type]
                exit_reason, price = exit_condition(df, date, trailing_stop_loss, entry_data[ABS_STOP_LOSS],
                                                    entry_data[TARGET_EXIT_PRICE])
                portfolio_value_today += df.loc[date, CLOSE] * entry_data[UNITS]
                if exit_reason > 0:
                    exit_price = price
                    profit = round((exit_price - entry_data[ENTRY_PRICE]) * entry_data[UNITS], 2)
                    profit_percent = round((exit_price / entry_data[ENTRY_PRICE]) - 1, 4) * 100
                    if profit > 0:
                        win += 1
                        total_profit += profit
                        avg_profit_percent += profit_percent
                    else:
                        loss += 1
                        total_loss += profit
                        avg_loss_percent += profit_percent

                    balance_cleared += entry_data[UNITS] * exit_price
                    if exit_reason == 1:
                        trailing_sl_exits += 1
                    elif exit_reason == 2:
                        abs_sl_exits += 1
                    elif exit_reason == 3:
                        target_exits += 1
                    exit_reason = {1: 'Tr SL', 2: 'Abs SL', 3: 'Target'}[exit_reason]
                    trade_log = trade_log.append(
                        {DATE: date, SYMBOL: share.symbol, TYPE: 'EXIT', UNITS: entry_data[UNITS],
                         ENTRY_PRICE: round(entry_data[ENTRY_PRICE], 2), EXIT_PRICE: round(exit_price, 2),
                         PROFIT: profit, PROFIT_PERCENT: profit_percent, EXIT_REASON: exit_reason}, ignore_index=True)
                    del portfolio[share.symbol]
                    positions_exited_today += 1
                    trades_exited += 1

            elif avl_positions > 0:
                price = entry_condition(df, date, high_type)
                if price > 0:
                    entry_price = price
                    units_purchased = (balance / avl_positions) // entry_price
                    absolute_stop_loss = entry_price * (100 - absolute_stop_loss_percent) / 100
                    target_exit_price = entry_price * (100 + target_profit_percent) / 100
                    possible_entries[share.symbol] = {UNITS: units_purchased,
                                                      ABS_STOP_LOSS: absolute_stop_loss,
                                                      TARGET_EXIT_PRICE: target_exit_price, ENTRY_PRICE: entry_price,
                                                      PURCHASE_AMOUNT: entry_price * units_purchased}

        if len(possible_entries.keys()) > 0:
            if len(possible_entries.keys()) > avl_positions:
                possible_entries = remove_excess_shares_from_possible_entries(possible_entries, avl_positions)

            for key in possible_entries.keys():
                data = possible_entries[key]
                portfolio[key] = data
                balance -= data[UNITS] * data[ENTRY_PRICE]
                if balance < 0:
                    raise Exception
                positions_entered_today += 1
                trades_entered += 1
                trade_log = trade_log.append(
                    {DATE: date, SYMBOL: key, TYPE: 'ENTRY', UNITS: data[UNITS],
                     ENTRY_PRICE: round(data[ENTRY_PRICE], 2)}, ignore_index=True)

        balance += balance_cleared
        if portfolio_value_today > 0:
            daily_log.loc[date, 'Cash Balance'] = cash_balance_today
            daily_log.loc[date, 'Portfolio Value'] = portfolio_value_today
            daily_log.loc[date, 'Net Value'] = cash_balance_today + portfolio_value_today
            daily_log.loc[date, 'Positions Entered'] = positions_entered_today
            daily_log.loc[date, 'Positions Exited'] = positions_exited_today
    daily_log.reset_index(inplace=True)
    daily_log.rename(columns={"index": "Date"}, inplace=True)

    avg_profit_percent = round(avg_profit_percent / win, 2)
    avg_loss_percent = round(avg_loss_percent / loss, 2)

    trailing_sl_exits = round(trailing_sl_exits / trades_exited * 100, 2)
    abs_sl_exits = round(abs_sl_exits / trades_exited * 100, 2)
    target_exits = round(target_exits / trades_exited * 100, 2)

    cagr, years = calculate_cagr(start_date, last_date, starting_capital, portfolio_value_today)
    stats_log = pd.DataFrame(
        {'Timestamp': datetime.now(), 'Total Trades': trades_entered + trades_exited,
         'Trades Entered': trades_entered, 'Trades Exited': trades_exited,
         'Wins': win, 'Losses': loss, 'W/L Ratio': round(win / loss, 2),
         'CAGR': cagr, 'Net Profit': total_profit + total_loss, 'Back Test Duration': years,
         'Trailing SL Exits %': trailing_sl_exits, 'Absolute SL Exits %': abs_sl_exits,
         'Target Met Exit %': target_exits, 'Trades per year': round((win + loss) / years, 2),
         'Start Date': start_date, 'End Date': last_date,
         'Total Profit': total_profit, 'Avg Profit %': avg_profit_percent,
         'Total Loss': total_loss, 'Avg Loss %': avg_loss_percent,
         'Initial Capital': starting_capital, 'Max Positions': max_positions,
         'Target %': target_profit_percent, 'Stop Loss %': absolute_stop_loss_percent,
         'Trailing Stop Loss': trailing_sl_type, 'High Type': high_type,
         'Maximum Portfolio Value': round(daily_log['Net Value'].max(), 2),
         'Minimum Portfolio Value': round(daily_log['Net Value'].min(), 2),
         'Stocks considered': len(shares)}, index=[0])
    return trade_log, daily_log, stats_log


# maximises purchase amount from possible entries
def remove_excess_shares_from_possible_entries(possible_entries, avl_positions):
    purchase_amount_map = [(x, possible_entries[x][PURCHASE_AMOUNT]) for x in list(possible_entries.keys())]
    purchase_amount_map = sorted(purchase_amount_map, key=lambda x: x[1], reverse=True)
    keys_to_be_removed = [x[0] for x in purchase_amount_map[avl_positions:]]
    for key in list(possible_entries.keys()):
        if key in keys_to_be_removed:
            del possible_entries[key]
    return possible_entries


if __name__ == '__main__':
    run_strategy_for_multiple_stocks_in_parallel(max_processes=2)
    # combine_stats()
