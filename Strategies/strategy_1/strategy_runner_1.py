import multiprocessing as mp
from datetime import datetime
from glob import glob

import pandas as pd
from icecream import ic
from loguru import logger
from sklearn.model_selection import ParameterGrid

from Indicators.trend.high_low import *
from Services.local_data.data_reader import get_indices_data
from Services.local_data.file_locations import BACKTEST_DATA_FOLDER
from Strategies.strategy_1.group_back_tester import back_test_for_multiple_shares
from Strategies.strategy_1.individual_back_tester import run_strategy_for_stocks_independently
from Strategies.strategy_1.shares_data_provider import load_shares_data

DIRECTORY_PATH = BACKTEST_DATA_FOLDER + 'Strategy 1\\Round 1\\'
ALL_TEST_CASES_FILE_PATH = DIRECTORY_PATH + 'All Test Cases.csv'


def get_high_days_value(high_type):
    return {HIGH_50D: 50, HIGH_100D: 100, HIGH_200D: 200}[high_type]


def get_low_days_value(low_type):
    return {LOW_30D: 30, LOW_20D: 20, LOW_10D: 10}[low_type]


def generate_test_cases():
    logger.info('Generating Test Cases')
    param_grid = {'high_type': [HIGH_50D, HIGH_100D, HIGH_200D], 'trailing_sl_type': [LOW_30D, LOW_20D, LOW_10D],
                  'starting_capital': [10000],
                  'target_loss_params': [(60, 20), (30, 10), (45, 15), (40, 10), (20, 5), (80, 20),
                                         (100, 30), (50, 25), (40, 20), (40, 5), (90, 30)],
                  'max_positions': [5, 10, 20],
                  'case': [1, 2, 3, 4, 5, 6]
                  }
    params_list = list(ParameterGrid(param_grid))
    df = pd.DataFrame()
    for param in params_list:
        trailing_sl_type = param['trailing_sl_type']
        starting_capital = param['starting_capital']
        target_profit_percent = param['target_loss_params'][0]
        absolute_stop_loss_percent = param['target_loss_params'][1]
        high_type = param['high_type']
        max_positions = param['max_positions']
        case = param['case']
        data_row = pd.DataFrame({
            'Starting Capital': starting_capital, 'Max Positions': max_positions,
            'Target %': target_profit_percent, 'Stop Loss %': absolute_stop_loss_percent,
            'Trailing Stop Loss': trailing_sl_type, 'High Type': high_type, 'Case Type': case,
            'Report Id': generate_report_id(absolute_stop_loss_percent=absolute_stop_loss_percent,
                                            target_profit_percent=target_profit_percent,
                                            trailing_sl_type=trailing_sl_type, starting_capital=starting_capital,
                                            high_type=high_type, max_positions=max_positions, case=case),
            'Status': 'N'
        }, index=[len(df.index)])
        df = df.append(data_row)
    df.to_csv(ALL_TEST_CASES_FILE_PATH, index=False)
    logger.success('{} has been saved', ALL_TEST_CASES_FILE_PATH)
    logger.info('There are {} test cases', len(df.index))
    return df


def run_strategy_for_multiple_stocks_in_parallel(max_processes=1):
    try:
        test_cases = pd.read_csv(ALL_TEST_CASES_FILE_PATH)
        test_cases['Status'] = test_cases['Status'].replace('I', 'N')
        test_cases.to_csv(ALL_TEST_CASES_FILE_PATH, index=False)
    except FileNotFoundError:
        test_cases = generate_test_cases()

    test_case_indexes = test_cases.index.to_list()
    _lock = mp.Lock()
    _shares_data = load_shares_data()
    with mp.Pool(processes=max_processes, initializer=init_child, initargs=(_lock, _shares_data,)) as process:
        process.map(run_strategy_for_multiple_stocks, test_case_indexes)


def init_child(_lock, _shares_data):
    global lock
    lock = _lock
    global global_shares_data
    global_shares_data = _shares_data


def combine_stats():
    list_of_files = glob(DIRECTORY_PATH + 'Back Test Reports/*.xlsx')
    strategy_summary = pd.DataFrame()
    total = len(list_of_files)
    counter = 1
    for name in list_of_files:
        strategy_summary = strategy_summary.append(pd.read_excel(name, sheet_name='Stats'))
        ic(counter, total)
        counter += 1
    strategy_summary.sort_values(by=['CAGR'], ascending=False, inplace=True)
    strategy_summary.to_excel(DIRECTORY_PATH + 'Strategy Stats Compilation.xlsx', index=False)
    logger.success('Combined Stats have been saved')


