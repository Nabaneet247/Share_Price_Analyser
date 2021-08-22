from datetime import datetime

import pandas as pd
from icecream import ic

from Constants.constants import *
from Strategies.strategy_1.entry_exit_checker import entry_condition, exit_condition
from Strategies.utils import calculate_cagr


def back_test_for_multiple_shares(symbols, target_profit_percent, absolute_stop_loss_percent, starting_capital,
                                  max_positions, trailing_sl_type, high_type, shares_data, start_date='01-01-1996',
                                  last_date='23-07-2021'):
    # ic(len(symbols), target_profit_percent, absolute_stop_loss_percent, starting_capital,
    #    max_positions, trailing_sl_type, high_type, len(shares_data.keys()), sys.getsizeof(shares_data))
    trade_log = pd.DataFrame()
    daily_log = pd.DataFrame()
    shares = []
    for symbol in symbols:
        shares.append(shares_data[symbol])

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
    portfolio_value_today = 0
    trading_start_date = dates[0]
    for date in dates:
        avl_positions = max_positions - len(portfolio)
        possible_entries = {}
        positions_exited_today = 0
        positions_entered_today = 0
        balance_cleared = 0
        portfolio_value_today = 0
        # cash_balance_today = balance
        for share in shares:
            df = share.price_data.ohlcv
            try:
                x = df.loc[date, CLOSE]
            except KeyError:
                if share.symbol in portfolio.keys():
                    entry_data = portfolio[share.symbol]
                    portfolio_value_today += entry_data[LTP] * entry_data[UNITS]
                continue

            if share.symbol in portfolio.keys():
                entry_data = portfolio[share.symbol]
                trailing_stop_loss = df.loc[date, trailing_sl_type]
                exit_reason, price = exit_condition(df, date, trailing_stop_loss, entry_data[ABS_STOP_LOSS],
                                                    entry_data[TARGET_EXIT_PRICE])
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
                elif exit_reason == 0:
                    portfolio[share.symbol][LTP] = df.loc[date, CLOSE]
                    portfolio_value_today += df.loc[date, CLOSE] * entry_data[UNITS]

            elif avl_positions > 0:
                price = entry_condition(df, date, high_type)
                if price > 0:
                    entry_price = price
                    units_purchased = (balance / avl_positions) // entry_price
                    if units_purchased > 0:
                        absolute_stop_loss = entry_price * (100 - absolute_stop_loss_percent) / 100
                        target_exit_price = entry_price * (100 + target_profit_percent) / 100
                        possible_entries[share.symbol] = {UNITS: units_purchased,
                                                          ABS_STOP_LOSS: absolute_stop_loss,
                                                          TARGET_EXIT_PRICE: target_exit_price,
                                                          ENTRY_PRICE: entry_price,
                                                          PURCHASE_AMOUNT: entry_price * units_purchased,
                                                          LTP: entry_price}

        if len(possible_entries.keys()) > 0:
            if len(possible_entries.keys()) > avl_positions:
                possible_entries = remove_excess_shares_from_possible_entries(possible_entries, avl_positions)

            for key in possible_entries.keys():
                new_entry_data = possible_entries[key]
                portfolio[key] = new_entry_data
                balance -= new_entry_data[PURCHASE_AMOUNT]
                if balance < 0:
                    raise Exception
                portfolio_value_today += new_entry_data[PURCHASE_AMOUNT]
                positions_entered_today += 1
                trades_entered += 1
                if trades_entered == 1:
                    trading_start_date = date
                trade_log = trade_log.append(
                    {DATE: date, SYMBOL: key, TYPE: 'ENTRY', UNITS: new_entry_data[UNITS],
                     ENTRY_PRICE: round(new_entry_data[ENTRY_PRICE], 2)}, ignore_index=True)

        balance += balance_cleared
        daily_log.loc[date, 'Cash Balance'] = balance
        daily_log.loc[date, 'Portfolio Value'] = portfolio_value_today
        daily_log.loc[date, 'Net Value'] = balance + portfolio_value_today
        daily_log.loc[date, 'Positions Entered'] = positions_entered_today
        daily_log.loc[date, 'Positions Exited'] = positions_exited_today

    avg_profit_percent = round(avg_profit_percent / win, 2) if win > 0 else 0
    avg_loss_percent = round(avg_loss_percent / loss, 2) if loss > 0 else 0

    trailing_sl_exits = round(trailing_sl_exits / trades_exited * 100, 2) if trades_exited > 0 else 0
    abs_sl_exits = round(abs_sl_exits / trades_exited * 100, 2) if trades_exited > 0 else 0
    target_exits = round(target_exits / trades_exited * 100, 2) if trades_exited > 0 else 0

    cagr, years = calculate_cagr(start_date, last_date, starting_capital, daily_log.loc[last_date, 'Net Value'])
    ic(trading_start_date, cagr)
    daily_log.reset_index(inplace=True)
    daily_log.rename(columns={"index": "Date"}, inplace=True)
    if loss > 0:
        win_loss_ratio = round(win / loss, 2)
    else:
        win_loss_ratio = round(win * 100, 2)
    stats_log = pd.DataFrame(
        {'Timestamp': datetime.now(), 'Total Trades': trades_entered + trades_exited,
         'Trades Entered': trades_entered, 'Trades Exited': trades_exited,
         'Wins': win, 'Losses': loss, 'W/L Ratio': win_loss_ratio,
         'CAGR': cagr, 'Net Profit': total_profit + total_loss, 'Back Test Duration': years,
         'Trailing SL Exits %': trailing_sl_exits, 'Absolute SL Exits %': abs_sl_exits,
         'Target Met Exit %': target_exits, 'Trades per year': round((win + loss) / years, 2),
         'Trading Start Date': trading_start_date, 'Trading Last Date': last_date,
         'Total Profit': total_profit, 'Avg Profit %': avg_profit_percent,
         'Total Loss': total_loss, 'Avg Loss %': avg_loss_percent,
         'Starting Capital': starting_capital, 'Max Positions': max_positions,
         'Target %': target_profit_percent, 'Stop Loss %': absolute_stop_loss_percent,
         'Trailing Stop Loss': trailing_sl_type, 'High Type': high_type,
         'Investment Start Date': start_date,
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
