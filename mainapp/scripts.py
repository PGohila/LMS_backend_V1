from datetime import date
from .models import *
#Create your views here.
def success(msg):
    # Create a dictionary named 'response' with two key-value pairs
    response={
        'status_code':0, # Key 'status_code' with value 0
        'data':msg       # Key 'data' with value 'msg' (the input parameter)
    }
    # Return the 'response' dictionary
    return response

def error(msg):
    # Create a dictionary with error details
    response={
        'status_code':1, # Status code indicating error
        'data':msg  # Error message
    }
    # Return the 'response' dictionary
    return response

def unique_id(pre, last_id):
    today1=date.today()
    today = today1.strftime("%d%m%y")
    last_ids = int(last_id) + 1
    if len(str(last_ids)) == 1:
        id = pre + today + '00' + str(last_ids)
    elif len(str(last_ids)) == 2:
        id = pre + today + '0' + str(last_ids)
    else:
        id = pre + today + str(last_ids)
    return id

# calculate credit score
def calculate_credit_score(payment_history, credit_utilization, credit_age, credit_mix, recent_inquiries):
    # Assigning weights to each component (you can adjust these)
    payment_weight = 0.35
    utilization_weight = 0.30
    age_weight = 0.15
    mix_weight = 0.10
    inquiries_weight = 0.10

    # Simple scoring logic (out of 1000 points)
    credit_score = (
        (payment_history * payment_weight) +
        (credit_utilization * utilization_weight) +
        (credit_age * age_weight) +
        (credit_mix * mix_weight) +
        (recent_inquiries * inquiries_weight)
    ) * 10  # Scale up to a 1000-point score system

    return min(max(credit_score, 300), 850)  # Ensure score is between 300 and 850

# existing liabilities calculation with customer existing loans
def calculate_existing_liabilities(loans):
    """
    loans is a list of dicts where each dict contains 'loan_type', 'outstanding_amount'
    Example: loans = [{'loan_type': 'home_loan', 'outstanding_amount': 50000}, ...]
    """
    total_liabilities = 0
    print("fehgferretr")
    for loan in loans:
        print("sadasdasdas",loan)
        loans = Loan.objects.get(id = loan )
        total_liabilities += loans.loan_amount
    
    
    return total_liabilities


# loan eligibilitity checking
def check_loan_eligibility(applicant_details, loan_amount):
    errors = []
   
    # Age check
    if not (21 <= applicant_details.age <= 65):
        errors.append("Applicant does not meet the age criteria (21-65 years).")

    # Income check
    minimum_income = 25000  # Example threshold # loan type minimum income
    if applicant_details.customer_income < minimum_income:
        errors.append(f"Monthly income is below the threshold of {minimum_income}. income {applicant_details.customer_income}")
    
    # Credit score check
    minimum_credit_score = 650  # Example threshold
    if applicant_details.credit_score < minimum_credit_score:
        errors.append(f"Credit score is below the required {minimum_credit_score}.")
    
    # Debt-to-income ratio check
    if applicant_details.customer_income > 0:  # Prevent division by zero
        debt_to_income_ratio = (applicant_details.existing_liabilities / applicant_details.customer_income) * 100
        if debt_to_income_ratio > 40:  # Example threshold
            errors.append(
                f"Debt-to-income ratio exceeds the allowable limit of 40%. Current ratio: {debt_to_income_ratio:.2f}%"
            )
    
    # Final decision
    if errors:
        return False, errors  # Not eligible
    else:
        return True, []  # Eligible


# Helper function to calculate risk score based on customer and loan application details
def calculate_risk_score(customer, loan_application):
    # Risk score calculation based on factors like credit score, income, and liabilities
    credit_score_weight = 0.4
    liabilities_weight = 0.3
    income_to_loan_ratio_weight = 0.2
    loan_amount_weight = 0.1

    # Example risk factors
    credit_score_risk = (700 - customer.credit_score) / 100 * credit_score_weight
    liabilities_risk = (customer.existing_liabilities / customer.customer_income) * liabilities_weight
    income_to_loan_ratio = loan_application.loan_amount / customer.customer_income
    income_to_loan_risk = income_to_loan_ratio * income_to_loan_ratio_weight

    total_risk = credit_score_risk + liabilities_risk + income_to_loan_risk
    return total_risk * 100  # Returning risk as a percentage

def calculate_risk_factors(customer, loan_application):
    # Similar to calculate_risk_score but returning individual risk factors
    credit_score_weight = 0.4
    liabilities_weight = 0.3
    income_to_loan_ratio_weight = 0.2
    loan_amount_weight = 0.1

    credit_score_risk = (700 - customer.credit_score) / 100 * credit_score_weight
    liabilities_risk = (customer.existing_liabilities / customer.customer_income) * liabilities_weight
    income_to_loan_ratio = loan_application.loan_amount / customer.customer_income
    income_to_loan_risk = income_to_loan_ratio * income_to_loan_ratio_weight

    risk_factors = {
        'Credit Score Risk': credit_score_risk,
        'Liabilities Risk': liabilities_risk,
        'Income to Loan Risk': income_to_loan_risk,
    }

    total_risk = credit_score_risk + liabilities_risk + income_to_loan_risk
    return total_risk * 100, risk_factors