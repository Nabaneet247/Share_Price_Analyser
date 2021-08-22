import math

import pandas as pd

from Constants.constants import *


def calculate_cagr(start_date, last_date, starting_capital, final_balance):
    start_date_obj = pd.to_datetime(start_date, format=DEFAULT_DATE_FORMAT)
    end_date_obj = pd.to_datetime(last_date, format=DEFAULT_DATE_FORMAT)
    years = round((end_date_obj - start_date_obj).days / 365, 3)
    cagr = round(math.pow(final_balance / starting_capital, 1 / years) - 1, 4) * 100
    return cagr, years
