#!/usr/bin/env python
"""Cash flow rebalancing app"""
import numpy as np
from prettytable import PrettyTable

__author__ = "Leon Beckert"
__copyright__ = "Copyright 2023, Cash Flow Rebalancing Calculator"
__credits__ = ["Leon Beckert"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.0.1"
__maintainer__ = "Leon Beckert"
__email__ = "beckert@leon.fm"
__status__ = "Production"

def correct_input(investments, distributions):
    """Checks whether the input is formatted correctly"""
    # Check whether number of investments and distributions match
    if not len(investments) == distributions.size:
        return False
    # Check whether total distribution adds up to 100%
    if distributions.sum() != 1:
        return False
    # If all checks run successfully exit with success
    return True


def calculate_current_distributions(investments):
    """Calculates the current distributions"""
    current_distributions = []
    total_amount = 0
    for investment in investments:
        total_amount += investment
    for investment in investments:
        current_distributions.append(round(investment / total_amount, 8))
    return current_distributions


def find_highest_positive_deviation(investments, distributions):
    """Finds the stock deviating positively the most from its target percentage"""
    highest_positive_deviation = 0
    highest_positive_deviation_location = 0
    current_distributions = calculate_current_distributions(investments)
    for counter, current_distribution in enumerate(current_distributions):
        temp_deviation = current_distribution - distributions[counter]
        if highest_positive_deviation < temp_deviation:
            highest_positive_deviation = temp_deviation
            highest_positive_deviation_location = counter
    return highest_positive_deviation_location


def calculate_minimum_rebalancing_amounts(investments, distrib_targets):
    """Calculates the minimum amount necessary to rebalance to the highest value"""
    max_dev_loc = find_highest_positive_deviation(investments, distrib_targets)
    total_target = investments[max_dev_loc] / distrib_targets[max_dev_loc]
    single_necessary_investments = []
    for counter, distribution in enumerate(distrib_targets):
        single_necessary_investments.append(
            total_target * distribution - investments[counter])
    return single_necessary_investments


def calculate_exact_rebalancing_amounts(investment_capital, post_comma_round,
    amounts, distribution_targets):
    """Calculates the exact rebalancing amounts for each position"""
    rebalancing_investments = calculate_minimum_rebalancing_amounts(
        amounts, distribution_targets)
    if not sufficient_rebalancing_capital(investment_capital, rebalancing_investments):
        return False, []
    remaining_capital = investment_capital
    for amount in rebalancing_investments:
        remaining_capital -= amount
    post_rebalancing_amount_per_position = remaining_capital / \
        len(rebalancing_investments)
    for counter, amount in enumerate(rebalancing_investments):
        rebalancing_investments[counter] = round(
            rebalancing_investments[counter] +
            post_rebalancing_amount_per_position,
            post_comma_round)
    return True, rebalancing_investments


def sufficient_rebalancing_capital(investment_capital, rebalancing_investments):
    """Checks whether investment capital is sufficient for rebalancing"""
    total_investment_needed = 0
    for amount in rebalancing_investments:
        total_investment_needed += amount
    if total_investment_needed > investment_capital:
        return False
    return True


def calculate_below_threshold(amounts, target_weights, investment):
    """If the investment is not sufficient we need to calculate the minimum"""
    current_values = np.array(amounts)
    current_total = current_values.sum()
    current_weights = current_values / current_total

    # calculate deviation of current weights from target weights
    deviation = current_weights - target_weights

    # find the index of the asset with the highest positive deviation
    index_highest_positive_deviation = np.where(deviation == deviation[deviation > 0].max())[0]
    target_portfolio_total = amounts[
        index_highest_positive_deviation[0]] / target_weights[index_highest_positive_deviation[0]]
    target_portfolio_values = np.array(target_portfolio_total * target_weights)
    target_values = np.copy(current_values)
    while investment > 0:
        deviation = target_values - target_portfolio_values
        index_highest_deviation = np.argmax(np.abs(deviation))
        target_values[index_highest_deviation] += 1
        investment -= 1
    rebalancing_values = target_values - current_values
    return rebalancing_values, target_values


def user_interface(names, distribution_targets):
    """Command line interface"""
    amounts = []
    print(f"\nPlease insert your current portfolio position values in {CURRENCY}:\n")
    for count, name in enumerate(names):
        while True:
            try:
                amount = int(input(f"{name}: \t"))
                if amount >= 0:
                    amounts.append(amount)
                else:
                    raise ValueError()
                break
            except ValueError:
                print("Please write a valid positive number.")
    table = PrettyTable()
    table.field_names = ["Position", "Value", "Distribution"]
    for count, name in enumerate(names):
        table.add_row([name, f"{amounts[count]:.2f} {CURRENCY}",
                      f"{amounts[count]*100/sum(amounts):.2f} %"])
    table.add_row(["", "", ""])
    table.add_row(["Total portfolio value", f"{sum(amounts):.2f} {CURRENCY}", ""])
    print("\n Your current portfolio:")
    print(table)

    minimum_amounts = calculate_minimum_rebalancing_amounts(
        amounts, distribution_targets)
    minimum_amount = sum(minimum_amounts)
    print(
        f"\nTo rebalance fully, you need to invest a minimum of {minimum_amount:.2f} {CURRENCY}\n\n")
    if input("- Show portfolio fully rebalanced? (y/n)\t") == "y":
        rebalance_table = PrettyTable()
        rebalance_table.field_names = ["Position", "Value", "Distribution"]
        for count, name in enumerate(names):
            total = amounts[count] + minimum_amounts[count]
            rebalance_table.add_row([name, f"{total:.2f} {CURRENCY}",
                                     f"{distribution_targets[count]*100:.2f} %"])
        rebalance_table.add_row(["", "", ""])
        rebalance_table.add_row(["Total",
                                 f"{(sum(amounts) + sum(minimum_amounts)):.2f} {CURRENCY}", ""])
        print(
            f"\n Your portfolio after rebalancing with {minimum_amount:.2f} {CURRENCY}:")
        print(rebalance_table)
    while True:
        try:
            available_capital = int(
                input("\nHow much do you want to invest?\n\n- Amount: "))
            break
        except ValueError:
            print("\nInput invalid. Please write a valid positive number.")
    rebalancing_possible, rebalancing_amounts = calculate_exact_rebalancing_amounts(
        available_capital, 3, amounts, distribution_targets)
    actual_distributions = distribution_targets
    if not rebalancing_possible:
        numpy_reb_amounts, target_amounts = calculate_below_threshold(
            amounts, distribution_targets, available_capital)
        rebalancing_amounts = numpy_reb_amounts.tolist()
        investments = target_amounts.tolist()
        actual_distributions = calculate_current_distributions(investments)
    rebalance_amounts_table = PrettyTable()
    rebalance_amounts_table.field_names = [
        "Position", "Rebalancing amount"]
    for count, name in enumerate(names):
        rebalance_amounts_table.add_row(
            [name, f"{rebalancing_amounts[count]:.2f} {CURRENCY}"])
    print("\n Your rebalancing amounts are:")
    print(rebalance_amounts_table)
    # Create rebalance total table
    rebalance_total_table = PrettyTable()
    rebalance_total_table.field_names = [
        "Position", "Value", "Distribution"]
    for count, name in enumerate(names):
        rebalance_total_table.add_row([name,
                                        f"{(amounts[count] + rebalancing_amounts[count]):.2f} {CURRENCY}",
                                        f"{actual_distributions[count]*100:.2f} %"])
    rebalance_total_table.add_row(["", "", ""])
    rebalance_total_table.add_row(["Total",
                                    f"{sum(amounts) + sum(rebalancing_amounts):.2f} {CURRENCY}", ""])
    print("\n Your portfolio after rebalancing:")
    print(rebalance_total_table)
    print("\n")

# ONLY EDIT BELOW THIS LINE

CURRENCY = "€"
investment_portfolio = [
    "iShares MSCI World Small Cap",
    "iShares Core MSCI EM IMI",
    "xTrackers MSCI World Value",
    "xTrackers MSCI World Quality",
    "xTrackers MSCI World Momentum"]
target_distributions = np.array([
    0.20, # 20% iShares MSCI World Small Cap
    0.20, # 20% iShares Core MSCI EM IMI
    0.20, # 20% xTrackers MSCI World Value
    0.20, # 20% xTrackers MSCI World Quality
    0.20 # 20% xTrackers MSCI World Momentum
    ])
    
# ONLY EDIT ABOVE THIS LINE

if not correct_input(investment_portfolio, target_distributions):
    print("Input wrong.")
else:
    user_interface(investment_portfolio, target_distributions)
