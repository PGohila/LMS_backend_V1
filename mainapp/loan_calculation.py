from decimal import Decimal, getcontext

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from prettytable import PrettyTable
from decimal import Decimal, InvalidOperation


# Set precision for float operations
getcontext().prec = 5

# Helper function to convert tenure into days based on tenure type
def convert_tenure_to_days(tenure, tenure_type):
    if tenure_type == 'days':
        return tenure
    elif tenure_type == 'weeks':
        return tenure * 7
    elif tenure_type == 'months':
        return tenure * 30
    elif tenure_type == 'years':
        return tenure * 365

# Helper function to determine periods and interval based on the repayment schedule
def determine_periods_and_interval(tenure_in_days, repayment_schedule):
    if repayment_schedule == 'daily':
        return tenure_in_days, timedelta(days=1)
    elif repayment_schedule == 'weekly':
        return tenure_in_days // 7, timedelta(weeks=1)
    elif repayment_schedule == 'monthly':
        return tenure_in_days // 30, relativedelta(months=1)
    elif repayment_schedule == 'quarterly':
        return tenure_in_days // 91, relativedelta(months=3)
    elif repayment_schedule == 'halfyearly':
        return tenure_in_days // 182, relativedelta(months=6)
    elif repayment_schedule == 'annually':
        return tenure_in_days // 365, relativedelta(years=1)

# Helper function to adjust interest rate based on the interest basis
def adjust_interest_rate(interest_rate, periods, interest_basis):
    if interest_basis == '365':
        return float(interest_rate) / float(100) / float(365 / periods)
    else:
        return float(interest_rate) / float(100) / float(365 / periods)

# Helper function to build a repayment entry with opening and closing balance
def build_repayment_entry(period, principal, interest, due_date, opening_balance, closing_balance):
    principal = float(principal)
    interest = float(interest)
    
    return {
        'Period': period,
        'Opening_Balance': round(opening_balance, 2),
        'Principal': round(principal, 2),
        'Interest': round(interest, 2),
        'Installment': round(principal + interest, 2),
        'Closing_Balance': round(closing_balance, 2),
        'Due_Date': due_date.strftime('%Y-%m-%d') if due_date else None,
    }

# Function to display the repayment plan in a table
def display_repayment_table(repayment_plan):
    table = PrettyTable()
    table.field_names = ["Period", "Opening Balance", "Principal", "Interest", "Installment", "Closing Balance", "Due Date"]
    for entry in repayment_plan:
        table.add_row([entry['Period'], entry['Opening_Balance'], entry['Principal'], entry['Interest'], entry['Installment'], entry['Closing_Balance'], entry['Due_Date']])
    print(table)

# Loan calculation methods
# 1. calculate_reducing_balance
def calculate_reducing_balance(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    # Ensure repayment_start_date is a datetime object
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d')  # Change format as necessary

    repayment_plan = []
    remaining_principal = float(loan_amount)  # Ensure this is a float
    period_interest_rate = float(interest_rate) / float(12) / float(100)  # Monthly interest rate

    # Calculate EMI (monthly installment) using float
    emi = (remaining_principal * period_interest_rate * (1 + period_interest_rate) ** float(periods)) / ((1 + period_interest_rate) ** float(periods) - 1)

    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = remaining_principal * period_interest_rate
        
        if repayment_mode == 'principal_only':
            principal_payment = emi - interest_payment
            interest_payment = float(0)
        elif repayment_mode == 'interest_only':
            principal_payment = float(0)
        elif repayment_mode == 'both':
            principal_payment = emi - interest_payment
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = float(0)
            else:
                principal_payment = emi - interest_payment
        elif repayment_mode == 'principal_end':
            principal_payment = float(0) if period < periods else remaining_principal
        else:
            raise ValueError(f"Unsupported repayment mode: {repayment_mode}")

        # Check for negative principal payment
        if principal_payment < 0:
            raise ValueError("Calculated principal payment cannot be negative.")

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        
        # Calculate due_date properly
        due_date = repayment_start_date + timedelta(days=30 * (period - 1)) if interval else repayment_start_date
        
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    print("repayment_plan",repayment_plan)
    return repayment_plan

# 2. calculate_flat_rate
def calculate_flat_rate(loan_amount, interest_rate, tenure, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate)
    tenure = float(tenure)
    
    fixed_interest = loan_amount * interest_rate / float(100) * tenure / float(12)
    monthly_payment = (loan_amount + fixed_interest) / periods
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = fixed_interest / periods
        
        if repayment_mode == 'principal_only':
            principal_payment = monthly_payment - interest_payment
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            principal_payment = loan_amount / periods
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = loan_amount / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal

        if interval == 'monthly':
            due_date = repayment_start_date + relativedelta(months=period - 1)
        elif interval == 'quarterly':
            due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
        elif interval == 'yearly':
            due_date = repayment_start_date + relativedelta(years=period - 1)
        else:
            due_date = repayment_start_date

        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))

    return repayment_plan

