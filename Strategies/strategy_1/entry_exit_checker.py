import pandas as pd

from Constants.constants import *


def entry_condition(df, index, high_type):
    if pd.isna(df.loc[index, CLOSE]) or pd.isna(df.loc[index, high_type]):
        return 0
    if df.loc[index, CLOSE] >= df.loc[index, high_type]:
        return df.loc[index, CLOSE]
    return 0


def exit_condition(df, index, trailing_stop_loss, absolute_stop_loss, target_exit_price):
    if pd.isna(df.loc[index, OPEN]) \
            or pd.isna(df.loc[index, CLOSE]) \
            or pd.isna(trailing_stop_loss) \
            or pd.isna(absolute_stop_loss) \
            or pd.isna(target_exit_price):
        return 0, 0
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
