from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from user_management.models import *

# MS setup models
class MSRegistration(models.Model):
    mservice_id = models.CharField(max_length=20,primary_key=True)
    mservice_name = models.CharField(max_length=100)
    arguments = models.JSONField(null=True,blank=True)
    arguments_list = models.TextField(null=True,blank=True)
    required_parameter = models.TextField(null=True,blank=True)
    optional_parameter = models.TextField(null=True,blank=True)
    is_authenticate = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
	
    def formatted_mservice_name(self):
        # Replace underscores with spaces in mservice_name
        return self.mservice_name.replace('_', ' ')
    def __str__(self):
        return str(self.mservice_id)
    
class ModuleRegistration(models.Model):
    module_name = models.CharField(max_length=250,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def str(self):
        return str(self.module_name)

class MsToModuleMapping(models.Model):
    mservice_id = models.OneToOneField(MSRegistration,on_delete=models.CASCADE,related_name='ms_id')
    module_id = models.ForeignKey(ModuleRegistration,on_delete=models.CASCADE,related_name='module_id')

    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def str(self):
        return str(self.module_id)	
    
# ============= Masters =====================
class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    registration_number = models.CharField(max_length=100)
    incorporation_date = models.DateField(blank=True,null=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class IdentificationType(models.Model):
    company_id = models.ForeignKey(Company,on_delete=models.CASCADE)
    type_name = models.CharField(max_length=100, unique=True) # passport, Adhar Card, License, Pan card
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BankAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='%(class)s_company')
    account_number = models.CharField(max_length=50, unique=True)
    account_holder_name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    nrfc_number = models.CharField(max_length=50, blank=True, null=True)  # Non-Resident Foreign Currency number
    swift_code = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_number}"

class Currency(models.Model):
	company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
	code = models.CharField(max_length=3)
	name = models.CharField(max_length=50)
	symbol = models.CharField(max_length=5, blank=True, null=True)
	exchange_rate = models.DecimalField(max_digits=10, decimal_places=4,)
	is_active = models.BooleanField(default=False,)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

class PaymentMethod(models.Model):
	company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
	method_name = models.CharField(max_length=50) # Bank Transfer,Credit/Debit Card,Cash,Mobile Payment Solutions(mobile apps),Checks
	description = models.TextField( blank=True,null=True)
	is_active = models.BooleanField(default=False,)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)   

class LoanType(models.Model):
    DISBURSEMENT_BENEFICIARY_CHOICES = [
        ('pay_self', 'Pay Self'),
        ('pay_milestone', 'Pay Milestone'),
    ]
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    loantype_id = models.CharField(max_length=50,unique = True)
    loantype = models.CharField(max_length=100) # personal loan, housing loan
    disbursement_beneficiary = models.CharField(max_length=20,choices=DISBURSEMENT_BENEFICIARY_CHOICES,default='pay_self') # 
    description = models.TextField(blank = True,null =True)
    interest_rate = models.FloatField(default = 0.0) # percentage
    loan_teams = models.IntegerField() # Standard loan term duration for this type, in months.
    min_loan_amt = models.FloatField(default = 0.0)
    max_loan_amt = models.FloatField(default = 0.0)
    eligibility = models.TextField() # Conditions a borrower must meet to qualify for this loan with customer income.
    collateral_required = models.BooleanField(default=False)
    charges = models.TextField() # Any associated fees like processing or administration fees.
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

# Collateral Type Master Table
class CollateralType(models.Model):
	company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
	name = models.CharField(max_length=100) # Real Estate, vehicle, saving account
	description = models.TextField(blank=True, null=True)
	category = models.CharField(max_length=50,choices= [
		('Tangible','Tangible'), # tangible is physical asset like own property or own bike etc
		('Intangible','Intangible'), # intangible is non-physical assets like parents, trademarks
		('Financial','Financial'), # financial assets like stocks, bonds, and certificates
	])
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

