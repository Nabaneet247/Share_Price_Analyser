from Models.interval import Interval
from Utils.string_utils import get_period_labels_from_string
import pandas as pd


def get_interval_obj_from_strings(strings):
    intervals = []
    for string in strings:
        interval = get_interval_obj_from_string(string)
        intervals.append(interval)
    return intervals


def get_interval_obj_from_string(string):
    interval = Interval()
    freq_value, freq_unit = get_period_labels_from_string(string)
    if freq_unit.startswith('y'):
        interval.value = freq_value
        interval.unit = 'Year'
        interval.abbreviation = str(freq_value) + 'Y'
        interval.offset = pd.offsets.DateOffset(years=freq_value)
    elif freq_unit.startswith('m'):
        interval.value = freq_value
        interval.unit = 'Month'
        interval.abbreviation = str(freq_value) + 'M'
        interval.offset = pd.offsets.DateOffset(months=freq_value)
    else:
        interval.value = freq_value
        interval.unit = 'Day'
        interval.abbreviation = str(freq_value) + 'D'
        interval.offset = pd.offsets.DateOffset(days=freq_value)
    return interval