# 3. calculate_constant_repayment(Amortization)
def calculate_constant_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate)
    periods = int(periods)
    
    period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
    monthly_payment = (loan_amount * period_interest_rate) / (1 - (1 + period_interest_rate) ** -periods)
    
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = remaining_principal * period_interest_rate
        
        if repayment_mode == 'principal_only':
            principal_payment = monthly_payment - interest_payment
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            principal_payment = monthly_payment - interest_payment
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = monthly_payment - interest_payment
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        
        if interval == 'monthly':
            due_date = repayment_start_date + relativedelta(months=period - 1)
        elif interval == 'quarterly':
            due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
        elif interval == 'yearly':
            due_date = repayment_start_date + relativedelta(years=period - 1)
        else:
            due_date = repayment_start_date
        
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 4. calculate_simple_interest
def calculate_simple_interest(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    
    total_interest = loan_amount * interest_rate
    interest_payment = total_interest / periods
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        
        if repayment_mode == 'principal_only':
            principal_payment = loan_amount / periods
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            principal_payment = loan_amount / periods
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = loan_amount / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 5. calculate_compound_interest
def calculate_compound_interest(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = remaining_principal * (1 + interest_rate) ** period - remaining_principal
        
        if repayment_mode == 'principal_only':
            principal_payment = loan_amount / periods
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            principal_payment = loan_amount / periods
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = loan_amount / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 6. calculate_graduated_repayment
def calculate_graduated_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = remaining_principal * interest_rate / periods
        
        # Graduated payments increase over time
        principal_payment = loan_amount / periods * (1 + float(0.05) * period)
        
        if repayment_mode == 'principal_only':
            principal_payment = loan_amount / periods
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            pass  # Already computed above
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = loan_amount / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 7. calculate_balloon_payment
def calculate_balloon_payment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode, balloon_percentage):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    balloon_payment = loan_amount * float(balloon_percentage) / float(100)
    
    remaining_principal = loan_amount - balloon_payment
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = remaining_principal * interest_rate / periods
        
        if period == periods:
            principal_payment = balloon_payment
        else:
            principal_payment = (loan_amount - balloon_payment) / periods
        
        if repayment_mode == 'principal_only':
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            pass
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = (loan_amount - balloon_payment) / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal
        
        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 8. calculate_bullet_repayment
def calculate_bullet_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    
    remaining_principal = loan_amount
    total_interest = loan_amount * interest_rate * periods
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        
        # Bullet repayment at the end of the term
        principal_payment = loan_amount if period == periods else 0
        interest_payment = total_interest if period == periods else 0
        
        if repayment_mode == 'principal_only':
            interest_payment = 0
        elif repayment_mode == 'interest_only':
            principal_payment = 0
        elif repayment_mode == 'both':
            pass
        elif repayment_mode == 'interest_first':
            if period <= periods // 2:
                principal_payment = 0
            else:
                principal_payment = loan_amount / periods
        elif repayment_mode == 'principal_end':
            principal_payment = 0 if period < periods else remaining_principal

        remaining_principal -= principal_payment
        closing_balance = remaining_principal
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan

# 9. calculate_interest_only
def calculate_interest_only(loan_amount, interest_rate, periods, interval, repayment_start_date):
    repayment_plan = []
    
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate) / float(100)
    
    remaining_principal = loan_amount
    
    if isinstance(repayment_start_date, str):
        repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
    for period in range(1, periods + 1):
        opening_balance = remaining_principal
        interest_payment = loan_amount * interest_rate / periods
        principal_payment = 0  # Only interest is paid until the final period
        
        if period == periods:
            principal_payment = loan_amount  # Principal repaid at the end
        
        closing_balance = remaining_principal - principal_payment
        due_date = repayment_start_date + interval * (period - 1)
        repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
    return repayment_plan












