#================== Processing =====================
class Customer(models.Model):
    EMPLOYMENT_STATUS = [
        ('Employed','Employed'), # The borrower has a job and receives a regular income.
		('Unemployed','Unemployed'), # The borrower is currently without a job and does not have a source of income.
		('Self_Employed','Self-Employed'), # The borrower works for themselves, such as owning a business or freelancing.
        ('Part_Time','Part-Time'), # The borrower works less than full-time hours.
        ('Retired','Retired'), # The borrower is no longer working and may be relying on retirement income.
        ('Student','Student'), #  The borrower is currently enrolled in an educational institution.
        ('Other','Other'), # Any other status that doesn’t fit into the above categories.
    ]
    company_id = models.ForeignKey(Company,on_delete=models.CASCADE)
    customer_id = models.CharField(max_length=20,unique=True)
    firstname = models.CharField(max_length=20)
    lastname = models.CharField(max_length=50,blank=True,null=True)
    email = models.EmailField()
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    dateofbirth = models.DateField()
    customer_income = models.FloatField(default = 0.0) # monthly income
    credit_score = models.IntegerField(default=651)
    employment_status = models.CharField(max_length=100,choices=EMPLOYMENT_STATUS)
    existing_liabilities = models.FloatField(default=0.0) # Stores the result of the eligibility check. mean previous loan outstanding amount
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     
    def __str__(self):
        return self.customer_id

