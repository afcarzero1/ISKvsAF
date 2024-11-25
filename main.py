import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from typing import List, Tuple

from typing import List


def compute_isk_tax(
        quarterly_values: List[float],
        annual_deposits: float,
        gov_interest_rate: float
) -> float:
    """
    Compute the tax on ISK according to the actual ISK tax rules.

    Parameters:
    - quarterly_values: List of ISK values at the start of each quarter.
    - annual_deposits: Total amount deposited during the year.
    - gov_interest_rate: Government borrowing rate (as a decimal).

    Returns:
    - The tax amount to be deducted from the ISK account.
    """
    assert len(quarterly_values) == 4, "Must contain 4 quarterly values"
    # Step 1: Calculate average value
    total_quarterly = sum(quarterly_values)
    average_value = (total_quarterly + annual_deposits) / 4

    # Step 2: Compute standard income
    standard_rate = max(gov_interest_rate + 0.01, 0.0125)
    standard_income = average_value * standard_rate

    # Step 3: Compute tax (30% of standard income)
    tax = standard_income * 0.3

    return tax


def compute_isk(
        capital: float,
        monthly_investment: float,
        annual_return: float,
        gov_interest_rate: float,
        years: int
) -> (List[float], List[float], List[float]):
    """
    Compute monthly values for ISK account according to actual ISK tax rules.

    Parameters:
    - capital: Initial capital in the ISK account.
    - monthly_investment: Amount invested monthly.
    - annual_return: Expected annual return rate (as a decimal).
    - gov_interest_rate: Government borrowing rate (as a decimal).
    - years: Number of years to simulate.

    Returns:
    - A tuple containing:
      - List of ISK account values at the end of each month.
      - List of total tax paid up to each month.
      - List of total gains up to each month.
    """
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    isk_value = capital
    isk_values = [isk_value]
    total_months = years * 12

    # Variables to track quarterly values and annual deposits
    quarterly_values = []
    annual_deposits = 0
    total_tax_paid = 0
    tax_paid_list = [0.0]
    total_invested = capital  # Initial capital
    total_gains_list = [0.0]  # Initial gains are zero

    for month in range(1, total_months + 1):
        # Record the isk_value at the start of each quarter (before any actions in that month)
        if (month - 1) % 12 in [0, 3, 6, 9]:
            quarterly_values.append(isk_value)

        # Add monthly investment
        isk_value += monthly_investment
        annual_deposits += monthly_investment
        total_invested += monthly_investment

        # Apply monthly return
        isk_value *= (1 + monthly_return)

        # Apply tax at the end of each year, but not in the first month
        if month % 12 == 0:
            # Compute tax using the separate function
            tax = compute_isk_tax(quarterly_values, annual_deposits, gov_interest_rate)

            # Deduct tax from isk_value
            isk_value -= tax
            total_tax_paid += tax

            # Reset annual variables
            quarterly_values = []
            annual_deposits = 0
        else:
            tax = 0.0

        isk_values.append(isk_value)
        tax_paid_list.append(total_tax_paid)

        # Calculate total gains
        total_gains = isk_value - total_invested
        total_gains_list.append(total_gains)

    return isk_values, tax_paid_list, total_gains_list


