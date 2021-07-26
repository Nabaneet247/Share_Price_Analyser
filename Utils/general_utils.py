from datetime import datetime

from loguru import logger


def find_difference_between_two_lists(first_list, second_list):
    missing_values = []
    for values in first_list:
        if values not in second_list:
            missing_values.append(values)
    return missing_values


def print_running_duration(decorated_function):
    def inner(**kwargs):
        logger.info('Gonna execute {}', decorated_function.__name__)
        start_time = datetime.now()
        decorated_function(**kwargs)
        duration = datetime.now() - start_time
        logger.info('{} was executed in {} mins {} seconds', decorated_function.__name__, duration.total_seconds() // 60,
                    duration.total_seconds() % 60)

    return inner
