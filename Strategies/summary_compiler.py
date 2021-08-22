from glob import glob

import pandas as pd
import plotly.express as px
from icecream import ic
from loguru import logger

from Services.local_data.file_locations import BACKTEST_DATA_FOLDER


def get_directory_path(strategy_number, round_number):
    return BACKTEST_DATA_FOLDER + 'Strategy {}\\Round {}\\'.format(strategy_number, round_number)


def read_stats(strategy_number, round_number, re_combine=False):
    if re_combine:
        return combine_stats(strategy_number, round_number)
    try:
        directory_path = get_directory_path(strategy_number, round_number)
        return pd.read_excel(directory_path + 'Strategy Stats Compilation.xlsx')
    except FileNotFoundError:
        return combine_stats(strategy_number, round_number)


def combine_stats(strategy_number, round_number):
    directory_path = get_directory_path(strategy_number, round_number)
    list_of_files = glob(directory_path + 'Back Test Reports/*.xlsx')
    strategy_summary = pd.DataFrame()
    total = len(list_of_files)
    counter = 1
    for name in list_of_files:
        strategy_summary = strategy_summary.append(pd.read_excel(name, sheet_name='Stats'))
        ic(counter, total)
        counter += 1
    strategy_summary.sort_values(by=['CAGR'], ascending=False, inplace=True)
    strategy_summary.to_excel(directory_path + 'Strategy Stats Compilation.xlsx', index=False)
    logger.success('Combined Stats have been saved')
    return strategy_summary


def plot_stats(data, strategy_number, round_number):
    directory_path = get_directory_path(strategy_number, round_number)
    data['Target-SL'] = data["Target %"].astype(str) + '-' + data["Stop Loss %"].astype(str)

    '''
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
    '''

    # data = data[data['Case Type'] == 'NIFTY 200']
    grouper_columns = ['CAGR', 'W/L Ratio', 'Target Met Exit %', 'Trades per year']
    for grouper_column in grouper_columns:
        marginal = 'box'
        bar_mode = 'group'
        opacity = 0.9
        fig1 = px.histogram(data, x=grouper_column, color="Trailing Stop Loss", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Trailing Stop Loss)'.format(strategy_number,
                                                                                                      grouper_column))
        fig1.update_layout(barmode=bar_mode)
        fig1.update_traces(opacity=opacity)

        fig2 = px.histogram(data, x=grouper_column, color="High Type", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by High Type)'.format(strategy_number,
                                                                                             grouper_column))
        fig2.update_layout(barmode=bar_mode)
        fig2.update_traces(opacity=opacity)

        fig3 = px.histogram(data, x=grouper_column, color="Target-SL", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Target % and Abs SL)'.format(strategy_number,
                                                                                                       grouper_column))
        fig3.update_layout(barmode=bar_mode)
        fig3.update_traces(opacity=opacity)

        fig4 = px.histogram(data, x=grouper_column, color="Max Positions", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Max Positions)'.format(strategy_number,
                                                                                                 grouper_column))
        fig4.update_layout(barmode=bar_mode)
        fig4.update_traces(opacity=opacity)

        # fig5 = px.histogram(data, x=grouper_column, color="Case Type", marginal=marginal,
        #                     title='Strategy {} - {} Histogram (Grouped by Case Type)'.format(strategy_number,
        #                                                                                      grouper_column))
        # fig5.update_layout(barmode=bar_mode)
        # fig5.update_traces(opacity=opacity)

        fig6 = px.histogram(data, x=grouper_column, color="Stop Loss %", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Stop Loss %)'.format(strategy_number,
                                                                                               grouper_column))
        fig6.update_layout(barmode=bar_mode)
        fig6.update_traces(opacity=opacity)

        fig7 = px.histogram(data, x=grouper_column, color="Back Test Duration", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Back Test Duration)'.format(strategy_number,
                                                                                                      grouper_column))
        fig7.update_layout(barmode=bar_mode)
        fig7.update_traces(opacity=opacity)

        fig8 = px.histogram(data, x=grouper_column, color="Investment Start Date", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Investment Start Date)'.format(
                                strategy_number,
                                grouper_column))
        fig8.update_layout(barmode=bar_mode)
        fig8.update_traces(opacity=opacity)

        fig9 = px.histogram(data, x=grouper_column, color="Trading Last Date", marginal=marginal,
                            title='Strategy {} - {} Histogram (Grouped by Trading Last Date)'.format(strategy_number,
                                                                                                     grouper_column))
        fig9.update_layout(barmode=bar_mode)
        fig9.update_traces(opacity=opacity)

        file_name = grouper_column.replace('/', '-')
        with open(directory_path + '{} NIFTY 200 Histograms.html'.format(file_name), 'w') as f:
            f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig2.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig3.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig4.to_html(full_html=False, include_plotlyjs='cdn'))
            # f.write(fig5.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig6.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig7.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig8.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write(fig9.to_html(full_html=False, include_plotlyjs='cdn'))
    # fig.write_html(directory_path + "Strategy 1 - Trailing Stop Loss v CAGR.html")


def generate_case_id(target_percent, high_type, max_positions, start_date, last_date):
    case_id = 'tp {} hi{} p{} sd{} ld{}'.format(target_percent, high_type, max_positions, start_date, last_date)
    return case_id


def analyse_parameters(data, strategy_number, round_number):
    directory_path = get_directory_path(strategy_number, round_number)
    data['Target-SL'] = data["Target %"].astype(str) + '-' + data["Stop Loss %"].astype(str)
    min_cagr = data['CAGR'].min()
    data['Normalized CAGR'] = data['CAGR'] - min_cagr
    for index, row in data.iterrows():
        data.loc[index, 'ID'] = generate_case_id(row['Target %'], row['High Type'], row['Max Positions'],
                                                 row['Trading Start Date'],
                                                 row['Trading Last Date'])
    x = 'ID'
    y = 'CAGR'
    color = 'Stop Loss %'
    fig1 = px.line(data, x=x, y=y, color=color, title='Target-SL v CAGR - Case Wise Comparision')
    # fig1.update_yaxes(dtick=1)
    # fig1.update_layout(autosize=True, height=2400)

    fig2 = px.bar(data, x=x, y=y, color=color, title='Target-SL v CAGR - Case Wise Comparision')
    # fig2.update_yaxes(dtick=1)
    # fig2.update_layout(autosize=True, height=2400)

    fig3 = px.area(data, x=x, y=y, color=color, title='Target-SL v CAGR - Case Wise Comparision')
    # fig3.update_yaxes(dtick=1)
    # fig3.update_layout(autosize=True, height=2400)

    with open(directory_path + "Parameter Comparision.html", 'w') as f:
        # f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(fig2.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(fig3.to_html(full_html=False, include_plotlyjs='cdn'))


if __name__ == '__main__':
    strategy_index_number = 1
    round_num = 2
    summary = read_stats(strategy_number=strategy_index_number, round_number=round_num, re_combine=False)
    plot_stats(data=summary, strategy_number=strategy_index_number, round_number=round_num)
    analyse_parameters(data=summary, strategy_number=strategy_index_number, round_number=round_num)