class CustomerDocuments(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE, related_name='%(class)s_customers')
    documentid = models.CharField(max_length=20,unique=True)
    document_type = models.ForeignKey(IdentificationType,on_delete=models.CASCADE, related_name='%(class)s_document_type')
    documentfile = models.FileField(upload_to='documents/' ,blank=True,null=True )
    uploaded_at = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class LoanCalculators(models.Model):
	loan_amount = 	models.FloatField(default = 0.0) # principal amount
	interest_rate = models.FloatField(default = 0.0) # 
	tenure = models.IntegerField(help_text="Tenure in days/weeks/months/years depending on the schedule.") # number of month
	tenure_type = models.CharField(max_length=100,choices=[
		('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')])
	repayment_schedule = models.CharField(max_length=100,choices=[('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('halfyearly', 'Half Yearly'),
        ('annually', 'Annually'),
        ('one_time', 'One Time'),]) # 
	repayment_mode = models.CharField(max_length=100,choices=[
        ('principal_only', 'Principal Only'),
        ('interest_only', 'Interest Only'),
        ('both', 'Principal and Interest'),
        ('interest_first', 'Interest First, Principal Later'),
        ('principal_end', 'Principal at End, Interest Periodically'),
    ])
	interest_basics = models.CharField(max_length=100,choices=[
        ('365', '365 Days Basis'),
        ('other', 'Other Basis'),
    ])
	loan_calculation_method = models.CharField(max_length=150,choices=[
        ('reducing_balance', 'Reducing Balance Method'),
        ('flat_rate', 'Flat Rate Method'),
        ('constant_repayment', 'Constant Repayment (Amortization)'),
        ('simple_interest', 'Simple Interest'),
        ('compound_interest', 'Compound Interest'),
        ('graduated_repayment', 'Graduated Repayment'),
        ('balloon_payment', 'Balloon Payment'),
        ('bullet_repayment', 'Bullet Repayment'),
        ('interest_first', 'Interest-Only Loans'),
    ])
	repayment_start_date = models.DateField()
	created_at = models.DateField(auto_now=True)
	updated_at = models.DateField(auto_now=True)

class LoanApplication(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    application_id = models.CharField(max_length=20,unique=True)
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)
    loantype = models.ForeignKey(LoanType,on_delete=models.CASCADE, related_name='%(class)s_loantype') # personal loan etc
    loan_amount = models.FloatField(default=0.0) # requested amount
    loan_purpose = models.TextField()
    application_status = models.CharField(max_length=100,choices=[
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
        ])  # application approval status
    interest_rate = models.FloatField(default=0.0)  #
    tenure_type = models.CharField(max_length=100,choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')])
    tenure = models.IntegerField(help_text="Duration of the loan in months") # Duration of the loan in months
    disbursement_type = models.CharField(max_length=50, choices=[('one_off', 'One-Off'), ('trenches', 'Trenches')]) # one off - mean  entire loan amount to the borrower at once.  trenches-  the loan funds in multiple installments (or "tranches") over time, often based on specific criteria or project milestones.
    repayment_schedule = models.CharField(max_length=100,choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('halfyearly', 'Half Yearly'),
        ('annually', 'Annually'),
        ('one_time', 'One Time')])
    repayment_mode = models.CharField(max_length=100,choices=[
        ('principal_only', 'Principal Only'),
        ('interest_only', 'Interest Only'),
        ('both', 'Principal and Interest'),
        ('interest_first', 'Interest First, Principal Later'),
        ('principal_end', 'Principal at End, Interest Periodically'),
    ])
    interest_basics = models.CharField(max_length=100,choices=[
        ('365', '365 Days Basis'),
        ('other', 'Other Basis'),
    ])
    loan_calculation_method = models.CharField(max_length=150,choices=[
        ('reducing_balance', 'Reducing Balance Method'),
        ('flat_rate', 'Flat Rate Method'),
        ('constant_repayment', 'Constant Repayment (Amortization)'),
        ('simple_interest', 'Simple Interest'),
        ('compound_interest', 'Compound Interest'),
        ('graduated_repayment', 'Graduated Repayment'),
        ('balloon_payment', 'Balloon Payment'),
        ('bullet_repayment', 'Bullet Repayment'),
        ('interest_first', 'Interest-Only Loans'),
    ])

    repayment_start_date = models.DateField()
    applied_at = models.DateField(auto_now=True) # application date
    approved_at = models.DateField(blank=True,null=True) # loan application approved date
    rejected_reason = models.TextField(blank=True,null=True) # loan rejected reason
    description = models.TextField(blank=True, null=True)
    workflow_stats = models.CharField(max_length=50,choices=[
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Borrower_Approved','Borrower Approved'), # loan agreement screen
        ('Lender_Approved','Lender Approved'),
        ('Borrower_and_Lender_Approved', 'Borrower and Lender Approved'),
        ('Borrower_Rejected', 'Borrower Rejected'),
        ('Agreement_completed','Agreement_completed'),
        ('Agreement_dined','Agreement_dined'),
        ('Disbursment', 'Disbursment'),
        ('Processing', 'Processing'),
        ('Loan Closed', 'Loan Closed'),
        ])
    is_active = models.BooleanField(default=False)
    is_eligible = models.BooleanField(default=False) # customer eligible checking
    eligible_rejection_reason = models.TextField(null=True, blank=True)
    checked_on = models.DateTimeField(null=True, blank=True)
    risk_score = models.FloatField(default=0.0, null=True, blank=True)  # E.g., from 0.00 to 100.00
    risk_factor = models.TextField(null=True, blank=True)  # To store detailed risk factors as text
    document_verified = models.BooleanField(default=False) # loan customer documents verifications(update in document verification screen)
    document_verified_datetime = models.DateTimeField(null=True, blank=True) # (update in document verification screen)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Loan(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE, related_name='%(class)s_customer')
    loanapp_id = models.ForeignKey(LoanApplication,on_delete=models.CASCADE, related_name='%(class)s_loanapp')
    loan_id = models.CharField(max_length=20, unique=True)
    loan_amount = models.FloatField(default = 0.0)
    approved_amount = models.FloatField(default = 0.0)
    interest_rate = models.FloatField(default = 0.0)
    disbursement_amount = models.FloatField(default = 0.0) # total disbursement amount
    tenure = models.IntegerField()  # In months
    tenure_type = models.CharField(max_length=100,choices=[
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')])
    repayment_schedule = models.CharField(max_length=100,choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('halfyearly', 'Half Yearly'),
        ('annually', 'Annually'),
        ('one_time', 'One Time')])
    repayment_mode = models.CharField(max_length=100,choices=[
        ('principal_only', 'Principal Only'),
        ('interest_only', 'Interest Only'),
        ('both', 'Principal and Interest'),
        ('interest_first', 'Interest First, Principal Later'),
        ('principal_end', 'Principal at End, Interest Periodically'),
    ])
    interest_basics = models.CharField(max_length=100,choices=[
        ('365', '365 Days Basis'),
        ('other', 'Other Basis'),
    ])
    loan_calculation_method = models.CharField(max_length=150,choices=[
        ('reducing_balance', 'Reducing Balance Method'),
        ('flat_rate', 'Flat Rate Method'),
        ('constant_repayment', 'Constant Repayment (Amortization)'),
        ('simple_interest', 'Simple Interest'),
        ('compound_interest', 'Compound Interest'),
        ('graduated_repayment', 'Graduated Repayment'),
        ('balloon_payment', 'Balloon Payment'),
        ('bullet_repayment', 'Bullet Repayment'),
        ('interest_first', 'Interest-Only Loans'),
    ])
    loan_purpose = models.TextField()
    paid_amount = models.FloatField(default = 0.0)
    lender = models.ForeignKey(User, related_name='lender', on_delete=models.CASCADE,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending') # loan agreement status
    workflow_stats = models.CharField(max_length=50,choices=[
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Borrower_Approved','Borrower Approved'), # loan agreement screen
        ('Lender_Approved','Lender Approved'),
        ('Borrower_and_Lender_Approved', 'Borrower and Lender Approved'),
        ('Borrower_Rejected', 'Borrower Rejected'),
        ('Agreement_completed','Agreement_completed'),
        ('Agreement_dined','Agreement_dined'),
        ('Disbursment', 'Disbursment'),
        ('Processing', 'Processing'),
        ('Loan Closed', 'Loan Closed'),
        ])
    is_eligible = models.BooleanField(default=False) # customer eligible checking
    eligible_rejection_reason = models.TextField(null=True, blank=True)
    checked_on = models.DateTimeField(null=True, blank=True)
    risk_score = models.FloatField(default=0.0, null=True, blank=True)  # E.g., from 0.00 to 100.00
    risk_factor = models.TextField(null=True, blank=True)  # To store detailed risk factors as text
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"Loan {self.loan_id}"

class ValueChainSetUps(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=100,unique=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    valuechain_name = models.CharField(max_length=500)
    max_amount  = models.FloatField(default= 0.0)
    min_amount = models.FloatField(default=0.0)
    description = models.TextField(blank=True,null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    def __str__(self):
        return f"{self.valuechain_name}"

class MilestoneSetUp(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=100,unique=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    valuechain_id = models.ForeignKey(ValueChainSetUps,on_delete=models.CASCADE)
    milestone_name = models.CharField(max_length=500)
    max_amount  = models.FloatField(default=0.0)
    min_amount = models.FloatField(default=0.0)
    description = models.TextField(blank=True,null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    def __str__(self):
        return f"{self.milestone_name}"

class MilestoneStagesSetup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    milestone_id = models.ForeignKey(MilestoneSetUp,on_delete=models.CASCADE)
    stage_name = models.CharField(max_length=500)
    min_amount = models.FloatField(default=0.0)  # Amount allocated for this stage
    max_amount = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)  # Optional description of the stage
    sequence = models.PositiveIntegerField(default = 1)  # Order of the stage in the milestone
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

# actual value chain for loan application
class LoanValuechain(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE,related_name = '%(class)s_loan')
    unique_id = models.CharField(max_length=100,unique=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    valuechain_name = models.CharField(max_length=500)
    amount  = models.FloatField(default= 0.0)
    description = models.TextField(blank=True,null=True)
    start_date = models.DateField(blank=True, null=True)  # Optional start date
    end_date = models.DateField(blank=True, null=True)  # Optional end date
    active = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)  # Expected completion date
    actual_completion_date = models.DateField(blank=True, null=True)  # When milestone was completed
    sequence = models.PositiveIntegerField()  # Order of milestones
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    def __str__(self):
        return f"{self.valuechain_name}"
     
class LoanMilestone(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE,related_name = '%(class)s_loan')
    unique_id = models.CharField(max_length=100,unique=True)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    valuechain_id = models.ForeignKey(LoanValuechain,on_delete=models.CASCADE)
    milestone_name = models.CharField(max_length=500)
    max_amount  = models.FloatField(default=0.0)
    description = models.TextField(blank=True,null=True)
    active = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)  # Expected completion date
    actual_completion_date = models.DateField(blank=True, null=True)  # When milestone was completed
    sequence = models.PositiveIntegerField()  # Order of milestones
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    def __str__(self):
        return f"{self.milestone_name}"

class LoanMilestoneStages(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE,related_name = '%(class)s_loan')
    milestone_id = models.ForeignKey(LoanMilestone,on_delete=models.CASCADE)
    stage_name = models.CharField(max_length=500)
    min_amount = models.FloatField(default=0.0)  # Amount allocated for this stage
    max_amount = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)  # Optional description of the stage
    sequence = models.PositiveIntegerField(default = 0)  # Order of the stage in the milestone
    start_date = models.DateField(blank=True, null=True)  # Optional start date
    end_date = models.DateField(blank=True, null=True)  # Optional end date
    status = models.CharField(
        max_length=50, 
        choices=[("Pending", "Pending"), ("In Progress", "In Progress"), ("Completed", "Completed")], 
        default="Pending"
    )  # Stage status
    actual_completion_date = models.DateField(blank=True, null=True)  # Completion date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 


    
# This is the main account for tracking principal, interest, and penalties for each loan
class LoanAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    account_no = models.CharField(max_length=50)
    loan = models.OneToOneField(Loan, on_delete = models.CASCADE, related_name="loan_detail5")
    principal_amount = models.FloatField(default = 0.0)
    interest_amount = models.FloatField(default = 0.0)
    penalty_amount = models.FloatField(default = 0.0)
    outstanding_balance = models.FloatField(default = 0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan Account for {self.loan.id}"
    
# This model tracks the disbursement of funds for each loan. each loan have disbursement account
class LoanDisbursementAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    account_no = models.CharField(max_length=50)
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail4")
    amount = models.FloatField(default=0.0)
    milestone_account = models.ForeignKey('MilestoneAccount', on_delete=models.SET_NULL, null=True, blank=True)
    loan_account = models.ForeignKey('LoanAccount', on_delete=models.SET_NULL, null=True, blank=True)
    disbursement_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending', choices=[('pending', 'Pending'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Disbursement for Loan {self.loan}"

# This model handles all repayments made by the borrower.
class LoanRepaymentAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    account_no = models.CharField(max_length=50)
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail3")
    repayment_date = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField(default=0.0)
    payment_method = models.CharField(max_length=50, choices=[('bank_transfer', 'Bank Transfer'), ('cash', 'Cash')])
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Repayment for Loan {self.loan.id}"
    


# This is the main account for tracking principal, interest, and penalties for each loan
class PenaltyAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    account_no = models.CharField(max_length=50)
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail2")
    penalty_date = models.DateTimeField(auto_now_add=True)
    penalty_amount = models.FloatField(default=0.0)
    penalty_reason = models.TextField()
    status = models.CharField(max_length=50, default='unpaid', choices=[('unpaid', 'Unpaid'), ('paid', 'Paid')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Penalty for Loan {self.loan.id}"

# This handles the recording of interest accruals and payments.
class InterestAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    account_no = models.CharField(max_length=50)
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail")
    interest_accrued = models.FloatField(default=0.0)
    interest_payment_date = models.DateField(null=True, blank=True)
    interest_payment_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Interest Account for Loan {self.loan.id}"

# This tracks disbursements made to specific milestones if the loan is based on milestones.
class MilestoneAccount(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail1")
    milestone_header = models.ForeignKey('LoanValuechain', on_delete=models.CASCADE)  # This is the value chain or scheme-based identifier
    milestone_cost = models.FloatField(default=0.0)
    disbursement_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending', choices=[('pending', 'Pending'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Milestone Account for Loan {self.loan.id}"

# This captures the complete loan transaction history from disbursement to repayment, interest, and penalties.
class LoanEntry(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="loan_detail7")
    transaction_type = models.CharField(max_length=50, choices=[('disbursement', 'Disbursement'), ('repayment', 'Repayment'), ('penalty', 'Penalty'), ('interest', 'Interest')])
    amount = models.FloatField(default=0.0)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction {self.transaction_type} for Loan {self.loan.id}"

class LoanAgreement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_company')
    agreement_id = models.CharField(max_length=20, unique=True)
    loan_id = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='%(class)s_loan_id')
    loanapp_id = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='%(class)s_loanapp_id')
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='%(class)s_customer_id')
    agreement_terms = models.TextField(blank=True, null=True)
    agreement_date = models.DateTimeField(auto_now_add=True)
    borrower_signature = models.FileField(upload_to='signatures/borrowers/', blank=True, null=True)
    lender_signature = models.FileField(upload_to='signatures/lenders/', blank=True, null=True)
    signed_at = models.DateTimeField(blank=True, null=True)
    agreement_status = models.CharField(max_length=70, choices=[
        ('Active', 'Active'),
        ('Terminated', 'Terminated'),
        ('Completed', 'Completed'),
    ])
    disbursement_approval = models.CharField(max_length=70, choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Denied', 'Denied'),
        ('Approved', 'Approved'),
    ],default='Active')
    disburse_reject_reason = models.TextField(blank=True, null=True)
    maturity_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Disbursement(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='%(class)s_company')
    disbursement_id = models.CharField(max_length=50,unique=True)
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE, related_name='%(class)s_customer_id')
    loan = models.ForeignKey(Loan,on_delete=models.CASCADE, related_name='%(class)s_loan')
    loan_application = models.ForeignKey(LoanApplication,on_delete=models.CASCADE, related_name='%(class)s_loan_application')
    disbursement_date = models.DateField(auto_now=True)
    amount = models.FloatField(default=0.0)
    disbursement_type = models.CharField(max_length=50,choices=[
        ('one_off', 'One-Off'), 
        ('trenches', 'Trenches')
    ])
    disbursement_status = models.CharField(max_length=50,choices=[
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
    ])
    disbursement_method = models.CharField(max_length=50, choices=[
        ('direct_deposit', 'Direct Deposit'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('prepaid_card','Prepaid Card'),
        ('Third-Party','Third-Party')
    ])
    bank = models.ForeignKey(BankAccount,on_delete=models.CASCADE,blank=True,null=True)
    currency = models.ForeignKey(Currency,on_delete=models.CASCADE)
    notes = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RepaymentSchedule(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='%(class)s_company')
    loan_application = models.ForeignKey(LoanApplication,on_delete=models.CASCADE,related_name='%(class)s_loan_application')
    loan_id = models.ForeignKey(Loan,on_delete=models.CASCADE,blank=True,null=True)
    period = models.IntegerField(default=0)
    schedule_id = models.CharField(max_length=50)
    repayment_date = models.DateField()
    instalment_amount = models.FloatField(default = 0.0)
    paid_amount = models.FloatField(default = 0.0)
    principal_amount = models.FloatField(default = 0.0)
    interest_amount = models.FloatField(default = 0.0)
    remaining_balance = models.FloatField(default = 0.0)
    repayment_status = models.CharField(max_length = 50,choices = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ],default="Pending")
    payment_method = models.ForeignKey(PaymentMethod,on_delete=models.CASCADE,related_name='%(class)s_payment_method',blank=True,null=True)
    transaction_id = models.CharField(max_length=50,blank=True,null=True)
    notes = models.TextField(blank=True,null=True)
    confirmed_status = models.CharField(max_length=50,choices = [
        ('Confirmed', 'Confirmed'),
        ('Pending', 'Pending'),
    ],default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payments(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=50,unique=True)
    loan_id = models.ForeignKey(Loan,on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0)
    payment_date = models.DateField(auto_now=True)
    payment_method = models.ForeignKey(PaymentMethod,on_delete=models.CASCADE)
    transaction_refference = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Penalties(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='%(class)s_company')
    penalty_id = models.CharField(max_length=50,unique=True)
    loan_application = models.ForeignKey(LoanApplication,on_delete=models.CASCADE,related_name='%(class)s_loan_application')
    repaymentschedule_id = models.ForeignKey(RepaymentSchedule,on_delete=models.CASCADE,related_name='%(class)s_repaymentschedule_id')
    panalty_date = models.DateField(auto_now=True)
    penalty_amount = models.FloatField(default=0.0)
    penalty_reason = models.CharField(max_length=50,choices = [
        ('Late Payment', 'Late Payment'),
        ('Missed Payment', 'Missed Payment'),
    ])
    payment_status = models.CharField(max_length=50,choices = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
    ])
    transaction_refference = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class LoanClosure(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    closure_id = models.CharField(max_length=50,unique=True)
    loanapp_id = models.ForeignKey(LoanApplication,on_delete=models.CASCADE)
    closure_date = models.DateField()
    closure_amount = models.FloatField(default=0.0)
    remaining_balance = models.FloatField(default=0.0)
    closure_method = models.CharField(max_length=50,choices = [
        ('lump sum Payment', 'lump sum Payment'),
        ('Refinancing', 'Refinancing'),
    ])
    closure_reason = models.TextField()
    transaction_refference = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Collaterals(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    collateral_id = models.CharField(max_length=20,unique=True)
    loanapp_id = models.ForeignKey(LoanApplication,on_delete=models.CASCADE)
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)
    collateral_type = models.ForeignKey(CollateralType,on_delete=models.CASCADE)
    collateral_value = models.FloatField(default = 0.0,help_text="Monetary value of the collateral") 
    valuation_date = models.DateField()
    collateral_status = models.CharField(max_length=50,choices=[
        ('Held', 'Held'),
        ('Released', 'Released'),
        ('Sold', 'Sold'),
    ])
    insurance_status = models.CharField(max_length=50,choices=[
        ('Insured', 'Insured'),
        ('Not insured', 'Not insured'),
    ])
    borrower_signature = models.FileField(upload_to='borrower_signatures/', blank=True, null=True, help_text="Upload borrower signature document.")
    description = models.TextField(blank=True, null=True, help_text="A brief description of the collateral.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CollateralDocuments(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    application_id = models.ForeignKey(LoanApplication,on_delete=models.CASCADE)
    document_name = models.CharField(max_length=100)
    additional_documents = models.FileField(upload_to='additional_documents/', blank=True, null=True, help_text="Upload any additional documents related to the collateral.")
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

#===========================================

class Creditscores(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_company')
	scores_id = models.CharField(max_length=20)
	customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='%(class)s_customer_id')
	credit_score = models.IntegerField(blank=True,null=True) # A credit score is a three-digit number that typically ranges from 300 to 850.
	retrieved_at = models.DateField(blank=True,null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

class LoanOffer(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    offer_id = models.CharField(max_length=20,unique=True)
    application_id = models.ForeignKey(LoanApplication,on_delete=models.CASCADE)
    loanamount = models.FloatField(default=0.0)
    interest_rate = models.FloatField(default = 0.0)
    tenure = models.IntegerField(help_text="Duration of the loan in months")
    monthly_instalment = models.FloatField(default = 0.0)
    terms_condition = models.TextField(null=True, blank=True)
    offer_status = models.CharField(max_length=50,choices=[
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class SupportTickets(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    ticket_id = models.CharField(max_length=50,unique=True)
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)
    subject = models.TextField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=50,choices= [
        ('Open', 'Open'),
        ('In-progress', 'In-progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ])
    priority = models.CharField(max_length=50,choices= [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ])
    assigned_to = models.CharField(max_length=50,blank=True,null=True)
    resolution = models.CharField(max_length=50)
    resolution_date = models.DateField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CustomerFeedBack(models.Model):
    feedback_id = models.CharField(max_length=50,unique=True)
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)
    feedback_date = models.DateField(blank=True,null=True)
    feedback_type = models.CharField(max_length=50,choices=  [
        ('Complaint', 'Complaint'),
        ('Suggestion', 'Suggestion'),
        ('Compliment', 'Compliment'),
    ])
    subject = models.CharField(max_length=50)
    description = models.TextField(blank=True,null=True)
    feedback_status = models.CharField(max_length=50)


class Notifications(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_company')
	notification_id = models.CharField(max_length=20)
	customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='%(class)s_customer_id')
	message = models.TextField()
	status = models.CharField(max_length=20)
	priority = models.CharField(max_length=20)





#===============DMS===================

class CustomDocumentEntity(models.Model):
	entity_id = models.CharField(max_length=100, unique=True)
	entity_name = models.CharField(max_length=100)
	type=[
		('loan','loan'),
	]
	entity_type = models.CharField(max_length=100,choices=type)
	description = models.TextField(blank=True,null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocEntityType_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="DocEntityType_update_by")
	update_at = models.DateTimeField(auto_now=True)

	# def __str__(self):
	# 	return self.entity_id

class FolderMaster(models.Model):
	folder_id=models.CharField(max_length=100, unique=True,blank=False,null=False)
	folder_name=models.CharField(max_length=100,blank=False,null=False)
	description = models.TextField(max_length=500,blank=True, null=True)
	entity=models.ForeignKey(CustomDocumentEntity, on_delete=models.CASCADE)
	customer=models.ForeignKey(Customer, on_delete=models.CASCADE,blank=True, null=True)
	company=models.ForeignKey(Company, on_delete=models.CASCADE,blank=True, null=True)
	master_checkbox_file = models.BooleanField(default=False, blank=True, null=True)
	parent_folder=models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='FolderMasters')
	default_folder=models.BooleanField(default=False)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="FolderMastere_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="FolderMastere_update_by")
	update_at = models.DateTimeField(auto_now=True)


class DocumentType(models.Model):
	type_name = models.CharField(max_length=100, unique=True)
	short_name = models.CharField(max_length=100)
	description = models.TextField(blank=True,null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocumentType_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="DocumentType_update_by")
	update_at = models.DateTimeField(auto_now=True)  


class DocumentCategory(models.Model):
	category_name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True,null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocumentCategory_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="DocumentCategory_update_by")
	update_at = models.DateTimeField(auto_now=True)
 
from django.db import models
import datetime

class DocumentUpload(models.Model):
	company=models.ForeignKey(Company, on_delete=models.CASCADE,blank=True, null=True)
	document_id=models.CharField(max_length=100, primary_key=True)
	document_title=models.CharField(max_length=100,blank=False,null=False)
	document_type=models.ForeignKey(IdentificationType,on_delete=models.CASCADE,blank=True, null=True)
	entity_type=models.ManyToManyField(CustomDocumentEntity,blank=True)
	folder=models.ForeignKey(FolderMaster,on_delete=models.CASCADE,blank=True, null=True)
	document_size=models.PositiveBigIntegerField(blank=True,null=True)
	description = models.TextField(blank=True, null=True)
	document_upload = models.FileField(blank=True, null=True)
	upload_date = models.DateField(blank=True, null=True, default=datetime.date.today)
	expiry_date= models.DateField(blank=True,null=True)
	start_date=models.DateField(blank=True,null=True)
	end_date=models.DateField(blank=True,null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocumentUpload_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="DocumentUpload_update_by")
	update_at = models.DateTimeField(auto_now=True)



class DocumentAccess(models.Model):
	document = models.ForeignKey(DocumentUpload,on_delete=models.CASCADE)
	access_to = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocumentAccess_access_to")
	permission = models.TextField(blank=True,null=True)
	expiry_from_at = models.DateTimeField(blank=True,null=True)
	expiry_to_at = models.DateTimeField(blank=True,null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name="DocumentAccess_created_by")
	created_at = models.DateTimeField(auto_now_add=True)
	update_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name="DocumentAccess_update_by")
	update_at = models.DateTimeField(auto_now=True)


class DocumentUploadHistory(models.Model):
	document_id=models.CharField(max_length=100,blank=False,null=False)
	document_title=models.CharField(max_length=100,blank=False,null=False)
	document_type=models.ForeignKey(IdentificationType,on_delete=models.CASCADE,blank=True, null=True)
	folder=models.ForeignKey(FolderMaster,on_delete=models.CASCADE,blank=True, null=True)
	document_size=models.PositiveBigIntegerField(blank=True,null=True)
	description = models.TextField(blank=True, null=True)
	document_upload = models.FileField(blank=True, null=True)
	upload_date = models.DateField(blank=True, null=True, default=datetime.date.today)
	expiry_date= models.DateField(blank=True,null=True)
	start_date=models.DateField(blank=True,null=True)
	end_date=models.DateField(blank=True,null=True)
	is_deactivate = models.BooleanField(default=False)
	version = models.PositiveIntegerField()



class DocumentUploadAudit(models.Model):
	document_id=models.CharField(max_length=100,blank=False,null=False)
	document_title=models.CharField(max_length=100,blank=False,null=False)
	document_type=models.ForeignKey(IdentificationType,on_delete=models.CASCADE)
	folder=models.ForeignKey(FolderMaster,on_delete=models.CASCADE,blank=True, null=True)
	document_size=models.PositiveBigIntegerField(blank=True,null=True)
	description = models.TextField(blank=True, null=True)
	document_upload = models.FileField(blank=True, null=True)
	upload_date = models.DateField(blank=True, null=True, default=datetime.date.today)
	expiry_date= models.DateField(blank=True,null=True)
	start_date=models.DateField(blank=True,null=True)
	end_date=models.DateField(blank=True,null=True)
	STATUS = (
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    )
	status = models.CharField(max_length=100, choices=STATUS)
	created_by = models.ForeignKey(User, related_name='DocumentUploadAuditAudit_created_by', on_delete=models.SET_NULL,null=True)
	updated_by = models.ForeignKey(User, related_name='DocumentUploadAuditAudit_updated_by', on_delete=models.SET_NULL,null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

#===================
    
class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    screen_name = models.CharField(max_length=50,null=True, blank=True)  #Screen Name 
    datetime = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True,blank=True)
    object_id = models.PositiveIntegerField(null=True,blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    action = models.CharField(max_length=50)  # 'create', 'update', 'delete'
    details = models.TextField(null=True, blank=True)