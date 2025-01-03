from rest_framework import serializers
from .models import *

#  ms setup serializer
class MSSerializer(serializers.Serializer):
    ms_id = serializers.CharField(max_length=100)
    ms_payload = serializers.JSONField(initial=dict)

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"

class CollateraltypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollateralType
        fields = "__all__"


class IdentificationtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentificationType
        fields = "__all__"


class PaymentmethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class CustomerAccountSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = CustomerAccount
        fields = "__all__"

class CustomerSerializer(serializers.ModelSerializer):
    company_id = CompanySerializer()

    class Meta:
        model = Customer
        fields = "__all__"


class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = "__all__"

class CustomerDocumentsSerializer(serializers.ModelSerializer):
    customer_id = CustomerSerializer()
    document_type = IdentificationtypeSerializer()
    class Meta:
        model = CustomerDocuments
        fields = "__all__"

class CreditscoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Creditscores
        fields = "__all__"


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedBack
        fields = "__all__"

class LoanapplicationSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    customer_id = CustomerSerializer()
    loantype = LoanTypeSerializer()
    class Meta:
        model = LoanApplication
        exclude = ['created_at','updated_at']

class LoanSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    loanapp_id = LoanapplicationSerializer()
    customer = CustomerSerializer()
    class Meta:
        model = Loan
        exclude = ['created_at','updated_at']


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = "__all__"


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTickets
        fields = "__all__"


class CollateralsSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    loanapp_id = LoanapplicationSerializer()
    customer_id = CustomerSerializer()
    collateral_type = CollateraltypeSerializer()
    class Meta:
        model = Collaterals
        fields = "__all__"

class CollateralDocumentsSerializer(serializers.ModelSerializer):
    application_id = LoanapplicationSerializer()
    class Meta:
        model = CollateralDocuments
        fields = "__all__"


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'


class LoanagreementSerializer(serializers.ModelSerializer):
    loan_id = LoanSerializer()
    loanapp_id = LoanapplicationSerializer()
    customer_id = CustomerSerializer()
    agreement_template=TemplateSerializer()
    class Meta:
        model = LoanAgreement
        fields = "__all__"

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"

class LoanClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanClosure
        fields = "__all__"


class PaymentsSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    loan_id = LoanSerializer()
    payment_method = PaymentmethodSerializer()
    class Meta:
        model = Payments
        fields = "__all__"
        


class DisbursementSerializer(serializers.ModelSerializer):
    customer_id = CustomerSerializer()
    loan = LoanSerializer()
    loan_application = LoanapplicationSerializer()
    bank = BankAccountSerializer()
    currency = CurrencySerializer()
    class Meta:
        model = Disbursement
        fields = "__all__"


class ValueChainSetUpsSerializer(serializers.ModelSerializer):
    loan_type = LoanTypeSerializer()
    company = CompanySerializer()
    class Meta:
        model = ValueChainSetUps
        fields = ['id','company', 'unique_id', 'loan_type', 'valuechain_name', 'max_amount', 
                  'min_amount', 'description', 'status']

class MilestoneSetUpSerializer(serializers.ModelSerializer):
    loan_type = LoanTypeSerializer()
    valuechain_id = ValueChainSetUpsSerializer()
    class Meta:
        model = MilestoneSetUp
        fields = "__all__"

class MilestoneStagesSetupSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    milestone_id = MilestoneSetUpSerializer()
    class Meta:
        model = MilestoneStagesSetup
        fields = "__all__"



class LoanOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanOffer
        fields = "__all__"

class RepaymentscheduleSerializer(serializers.ModelSerializer):
    loan_application = LoanapplicationSerializer()
    loan_id = LoanSerializer()
    company = CompanySerializer()
    class Meta:
        model = RepaymentSchedule
        fields = "__all__"

class RefinancescheduleSerializer(serializers.ModelSerializer):
    loan_application = LoanapplicationSerializer()
    loan_id = LoanSerializer()
    company = CompanySerializer()
    class Meta:
        model = RefinanceSchedule
        fields = "__all__"

class RestructurescheduleSerializer(serializers.ModelSerializer):
    loan_application = LoanapplicationSerializer()
    loan_id = LoanSerializer()
    company = CompanySerializer()
    class Meta:
        model = RestructureSchedule
        fields = "__all__"


class PenaltySerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    loan = LoanSerializer()
    repayment_schedule = RepaymentscheduleSerializer()
    class Meta:
        model = Penalty
        fields = "__all__"

class CustomDocumentEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDocumentEntity
        exclude = ('created_by','created_at','update_by','update_at')


class FolderMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderMaster
        exclude = ('created_by','created_at','update_by','update_at')
        
class FolderMasterSerializer(serializers.ModelSerializer):
    parent_folder=FolderMasterSerializer()
    class Meta:
        model = FolderMaster
        fields = '__all__' 



class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'  

class FolderMasterSerializer1(serializers.ModelSerializer):
    class Meta:
        model = FolderMaster
        exclude = ('created_by','created_at','update_by','update_at')

class DocumentUploadHistorySerializer(serializers.ModelSerializer):
    folder=FolderMasterSerializer1() 
    document_type = IdentificationtypeSerializer()
    class Meta:
        model = DocumentUploadHistory
        fields = '__all__'       


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'       
class LoanAccountSerializer(serializers.ModelSerializer):
    loan = LoanSerializer()
    class Meta:
        model = LoanAccount
        fields = '__all__'    

class LoanDisbursementAccountSerializer(serializers.ModelSerializer):
    loan = LoanSerializer()
    class Meta:
        model = LoanDisbursementAccount
        fields = '__all__'     

class LoanRepaymentAccountSerializer(serializers.ModelSerializer):
    loan = LoanSerializer()
    class Meta:
        model = LoanRepaymentAccount
        fields = '__all__'     

class PenaltyAccountSerializer(serializers.ModelSerializer):
    loan = LoanSerializer()
    class Meta:
        model = PenaltyAccount
        fields = '__all__'     

class InterestAccountSerializer(serializers.ModelSerializer):
    loan = LoanSerializer()
    class Meta:
        model = InterestAccount
        fields = '__all__'     

class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = '__all__'    


class LoanValuechainSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanValuechain
        fields = '__all__'

class LoanMilestoneStagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanMilestoneStages
        fields = '__all__'

class LoanMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanMilestone
        fields = '__all__'