# from float import float, getcontext
# from datetime import timedelta, date,datetime
# from dateutil.relativedelta import relativedelta
# from prettytable import PrettyTable

# getcontext().prec = 5  # Set precision for float operations

# # Helper function to convert tenure into days based on tenure type
# def convert_tenure_to_days(tenure, tenure_type):
#     if tenure_type == 'days':
#         return tenure
#     elif tenure_type == 'weeks':
#         return tenure * 7
#     elif tenure_type == 'months':
#         return tenure * 30
#     elif tenure_type == 'years':
#         return tenure * 365

# # Helper function to determine periods and interval based on the repayment schedule
# def determine_periods_and_interval(tenure_in_days, repayment_schedule):
#     if repayment_schedule == 'daily':
#         return tenure_in_days, timedelta(days=1)
#     elif repayment_schedule == 'weekly':
#         return tenure_in_days // 7, timedelta(weeks=1)
#     elif repayment_schedule == 'monthly':
#         return tenure_in_days // 30, relativedelta(months=1)
#     elif repayment_schedule == 'quarterly':
#         return tenure_in_days // 91, relativedelta(months=3)
#     elif repayment_schedule == 'halfyearly':
#         return tenure_in_days // 182, relativedelta(months=6)
#     elif repayment_schedule == 'annually':
#         return tenure_in_days // 365, relativedelta(years=1)

# # Helper function to adjust interest rate based on the interest basis
# def adjust_interest_rate(interest_rate, periods, interest_basis):
#     if interest_basis == '365':
#         return float(interest_rate) / float(100) / float(365 / periods)
#     else:
#         return float(interest_rate) / float(100) / float(365 / periods)

# # Helper function to build a repayment entry with opening and closing balance
# def build_repayment_entry(period, principal, interest, due_date, opening_balance, closing_balance):
#     principal = float(principal)
#     interest = float(interest)
    
#     return {
#         'Period': period,
#         'Opening_Balance': round(opening_balance, 2),
#         'Principal': round(principal, 2),
#         'Interest': round(interest, 2),
#         'Installment': round(principal + interest, 2),
#         'Closing_Balance': round(closing_balance, 2),
#         'Due_Date': due_date.strftime('%Y-%m-%d') if due_date else None,
#     }

# # Function to display the repayment plan in a table
# def display_repayment_table(repayment_plan):
#     table = PrettyTable()
#     table.field_names = ["Period", "Opening Balance", "Principal", "Interest", "Installment", "Closing Balance", "Due Date"]
#     for entry in repayment_plan:
#         table.add_row([entry['Period'], entry['Opening_Balance'], entry['Principal'], entry['Interest'], entry['Installment'], entry['Closing_Balance'], entry['Due_Date']])
#     print(table)

# # Loan calculation methods
# # 1. calculate_reducing_balance
# def calculate_reducing_balance(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
#     remaining_principal = loan_amount
#     period_interest_rate = float(interest_rate) / 12 / 100  # Monthly interest rate

#     # Calculate EMI (monthly installment)
#     emi = loan_amount * period_interest_rate * (1 + period_interest_rate) ** periods / ((1 + period_interest_rate) ** periods - 1)

#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
#         interest_payment = float(remaining_principal) * float(period_interest_rate)
#         principal_payment = float(emi) - interest_payment
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal
#         due_date = repayment_start_date + timedelta(days=30 * (period - 1)) if interval else repayment_start_date
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
#     return repayment_plan

# # 2. calculate_flat_rate
# def calculate_flat_rate(loan_amount, interest_rate, tenure, periods, interval, repayment_start_date):
#     repayment_plan = []
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     tenure = float(tenure)
    
#     fixed_interest = loan_amount * interest_rate / float(100) * tenure / float(12)
#     monthly_payment = (loan_amount + fixed_interest) / periods
#     remaining_principal = loan_amount
    