@logger.catch
def run_strategy_for_multiple_stocks(index):
    ic(index)
    with lock:
        test_cases = pd.read_csv(ALL_TEST_CASES_FILE_PATH)
        if test_cases.loc[index, 'Status'] == 'N':
            test_cases.loc[index, 'Status'] = 'I'
            test_cases.to_csv(ALL_TEST_CASES_FILE_PATH, index=False)
            param = test_cases.loc[index]
        else:
            return
    trailing_sl_type = param['Trailing Stop Loss']
    starting_capital = param['Starting Capital']
    target_profit_percent = param['Target %']
    absolute_stop_loss_percent = param['Stop Loss %']
    high_type = param['High Type']
    shares_data = global_shares_data
    max_positions = param['Max Positions']
    case = param['Case Type']

    individual_report_id = 'tp{} asl{} tsl{} hi{}'.format(
        target_profit_percent, absolute_stop_loss_percent, get_low_days_value(trailing_sl_type),
        get_high_days_value(high_type))
    individual_report_file_name = DIRECTORY_PATH + 'Individual Reports/{}.xlsx'.format(individual_report_id)

    try:
        individual_report = pd.read_excel(individual_report_file_name)
    except FileNotFoundError:
        ic(individual_report_id)
        individual_report = run_strategy_for_stocks_independently(target_profit_percent, absolute_stop_loss_percent,
                                                                  trailing_sl_type, high_type, shares_data)
        individual_report.to_excel(individual_report_file_name, index=False)
        logger.success('{} has been saved', individual_report_file_name)

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
        logger.error('Symbols list was empty')
        return

    back_test_report_id = param['Report Id']
    report_file_name = DIRECTORY_PATH + 'Back Test Reports/{}.xlsx'.format(back_test_report_id)

    start_time = datetime.now()
    try:
        ic(back_test_report_id)
        trade_log, daily_log, stats_log = back_test_for_multiple_shares(symbols, target_profit_percent,
                                                                        absolute_stop_loss_percent,
                                                                        starting_capital, max_positions,
                                                                        trailing_sl_type, high_type,
                                                                        shares_data)
        duration = datetime.now() - start_time
        stats_log.loc[0, 'Time Taken'] = '{}:{}'.format(int(duration.total_seconds() // 60),
                                                        int(duration.total_seconds() % 60))

        stats_log.loc[0, 'Case Type'] = case_label
        stats_log.loc[0, 'Report Number'] = back_test_report_id
        with pd.ExcelWriter(report_file_name) as writer:
            trade_log.to_excel(writer, sheet_name="Trade Logs", index=False)
            daily_log.to_excel(writer, sheet_name="Daily Logs", index=False)
            stats_log.to_excel(writer, sheet_name="Stats", index=False)
            symbols_df = pd.DataFrame(symbols, columns=['Symbols'])
            symbols_df.to_excel(writer, sheet_name="Symbols", index=False)
            individual_report.to_excel(writer, sheet_name="Individual Test Report", index=False)
            logger.success('{} has been saved', report_file_name)
        with lock:
            test_cases = pd.read_csv(ALL_TEST_CASES_FILE_PATH)
            test_cases.loc[index, 'Status'] = 'Y'
            test_cases.loc[index, 'Timestamp'] = datetime.now()
            test_cases.to_csv(ALL_TEST_CASES_FILE_PATH, index=False)
    except Exception as e:
        logger.error('Exception: {} - {}', type(e), e)
        with lock:
            test_cases = pd.read_csv(ALL_TEST_CASES_FILE_PATH)
            test_cases.loc[index, 'Status'] = 'E'
            test_cases.loc[index, 'Timestamp'] = datetime.now()
            test_cases.to_csv(ALL_TEST_CASES_FILE_PATH, index=False)


def generate_report_id(absolute_stop_loss_percent, case, high_type, max_positions, starting_capital,
                       target_profit_percent, trailing_sl_type):
    report_number = 'tp{} asl{} tsl{} hi{} sc{} p{} c{}'.format(target_profit_percent,
                                                                absolute_stop_loss_percent,
                                                                get_low_days_value(trailing_sl_type),
                                                                get_high_days_value(high_type),
                                                                starting_capital, max_positions, case)
    return report_number


def debug_a_case():
    # tp40 asl10 tsl10 hi50 sc1000 p5 c1
    shares_data = load_shares_data()
    case = 1

    individual_report_id = 'tp40 asl10 tsl10 hi50'
    individual_report_file_name = DIRECTORY_PATH + 'Individual Reports/{}.xlsx'.format(individual_report_id)
    individual_report = pd.read_excel(individual_report_file_name)

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

    trade_log, daily_log, stats_log = back_test_for_multiple_shares(symbols=symbols, target_profit_percent=40,
                                                                    absolute_stop_loss_percent=10,
                                                                    starting_capital=1000, max_positions=5,
                                                                    trailing_sl_type=LOW_10D, high_type=HIGH_50D,
                                                                    shares_data=shares_data)
    print('Debug done')


if __name__ == '__main__':
    run_strategy_for_multiple_stocks_in_parallel(max_processes=2)
    combine_stats()
    # debug_a_case()
