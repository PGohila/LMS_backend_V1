from django.contrib import admin
from .models import *

@admin.register(MSRegistration)
class MSRegistrationAdmin(admin.ModelAdmin):
    list_display = ['mservice_id', 'mservice_name', 'is_authenticate']

@admin.register(ModuleRegistration)
class ModuleRegistrationAdmin(admin.ModelAdmin):
    list_display = ['module_name']

@admin.register(MsToModuleMapping)
class MsToModuleMappingAdmin(admin.ModelAdmin):
    list_display = ['mservice_id','module_id']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['loantype', 'interest_rate', 'is_active']
    
@admin.register(CollateralType)
class CollateraltypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    
@admin.register(IdentificationType)
class IdentificationtypeAdmin(admin.ModelAdmin):
    list_display = ['type_name', 'description', 'is_active']
    
@admin.register(PaymentMethod)
class PaymentmethodAdmin(admin.ModelAdmin):
    list_display = ['method_name', 'description', 'is_active']
    
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_active']
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['company_id', 'customer_id', 'firstname', 'lastname', 'email', 'phone_number', 'address', 'dateofbirth', 'expiry_date', 'is_active']
    
@admin.register(CustomerDocuments)
class CustomerdocumentsAdmin(admin.ModelAdmin):
    list_display = ['company', 'documentid', 'document_type', 'uploaded_at',]
    
@admin.register(Creditscores)
class CreditscoresAdmin(admin.ModelAdmin):
    list_display = ['company', 'scores_id', 'customer_id', 'credit_score', 'retrieved_at']
    
@admin.register(CustomerFeedBack)
class CustomerfeedbackAdmin(admin.ModelAdmin):
    list_display = ['feedback_id', 'customer_id', 'feedback_date', 'feedback_type', 'subject', 'description', 'feedback_status']
    
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['company', 'loanapp_id','loan_id', 'loan_amount', 'interest_rate']
    
@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['company', 'notification_id', 'customer_id', 'message', 'status', 'priority']
    
@admin.register(SupportTickets)
class SupportticketsAdmin(admin.ModelAdmin):
    list_display = ['company', 'ticket_id', 'customer_id', 'subject', 'description', 'status', 'priority', 'assigned_to', 'resolution', 'resolution_date']
    
@admin.register(CollateralDocuments)
class CollateralDocumentsAdmin(admin.ModelAdmin):
    list_display = ['company', 'application_id', 'document_name', 'additional_documents', 'description']

@admin.register(Collaterals)
class CollateralsAdmin(admin.ModelAdmin):
    list_display = ['company', 'collateral_id', 'loanapp_id', 'customer_id', 'collateral_type', 'collateral_value', 'valuation_date', 'collateral_status', 'insurance_status']


@admin.register(LoanAgreement)
class LoanagreementAdmin(admin.ModelAdmin):
    list_display = ['company', 'agreement_id', 'loanapp_id', 'customer_id','signed_at', 'agreement_date', 'borrower_signature', 'agreement_status', 'lender_signature', 'maturity_date']
    
@admin.register(LoanClosure)
class LoanclosureAdmin(admin.ModelAdmin):
    list_display = ['company', 'closure_id', 'loanapp_id', 'closure_date', 'closure_amount', 'remaining_balance', 'closure_method', 'closure_reason', 'transaction_refference']
    
@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ['company', 'payment_id', 'loan_id', 'amount', 'payment_date', 'payment_method', 'transaction_refference']
    
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['company', 'application_id', 'customer_id', 'loan_amount', 'loan_purpose', 'application_status', 'interest_rate', 'tenure', 'applied_at', 'approved_at']
    
@admin.register(Disbursement)
class DisbursementAdmin(admin.ModelAdmin):
    list_display = ['company', 'disbursement_id', 'loan_application', 'customer_id', 'disbursement_date', 'amount', 'disbursement_type', 'disbursement_status', 'currency', 'notes']
    
@admin.register(LoanOffer)
class LoanofferAdmin(admin.ModelAdmin):
    list_display = ['company', 'offer_id', 'application_id', 'loanamount', 'interest_rate', 'tenure', 'monthly_instalment', 'terms_condition', 'offer_status']
    
@admin.register(RepaymentSchedule)
class RepaymentscheduleAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan_application', 'repayment_date', 'instalment_amount', 'principal_amount', 'interest_amount', 'remaining_balance', 'repayment_status', 'payment_method', 'transaction_id', 'notes']
    
@admin.register(Penalties)
class PenaltiesAdmin(admin.ModelAdmin):
    list_display = ['company', 'penalty_id','loan_application', 'repaymentschedule_id', 'panalty_date', 'penalty_amount', 'penalty_reason', 'payment_status', 'transaction_refference']

@admin.register(LoanAccount)
class LoanAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan', 'principal_amount', 'interest_amount', 'penalty_amount', 'outstanding_balance']
    
@admin.register(LoanDisbursementAccount)
class LoanDisbursementAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan','amount', 'milestone_account', 'loan_account']

@admin.register(LoanRepaymentAccount)
class LoanRepaymentAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan', 'repayment_date', 'amount', 'payment_method', 'transaction_reference']
    
@admin.register(PenaltyAccount)
class PenaltyAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan','penalty_date', 'penalty_amount', 'penalty_reason', 'status']

@admin.register(InterestAccount)
class InterestAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan', 'interest_accrued', 'interest_payment_date', 'interest_payment_amount']
    
@admin.register(MilestoneAccount)
class MilestoneAccountAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan','milestone_header', 'milestone_cost', 'disbursement_date', 'status']

@admin.register(LoanEntry)
class LoanEntryAdmin(admin.ModelAdmin):
    list_display = ['company', 'loan','transaction_type', 'amount', 'transaction_date', 'transaction_reference']  


admin.site.register (CustomDocumentEntity)
admin.site.register (FolderMaster)
admin.site.register (DocumentType)
admin.site.register (Department)
admin.site.register (DocumentCategory)
admin.site.register (DocumentUpload)
admin.site.register (DocumentAccess)
admin.site.register (DocumentUploadHistory)
admin.site.register (DocumentUploadAudit)
admin.site.register (AuditTrail)