def compute_af(
    capital: float,
    monthly_investment: float,
    annual_return: float,
    af_tax_rate: float,
    years: int
) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute monthly values for AF account according to standard tax rules.

    Parameters:
    - capital: Initial capital in the AF account.
    - monthly_investment: Amount invested monthly.
    - annual_return: Expected annual return rate (as a decimal).
    - af_tax_rate: Tax rate applied to gains at the end (as a decimal).
    - years: Number of years to simulate.

    Returns:
    - A tuple containing:
      - List of AF account values at the end of each month.
      - List of total tax paid up to each month.
      - List of total gains up to each month.
    """
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    af_value = capital
    af_values = [af_value]
    total_months = years * 12
    total_invested = capital
    total_gains_list = [0.0]
    tax_paid_list = [0.0]  # Tax is only paid at the end
    total_tax_paid = 0.0

    for month in range(1, total_months + 1):
        # Add monthly investment
        af_value += monthly_investment
        total_invested += monthly_investment

        # Apply monthly return
        af_value *= (1 + monthly_return)

        # Append the current AF account value
        af_values.append(af_value)

        # Calculate total gains
        total_gains = af_value - total_invested
        total_gains_list.append(total_gains)

        # Tax is only applied at the end, so tax paid remains the same until the last month
        tax_paid_list.append(total_tax_paid)

    # Apply tax on total gain at the end
    total_gain = af_value - total_invested
    af_tax = total_gain * af_tax_rate
    af_value_after_tax = af_value - af_tax
    total_tax_paid += af_tax

    # Update the last AF account value and tax paid
    af_values[-1] = af_value_after_tax
    tax_paid_list[-1] = total_tax_paid
    total_gains_list[-1] = af_value_after_tax - total_invested

    return af_values, tax_paid_list, total_gains_list


def main():
    # Streamlit App
    st.title("ISK vs AF Account Growth Visualization with Monthly Investments")
    st.sidebar.header("Input Parameters")

    # Input Parameters
    capital: float = st.sidebar.number_input("Initial Capital (SEK)", value=10000.0, min_value=0.0, step=1000.0)
    monthly_investment: float = st.sidebar.number_input(
        "Monthly Investment (SEK)", value=1000.0, min_value=0.0, step=100.0
    )
    annual_return: float = st.sidebar.number_input(
        "Annual Investment Return (%)", value=5.0, step=0.1
    ) / 100
    isk_interest_rate: float = st.sidebar.number_input(
        "Government Borrowing Rate (%)", value=2.62, step=0.01
    ) / 100
    af_tax_rate: float = st.sidebar.number_input("AF Tax Rate (%)", value=30.0, step=0.1) / 100
    years: int = st.sidebar.slider("Investment Period (Years)", min_value=1, max_value=50, value=20)

    # Compute ISK and AF Values using the new functions
    isk_values, isk_tax_paid_list, isk_total_gains_list = compute_isk(
        capital, monthly_investment, annual_return, isk_interest_rate, years
    )
    af_values, af_tax_paid_list, af_total_gains_list = compute_af(
        capital, monthly_investment, annual_return, af_tax_rate, years
    )

    # Prepare Data for Plotting
    months = list(range(len(isk_values)))
    years_labels = [month / 12 for month in months]

    # Plotting Account Values
    st.subheader("Account Value Over Time")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years_labels, isk_values, label='ISK Account', linewidth=2)
    ax.plot(years_labels, af_values, label='AF Account', linestyle='--', linewidth=2)
    ax.set_xlabel("Years")
    ax.set_ylabel("Account Value (SEK)")
    ax.set_title("ISK vs AF Account Growth Over Time with Monthly Investments")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Plotting Total Tax Paid Over Time
    st.subheader("Total Tax Paid Over Time")
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.plot(years_labels, isk_tax_paid_list, label='ISK Total Tax Paid', linewidth=2)
    ax2.plot(years_labels, af_tax_paid_list, label='AF Total Tax Paid', linestyle='--', linewidth=2)
    ax2.set_xlabel("Years")
    ax2.set_ylabel("Total Tax Paid (SEK)")
    ax2.set_title("Total Tax Paid Over Time")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

    # Plotting Total Gains Over Time
    st.subheader("Total Gains Over Time")
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(years_labels, isk_total_gains_list, label='ISK Total Gains', linewidth=2)
    ax3.plot(years_labels, af_total_gains_list, label='AF Total Gains', linestyle='--', linewidth=2)
    ax3.set_xlabel("Years")
    ax3.set_ylabel("Total Gains (SEK)")
    ax3.set_title("Total Gains Over Time")
    ax3.legend()
    ax3.grid(True)
    st.pyplot(fig3)

    # Display Data in a Table
    st.subheader("Monthly Account Values, Gains, and Taxes")
    data = {
        "Month": months,
        "Year": years_labels,
        "ISK Account": isk_values,
        "ISK Total Tax Paid": isk_tax_paid_list,
        "ISK Total Gains": isk_total_gains_list,
        "AF Account": af_values,
        "AF Total Tax Paid": af_tax_paid_list,
        "AF Total Gains": af_total_gains_list,
    }
    df = pd.DataFrame(data)
    st.dataframe(df)


if __name__ == '__main__':
    main()