#     if isinstance(repayment_start_date, str):
#         repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
#         interest_payment = fixed_interest / periods
#         principal_payment = loan_amount / periods
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal

#         # Handle different intervals using relativedelta
#         if interval == 'monthly':
#             due_date = repayment_start_date + relativedelta(months=period - 1)
#         elif interval == 'quarterly':
#             due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
#         elif interval == 'yearly':
#             due_date = repayment_start_date + relativedelta(years=period - 1)
#         else:
#             due_date = repayment_start_date

#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))

#     return repayment_plan

# # 3. calculate_constant_repayment(Amortization)
# def calculate_constant_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
    
#     # Convert inputs to float for accuracy
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     periods = int(periods)  # Ensure periods is an integer
    
#     # Calculate period interest rate
#     period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
    
#     # Calculate monthly payment
#     monthly_payment = (loan_amount * period_interest_rate) / (1 - (1 + period_interest_rate) ** -periods)
    
#     remaining_principal = loan_amount
    
#     # Convert repayment_start_date to datetime if it's a string
#     if isinstance(repayment_start_date, str):
#         repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
#         interest_payment = remaining_principal * period_interest_rate
#         principal_payment = monthly_payment - interest_payment
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal
        
#         # Handle different intervals using relativedelta
#         if interval == 'monthly':
#             due_date = repayment_start_date + relativedelta(months=period - 1)
#         elif interval == 'quarterly':
#             due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
#         elif interval == 'yearly':
#             due_date = repayment_start_date + relativedelta(years=period - 1)
#         else:
#             due_date = repayment_start_date
        
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
#     return repayment_plan

# # 4. calculate_simple_interest
# def calculate_simple_interest(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
    
#     # Convert inputs to float for accuracy
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate) / float(100)  # Convert percentage to float
    
#     # Calculate interest payment for the entire loan
#     total_interest = loan_amount * interest_rate  # Total interest for the loan term
#     interest_payment = total_interest / periods  # Interest payment per period
#     remaining_principal = loan_amount
    
#     # Convert repayment_start_date to datetime if it's a string
#     if isinstance(repayment_start_date, str):
#         repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
#         principal_payment = loan_amount / periods
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal
        
#         # Handle different intervals using relativedelta
#         if interval == 'monthly':
#             due_date = repayment_start_date + relativedelta(months=period - 1)
#         elif interval == 'quarterly':
#             due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
#         elif interval == 'yearly':
#             due_date = repayment_start_date + relativedelta(years=period - 1)
#         else:
#             due_date = repayment_start_date
        
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
#     return repayment_plan

# # 5. calculate_compound_interest
# def calculate_compound_interest(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
    
#     # Convert inputs to float for accuracy
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     periods = int(periods)
    
#     # Calculate period interest rate based on the interval
#     if interval == 'monthly':
#         period_interest_rate = adjust_interest_rate(interest_rate, periods, '365') / float(12)
#     elif interval == 'quarterly':
#         period_interest_rate = adjust_interest_rate(interest_rate, periods, '365') / float(4)
#     elif interval == 'yearly':
#         period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
#     else:
#         raise ValueError("Unsupported interval type. Use 'monthly', 'quarterly', or 'yearly'.")
    
#     # Convert repayment_start_date to datetime if it's a string
#     if isinstance(repayment_start_date, str):
#         repayment_start_date = datetime.strptime(repayment_start_date, '%Y-%m-%d').date()
    
#     # Compute the compound factor for the entire loan term
#     compound_factor = (1 + period_interest_rate) ** periods
#     total_amount = loan_amount * compound_factor
#     remaining_principal = loan_amount
    
#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
        
#         # Calculate interest and principal payments
#         interest_payment = remaining_principal * period_interest_rate
#         principal_payment = (total_amount / periods) - interest_payment
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal
        
#         # Calculate due date based on interval
#         if interval == 'monthly':
#             due_date = repayment_start_date + relativedelta(months=period - 1)
#         elif interval == 'quarterly':
#             due_date = repayment_start_date + relativedelta(months=3 * (period - 1))
#         elif interval == 'yearly':
#             due_date = repayment_start_date + relativedelta(years=period - 1)
        
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
#     return repayment_plan

