def find_difference_between_two_lists(first_list, second_list):
    missing_values = []
    for values in first_list:
        if values not in second_list:
            missing_values.append(values)
    return missing_values