# # 6. calculate_graduated_repayment
# def calculate_graduated_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     initial_payment = loan_amount / float(periods)
#     increment_factor = float(1.05)  # 5% increment per period
#     period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
#     remaining_principal = loan_amount

#     for period in range(1, periods + 1):
#         opening_balance = remaining_principal
#         interest_payment = remaining_principal * period_interest_rate

#         # Calculate the principal payment with increment factor
#         principal_payment = initial_payment * (increment_factor ** (period - 1))
        
#         # Adjust principal payment if it exceeds the remaining principal
#         if principal_payment > remaining_principal:
#             principal_payment = remaining_principal

#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal

#         due_date = repayment_start_date + timedelta(days=interval * (period - 1))
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
        
#         # Exit loop if remaining principal is zero
#         if remaining_principal <= 0:
#             break
    
#     return repayment_plan

# # 7. calculate_balloon_payment
# def calculate_balloon_payment(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     periods = float(periods)
#     interval = float(interval)
#     balloon_amount = loan_amount * float(0.5)  # 50% as balloon payment
#     monthly_payment = (loan_amount - balloon_amount) / (periods - 1)
#     period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
#     remaining_principal = loan_amount

#     for period in range(1, int(periods)):
#         opening_balance = remaining_principal
#         interest_payment = remaining_principal * period_interest_rate
#         principal_payment = monthly_payment - interest_payment
#         remaining_principal -= principal_payment
#         closing_balance = remaining_principal
#         due_date = repayment_start_date + timedelta(days=int(interval) * (period - 1))
#         repayment_plan.append(build_repayment_entry(period, principal_payment, interest_payment, due_date, opening_balance, closing_balance))
    
#     # Balloon payment in the last period
#     due_date = repayment_start_date + timedelta(days=int(interval) * int(periods - 1))
#     repayment_plan.append(build_repayment_entry(int(periods), balloon_amount, remaining_principal * period_interest_rate, due_date, remaining_principal, 0))
    
#     return repayment_plan

# # 8. calculate_bullet_repayment
# def calculate_bullet_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date):
#     repayment_plan = []
#     loan_amount = float(loan_amount)
#     interest_rate = float(interest_rate)
#     periods = float(periods)
#     interval = float(interval)
#     period_interest_rate = adjust_interest_rate(interest_rate, periods, '365')
    
#     for period in range(1, int(periods)):
#         opening_balance = loan_amount
#         interest_payment = loan_amount * period_interest_rate
#         due_date = repayment_start_date + timedelta(days=int(interval) * (period - 1))
#         repayment_plan.append(build_repayment_entry(period, float(0), interest_payment, due_date, opening_balance, opening_balance))
    
#     # Bullet payment in the last period
#     due_date = repayment_start_date + timedelta(days=int(interval) * (int(periods) - 1))
#     repayment_plan.append(build_repayment_entry(int(periods), loan_amount, loan_amount * period_interest_rate,
#                                               due_date, loan_amount, float(0)))
    
#     return repayment_plan

# def calculate_repayment_schedule(loan_amount, interest_rate, tenure, tenure_type, repayment_schedule, loan_calculation_method, repayment_start_date):
#     """" # Main function to execute the repayment calculations based on method """
#     tenure_in_days = convert_tenure_to_days(tenure, tenure_type)
#     periods, interval = determine_periods_and_interval(tenure_in_days, repayment_schedule)

#     if loan_calculation_method == 'reducing_balance':
#         repayment_plan = calculate_reducing_balance(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'flat_rate':
#         repayment_plan = calculate_flat_rate(loan_amount, interest_rate, tenure, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'constant_repayment':
#         repayment_plan = calculate_constant_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'simple_interest':
#         repayment_plan = calculate_simple_interest(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'compound_interest': 
#         repayment_plan = calculate_compound_interest(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'graduated_repayment':
#         repayment_plan = calculate_graduated_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'balloon_payment':
#         repayment_plan = calculate_balloon_payment(loan_amount, interest_rate, periods, interval, repayment_start_date)
#     elif loan_calculation_method == 'bullet_repayment':
#         repayment_plan = calculate_bullet_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date)

#     # Display repayment plan
#     display_repayment_table(repayment_plan)
#     return repayment_plan

