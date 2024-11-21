import base64
from django.core.exceptions import ValidationError

from lms_backend import settings
from mainapp.common import log_audit_trail
from mainapp.dms import create_entity, create_folder_for_all_customer, document_upload_audit, document_upload_history, is_valid_current_datetime, unique_id_generate_doc
from .models import *
from .serializers import *
from .middleware import get_current_request
from .scripts import *
from decimal import Decimal,getcontext
from django.utils import timezone
from datetime import timedelta,datetime
from dateutil.relativedelta import relativedelta
from .loan_calculation import *
from django.shortcuts import get_object_or_404
def create_company(name,address,email,phone,registration_number,is_active=False, description = None,incorporation_date = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        instance = Company.objects.create(
            name=name,
            description=description,
            address = address,
            email = email,
            phone = phone,
            registration_number = registration_number,
            incorporation_date = incorporation_date,
            is_active=is_active,
        )
        create_entity(entity_name=name,entity_type="loan")

        try:
            log_audit_trail(request.user.id,'Company Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f'Successfully created {instance}')
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return error(f"Validation Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        return error(f"An error occurred: {e}")

def update_company(company_id,address,email,phone,registration_number,name=None, description=None,incorporation_date=None, is_active=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Company.objects.get(pk=company_id)
        instance.address = address
        instance.email = email
        instance.phone = phone
        instance.registration_number = registration_number
        instance.name = name if name is not None else instance.name
        instance.description = description if description is not None else instance.description
        instance.incorporation_date = incorporation_date if incorporation_date is not None else instance.incorporation_date
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'Company Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success('Successfully Updated')
    except  Company.DoesNotExist:
        print("Instance does not exist")
        return error('Instance does not exist')
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return error(f"Validation Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        return error(f"An error occurred: {e}")

def view_company(company_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None:
            record = Company.objects.get(pk=company_id)
            serializer = CompanySerializer(record)
        else:
            records = Company.objects.all()
            serializer = CompanySerializer(records, many=True)
        return success(serializer.data)
    
    except Company.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Company does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_company(company_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Company.objects.get(pk=company_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Company Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success("Successfully deleted")
    
    except Company.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred:{e}")

def create_customer(company_id, firstname, lastname, email, phone_number, address, dateofbirth,age, customer_income, expiry_date, is_active):
    """ ============== Customer Creation ==================="""
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')    

        if company_id is not None: 
            Company.objects.get(pk=company_id)


        # generate Unique id 
        generate_id = Customer.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.customer_id[9:]
        customer_id = unique_id('CM',last_id)

        instance = Customer.objects.create(
            company_id_id = company_id,
            customer_id = customer_id,
            firstname = firstname,
            lastname = lastname,
            email = email,
            phone_number = phone_number,
            address = address,
            dateofbirth = dateofbirth,
            age = age,
            customer_income = customer_income,
         
            expiry_date = expiry_date,
            is_active = is_active,
        )
        customer_id=instance.id
        print("customer_id34567890",customer_id)
        create_folder_for_all_customer(customer_id,company_id)

        try:
            log_audit_trail(request.user.id,'Customer Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except IdentificationType.DoesNotExist:
        return error('Invalid Identificationtype ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_customer(customer_id,company_id=None, firstname=None, lastname=None,age=None, email=None, phone_number=None, address=None,customer_income=None, dateofbirth=None, expiry_date=None, is_active=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get( pk=company_id )

        instance = Customer.objects.get(pk=customer_id)

        instance.company_id_id = company_id if company_id is not None else instance.company_id.id
        instance.firstname = firstname if firstname is not None else instance.firstname
        instance.lastname = lastname if lastname is not None else instance.lastname
        instance.email = email if email is not None else instance.email
        instance.phone_number = phone_number if phone_number is not None else instance.phone_number
        instance.address = address if address is not None else instance.address
        instance.customer_income = customer_income if customer_income is not None else instance.customer_income
        instance.dateofbirth = dateofbirth if dateofbirth is not None else instance.dateofbirth
        instance.age = age if age is not None else instance.age
        instance.expiry_date = expiry_date if expiry_date is not None else instance.expiry_date
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'Customer Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except IdentificationType.DoesNotExist:
        return error('Invalid Identificationtype ID: Destination not found.')
    except  Customer.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:    
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_customer(customer_id=None,company_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if customer_id is not None:
            record = Customer.objects.get(pk=customer_id)
            serializer = CustomerSerializer(record)
        elif company_id is not None:
            records = Customer.objects.filter(company_id_id = company_id)
            serializer = CustomerSerializer(records, many=True)
        else:
            records = Customer.objects.all()
            serializer = CustomerSerializer(records, many=True)
        return success(serializer.data)
    
    except Customer.DoesNotExist:
        return error('Customer does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def delete_customer(customer_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Customer.objects.get(pk=customer_id)
        instance.delete()
        print("instance4567u8io234567",instance)
        try:
            log_audit_trail(request.user.id,'Customer Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")        
        return success("Successfully deleted")
    
    except Customer.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_customerdocuments(company_id,customer_id, document_type_id, attachment,is_active=False,description=None):
    """ ================== customer Documentation ====================== """
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)

        if document_type_id is not None: 
            IdentificationType.objects.get(pk=document_type_id)
        
        if customer_id is not None:
            Customer.objects.get(pk=customer_id)


        # generate Unique id 
        generate_id = CustomerDocuments.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.documentid[9:]
        documentid = unique_id('CD',last_id)
         
        instance = CustomerDocuments.objects.create(
            company_id=company_id,
            customer_id_id = customer_id,
            documentid=documentid,
            document_type_id=document_type_id,
            documentfile = attachment,
            is_active = is_active,
            description = description,
 
        )

        try:
            log_audit_trail(request.user.id,'Customer Document Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except IdentificationType.DoesNotExist:
        return error('Invalid IdentificationType ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_customerdocuments(customerdocuments_id,company_id=None,customer_id=None, document_type_id=None,documentfile=None,is_active=False,description=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)

        if document_type_id is not None: 
            IdentificationType.objects.get(pk=document_type_id)

        instance = CustomerDocuments.objects.get(pk=customerdocuments_id)
        instance.company_id = company_id if company_id is not None else instance.company.id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id.id
        instance.document_type_id = document_type_id if document_type_id is not None else instance.document_type.id
        instance.documentfile = documentfile if documentfile is not None else instance.documentfile
        instance.is_active = is_active
        instance.description = description if description is not None else instance.description

        instance.save()

        try:
            log_audit_trail(request.user.id,'Customer Document Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success('Successfully Updated')
    
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except IdentificationType.DoesNotExist:
        return error('Invalid IdentificationType ID: Destination not found.')
    except  CustomerDocuments.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_customerdocuments(customerdocuments_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if customerdocuments_id is not None:
            record = CustomerDocuments.objects.get(pk=customerdocuments_id)
            serializer = CustomerDocumentsSerializer(record)

        elif company_id is not None:
            records = CustomerDocuments.objects.filter(company_id = company_id)
            serializer = CustomerDocumentsSerializer(records, many=True)
        else:
            records = CustomerDocuments.objects.all()
            serializer = CustomerDocumentsSerializer(records, many=True)
        return success(serializer.data)
    
    except CustomerDocuments.DoesNotExist:
        return error('Customerdocuments does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_verified_ducuments(company_id,customer_id=None):
    try:
        if customer_id is not None:
            records = CustomerDocuments.objects.filter(company_id = company_id,customer_id_id=customer_id)
            serializer = CustomerDocumentsSerializer(records, many=True)
        else:
            records = CustomerDocuments.objects.filter(company_id = company_id)
            serializer = CustomerDocumentsSerializer(records, many=True)

        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")


def delete_customerdocuments(customerdocuments_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = CustomerDocuments.objects.get(pk=customerdocuments_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Customer Document Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success("Successfully deleted")
    
    except CustomerDocuments.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def customerdoc_verification(customerdoc_id = None): # = customerdoc_id = Application id
    """ ========================= Customer Document Verification ======================"""
    try:
        if customerdoc_id is not None:
            customers = LoanApplication.objects.get(id = customerdoc_id)
            customers.document_verified = True
            customers.document_verified_datetime = datetime.now()
            customers.save() 
        return success("Successfully Verified")
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_loanapplication(company_id, customer_id, loan_amount,loantype_id, loan_purpose, interest_rate,loan_calculation_method,repayment_schedule,repayment_mode,interest_basics,disbursement_type, tenure,tenure_type,description,is_active,repayment_date=None):
    try:  
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)

        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)
        
        if loantype_id is not None:
            LoanType.objects.get(id = loantype_id)

        # generate Unique id 
        generate_id = LoanApplication.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.application_id[9:]
        application_id = unique_id('LA',last_id)



        instance = LoanApplication.objects.create(
            company_id = company_id,
            application_id = application_id,
            customer_id_id = customer_id,
            loantype_id = loantype_id,
            loan_amount = loan_amount,
            loan_purpose = loan_purpose,
            application_status = 'Submitted',
            loan_calculation_method = loan_calculation_method,
            repayment_schedule = repayment_schedule,
            repayment_mode = repayment_mode,
            interest_rate = interest_rate,
            disbursement_type = disbursement_type,
            interest_basics = interest_basics,
            repayment_start_date = repayment_date,
            tenure = tenure,
            tenure_type = tenure_type,
            description = description,
            workflow_stats = "Submitted",
            is_active = is_active,
        )

        try:
            log_audit_trail(request.user.id,'Loan Application Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except LoanType.DoesNotExist:
        return error('Invalid LoanType ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_loanapplication(loanapplication_id,company_id, customer_id,disbursement_type, loan_amount,loantype_id,loan_calculation_method,repayment_schedule,repayment_mode,interest_basics,loan_purpose, interest_rate, tenure,tenure_type,description,is_active,repayment_date=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)
        if loantype_id is not None:
            LoanType.objects.get(id = loantype_id)

        instance = LoanApplication.objects.get(pk=loanapplication_id)
        instance.company_id = company_id if company_id is not None else instance.company_id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id.id
        instance.loantype_id = loantype_id if loantype_id is not None else instance.loantype.id
        instance.loan_amount = loan_amount if loan_amount is not None else instance.loan_amount
        instance.repayment_schedule = repayment_schedule if repayment_schedule is not None else instance.repayment_schedule
        instance.repayment_mode = repayment_mode if repayment_mode is not None else instance.repayment_mode
        instance.disbursement_type = disbursement_type if disbursement_type is not None else instance.disbursement_type
        instance.interest_basics = interest_basics if interest_basics is not None else instance.interest_basics
        instance.loan_purpose = loan_purpose if loan_purpose is not None else instance.loan_purpose
        instance.loan_calculation_method = loan_calculation_method if loan_calculation_method is not None else instance.loan_calculation_method
        instance.interest_rate = interest_rate if interest_rate is not None else instance.interest_rate
        instance.tenure = tenure if tenure is not None else instance.tenure
        instance.tenure_type = tenure_type if tenure_type is not None else instance.tenure_type
        instance.description = description if description is not None else instance.description
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'Loan Application Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except LoanType.DoesNotExist:
        return error('Invalid LoanType ID: Destination not found.')
    except  LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loanapplication(loanapplication_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loanapplication_id is not None:
            record = LoanApplication.objects.get(pk=loanapplication_id)
            serializer = LoanapplicationSerializer(record)
        elif company_id is not None:
            records = LoanApplication.objects.filter(company_id = company_id)
            serializer = LoanapplicationSerializer(records, many=True)
        else:
            records = LoanApplication.objects.all()
            serializer = LoanapplicationSerializer(records, many=True)
        return success(serializer.data)
    
    except LoanApplication.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loanapplication does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def getting_approved_rejected_applications(company_id):
    try:
        records = LoanApplication.objects.filter(company_id = company_id,is_active=True )
        serializer = LoanapplicationSerializer(records, many=True)
        return success(serializer.data)
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def getting_approved_applications(company_id):
    try:
        records = LoanApplication.objects.filter(company_id = company_id,application_status__iexact = 'Approved',is_active=True)
        serializer = LoanapplicationSerializer(records, many=True)
        return success(serializer.data)
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_loanapplication(loanapplication_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = LoanApplication.objects.get(pk=loanapplication_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Loan Application Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def check_loan_eligibilities_forall(company_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = LoanApplication.objects.filter(is_active = True,company_id = company_id)
        for applications in instance:
            applicant_deatils = Customer.objects.get(pk=applications.customer_id.id)
            existing_loan = Loan.objects.filter(customer_id = applications.id)
            loanids = [data.id for data in existing_loan ]
            # Calculate Exsisting loan liabilities
            existing_loan_liabilities = calculate_existing_liabilities(loanids)
            applicant_deatils.existing_liabilities = existing_loan_liabilities
            applicant_deatils.save()

            # Perform eligibility check
            is_eligible, errors = check_loan_eligibility(applicant_deatils, applications.loan_amount)
            
            if is_eligible == True:
                applications.is_eligible = True
                applications.checked_on = datetime.now()
            else:
                applications.eligible_rejection_reason = errors
                applications.checked_on = datetime.now()
            applications.save()
    
        status = {'eligible_status':is_eligible,'errors':errors}
        
        # Pass results to template
        return success(status)

    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def check_loan_eligibilities(application_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        instance = LoanApplication.objects.get(pk=application_id)
        applicant_deatils = Customer.objects.get(pk=instance.customer_id.id)
        existing_loan = Loan.objects.filter(customer_id = applicant_deatils.id)
        loanids = [data.id for data in existing_loan ]
        # Calculate Exsisting loan liabilities
        existing_loan_liabilities = calculate_existing_liabilities(loanids)
        applicant_deatils.existing_liabilities = existing_loan_liabilities
        applicant_deatils.save()

        # Perform eligibility check
        is_eligible, errors = check_loan_eligibility(applicant_deatils, instance.loan_amount)
        
        if is_eligible == True:
            instance.is_eligible = True
            instance.checked_on = datetime.now()
        else:
            instance.eligible_rejection_reason = errors
            instance.checked_on = datetime.now()
        instance.save()
    
        status = {'eligible_status':is_eligible,'errors':errors}
        
        # Pass results to template
        return success(status)

    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def loan_risk_assessment_list(company_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = LoanApplication.objects.filter(company_id=company_id,is_active=True)
        serializer = LoanapplicationSerializer(instance, many=True).data
        # Compute the risk score for each loan application

        for application, serialized_data in zip(instance, serializer):
            customer = get_object_or_404(Customer,id=application.customer_id.id)
            # Compute the risk score for the loan application
            risk_score = calculate_risk_score(customer, application)  # Your custom function
            
            # Add or update the risk score in the serialized data
            serialized_data['risk_score'] = risk_score
            application.risk_score = float(risk_score)
            application.save()
        return success(serializer)
    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def loan_risk_assessment_detail(application_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        loan_application = get_object_or_404(LoanApplication, id=application_id)
        serializer = LoanapplicationSerializer(loan_application).data
        customer = get_object_or_404(Customer,id=loan_application.customer_id.id)

        risk_score, risk_factors = calculate_risk_factors(customer, loan_application)
        serializer['risk_score'] = risk_score
        serializer['risk_factors'] = risk_factors
        loan_application.risk_factor = risk_factors
        loan_application.save()

        return success(serializer)

    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def loan_approval(company_id,loanapp_id, approval_status = None,rejected_reason = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        instance = LoanApplication.objects.get(pk=loanapp_id)
        if approval_status == "Approved":
            instance.application_status = "Approved"
            instance.workflow_stats = "Approved"
            instance.save()

            # create loan
            loan = create_loan(loanapp_id)
            print('loan',loan)
            
             # Create accounts for the loan
            # 1. Create Loan Account
            loan_account = LoanAccount.objects.create(
                company_id = company_id,
                loan_id = loan['data'],
                principal_amount=instance.loan_amount,
                outstanding_balance=instance.loan_amount,
            )
            
            # 2. Create Loan Disbursement Account
            loan_disbursement_account = LoanDisbursementAccount.objects.create(
                company_id = company_id,
                loan_id = loan['data'],
                amount=instance.loan_amount,
                loan_account=loan_account,
            )

            # 3. Create Repayment Account
            LoanRepaymentAccount.objects.create(
                company_id = company_id,
                loan_id=loan['data'],
                amount=0.00,  # Initial amount can be set to 0.00
                payment_method='bank_transfer',  # Default method, adjust as needed
            )

            # 4. Create Penalty Account (optional)
            PenaltyAccount.objects.create(
                company_id = company_id,
                loan_id=loan['data'],
                penalty_amount=0.00,  # Initial penalty amount can be set to 0.00
                penalty_reason='N/A',  # Placeholder, adjust as necessary
            )

            # 5. Create Interest Account (optional)
            InterestAccount.objects.create(
                company_id = company_id,
                loan_id=loan['data'],
                interest_accrued=0.00,  # Initial interest accrued can be set to 0.00
            )

            # calling repayment schedule 
            schedules = calculate_repayment_schedule(instance.loan_amount,instance.interest_rate, instance.tenure, instance.tenure_type, instance.repayment_schedule, instance.loan_calculation_method, instance.repayment_start_date, instance.repayment_mode)
            if schedules['status_code'] == 1: 
                return error(f"An error occurred: {schedules['data']}")
            
            for data in schedules['data']:
                # generate Unique id 
                generate_id = RepaymentSchedule.objects.last()
                last_id = '00'
                if generate_id:
                    last_id = generate_id.schedule_id[10:]
                schedule_id = unique_id('SID',last_id)

                aa = RepaymentSchedule.objects.create(
                    company_id = instance.company.id,
                    schedule_id = schedule_id,
                    loan_application_id = instance.id,
                    loan_id_id = loan['data'],
                    period = float(data['Period']),
                    repayment_date = data['Due_Date'],
                    instalment_amount = float(data['Installment']),
                    principal_amount = float(data['Principal']),
                    interest_amount = float(data['Interest']),
                    remaining_balance = float(data['Closing_Balance']),
                )
             
            if loan['status_code'] == 1:
                return error(f"An error occurred: {loan['data']}")
        elif approval_status == "Rejected":
            instance.application_status = "Rejected"
            instance.rejected_reason = rejected_reason
        else:
            instance.application_status = "Submitted"
        instance.save()
        return success("Successfully Approved Your Application")
    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_loan(loanapp_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        records = LoanApplication.objects.get(pk=loanapp_id)

        # generate Unique id 
        generate_id = Loan.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.loan_id[9:]
        loan_id = unique_id('LN',last_id)

        instance = Loan.objects.create(
            company_id = records.company.id,
            customer_id = records.customer_id.id,
            loanapp_id_id = loanapp_id,
            loan_id = loan_id,
            loan_amount = float(records.loan_amount),
            approved_amount = float(records.loan_amount),
            interest_rate = float(records.interest_rate),
            tenure = records.tenure,
            tenure_type = records.tenure_type,
            repayment_schedule = records.repayment_schedule,
            repayment_mode = records.repayment_mode,
            interest_basics = records.interest_basics,
            loan_purpose = records.loan_purpose,
            workflow_stats = "Approved",

        )

        try:
            log_audit_trail(request.user.id,'Loan Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")



        return success(instance.id)
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loan(loan_id=None,loanapp_id = None,company=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loan_id is not None:
            record = Loan.objects.get(pk=loan_id)
            serializer = LoanSerializer(record)
        if loanapp_id is not None:
            record = Loan.objects.filter(loanapp_id_id=loanapp_id).last()
            serializer = LoanSerializer(record)

        elif company is not None:
            records = Loan.objects.filter(company_id = company)
            serializer = LoanSerializer(records, many=True)
        else:
            records = Loan.objects.all().order_by('-id')
            serializer = LoanSerializer(records, many=True)
        return success(serializer.data)
    
    except Loan.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loan does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def getting_approved_loanapp_records(company_id):
    try:
        records = Loan.objects.filter(company_id = company_id,workflow_stats__iexact = "Approved").order_by('-id')
        serializer = LoanSerializer(records, many=True)
        return success(serializer.data)
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")


def create_loanagreement(company_id,loan_id, loanapp_id, customer_id, agreement_terms,is_active=False,attachment=None,attachment1=None,maturity_date=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if loanapp_id is not None: 
            LoanApplication.objects.get(pk=loanapp_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)
        if Loan is not None:
            Loan.objects.get(pk = loan_id)

        # generate Unique id 
        generate_id = LoanAgreement.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.agreement_id[9:]
        agreement_id = unique_id('LG',last_id)

        instance = LoanAgreement.objects.create(
            company_id=company_id,
            agreement_id=agreement_id,
            loan_id_id = loan_id,
            loanapp_id_id = loanapp_id,
            customer_id_id=customer_id,
            agreement_terms=agreement_terms,
            borrower_signature = attachment,
            lender_signature = attachment1,
            maturity_date = maturity_date,
            agreement_status = 'Active',
            is_active = is_active,
        )

        # update the workflow status in loan application and loan table
        loanapp = LoanApplication.objects.get(pk=loanapp_id)
        loan = Loan.objects.get(pk = loan_id)
        if attachment1 and attachment:
            loanapp.workflow_stats = "Borrower_and_Lender_Approved"
            loan.workflow_stats = "Borrower_and_Lender_Approved"
        elif attachment:
            loanapp.workflow_stats = "Borrower_Approved"
            loan.workflow_stats = "Borrower_Approved"
        elif attachment1:
            loanapp.workflow_stats = "Lender_Approved"
            loan.workflow_stats = "Lender_Approved"
        else:
            loanapp.workflow_stats = "Borrower_and_Lender_Approved" # Approved
            loan.workflow_stats = "Borrower_and_Lender_Approved"
        loanapp.save()
        loan.save()

        try:
            log_audit_trail(request.user.id,'Loan Agreement Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except LoanApplication.DoesNotExist:
        return error('Invalid Loan ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def loanagreement_confirmation(company_id,loanagreementid,status):
    try:
        instance = LoanAgreement.objects.get(pk = loanagreementid)
        # update agreement status in loan
        loan = Loan.objects.get(pk = instance.loan_id.id)

        if status == "Completed":
            instance.agreement_status = "Completed"
            loan.status = 'approved'
        else:
            instance.agreement_status = "Terminated"
            loan.status = 'denied'
        
        instance.save()
        loan.save()

        return success(f'Successfully confirmed')
    except LoanAgreement.DoesNotExist:
        return error('Invalid LoanAgreement ID: LoanAgreement not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")


def update_loanagreement(loanagreement_id,company_id,is_active=False, loanapp_id = None,maturity_date=None,loan_id = None, customer_id = None, agreement_terms = None,attachment = None,attachment1 = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if loanapp_id is not None: 
            Loan.objects.get(pk=loanapp_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)

        instance = LoanAgreement.objects.get(pk = loanagreement_id)

        instance.company_id = company_id if company_id is not None else instance.company_id
        instance.loanapp_id_id = loanapp_id if loanapp_id is not None else instance.loanapp_id
        instance.loan_id_id = loan_id if loan_id is not None else instance.loan_id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id
        instance.agreement_terms = agreement_terms if agreement_terms is not None else instance.agreement_terms
        instance.borrower_signature = attachment if attachment is not None else instance.borrower_signature
        instance.lender_signature = attachment1 if attachment1 is not None else instance.lender_signature
        instance.is_active = is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'Loan Application Agreement', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Loan.DoesNotExist:
        return error('Invalid Loan ID: Loan not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except  LoanAgreement.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loanagreement(loanagreement_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loanagreement_id is not None:
            record = LoanAgreement.objects.get(pk=loanagreement_id)
            serializer = LoanagreementSerializer(record)
        elif company_id is not None:
            records = LoanAgreement.objects.filter(company_id = company_id).order_by("-id")
            serializer = LoanagreementSerializer(records, many=True)
        else:
            records = LoanAgreement.objects.all()
            serializer = LoanagreementSerializer(records, many=True)
        return success(serializer.data)
    
    except LoanAgreement.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loanagreement does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def getting_completed_agreement(company_id):
    try:
        records = Loan.objects.filter(company_id = company_id,is_active=True,status__iexact = 'approved').order_by("-id")
        serializer = LoanSerializer(records, many=True)
        return success(serializer.data)
    
    except LoanAgreement.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loanagreement does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def agreement_confirmation(loanagreement_id,status):
    try:
        records = LoanAgreement.objects.get(id = loanagreement_id)
        records.agreement_status = status
        records.save()
        loanapp = LoanApplication.objects.get(id = records.loan_id.id)
        loan_data = Loan.objects.get(id = records.loanapp_id.id)
        if status == 'Completed':
            loanapp.workflow_stats = 'Agreement_completed'
            loan_data.workflow_stats = 'Agreement_completed'
        else:
            loanapp.workflow_stats = 'Agreement_dined'
            loan_data.workflow_stats = 'Agreement_dined'
        loanapp.save()
        loan_data.save()

    except LoanAgreement.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loanagreement does not exist')
    except LoanApplication.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('LoanApplication does not exist')
    except Loan.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loan does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")


def delete_loanagreement(loanagreement_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = LoanAgreement.objects.get(pk=loanagreement_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Loan Application Agreement', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except LoanAgreement.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_approvedloan(company_id):
    try:
        loan_details = Loan.objects.filter(workflow_stats__iexact = "Borrower_and_Lender_Approved",company_id = company_id)
        serializer = LoanSerializer(loan_details,many=True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_disbursement(company_id, customer_id,loan_id, loan_application_id, amount, disbursement_type, disbursement_status,disbursement_method,currency_id,bank=None,notes=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        # Validate foreign keys
        Company.objects.get(pk=company_id)
        Customer.objects.get(pk=customer_id)
        LoanApplication.objects.get(pk=loan_application_id)
        Currency.objects.get(pk=currency_id)

        # Generate unique disbursement ID
        generate_id = Disbursement.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.disbursement_id[10:]
        disbursement_id = unique_id('DISB', last_id)

        loanapp = LoanApplication.objects.get(pk=loan_application_id)
        loan = Loan.objects.get(pk = loan_id)

        # 1 st scenario disbursement type one-off and Disbursement Beneficiary Pay Self
        if loanapp.disbursement_type == 'one_off':
            if loanapp.loantype.disbursement_beneficiary == 'pay_self':
                loan_account = LoanAccount.objects.get(loan_id = loan.id)
                loan_account.principal_amount = amount
                loan_account.outstanding_balance = amount
                loan_account.save()
                print("One-off disbursement to loan account completed.")
            elif loanapp.loantype.disbursement_beneficiary == 'pay_milestone':  
                # Prevent customer from withdrawing the loan amount for controlled purposes
                return error("Disbursement cannot proceed as the amount is designated for a milestone.")

        elif loanapp.disbursement_type == 'trenches': 
            if loanapp.loantype.disbursement_beneficiary == 'pay_self':
                loan_account = LoanAccount.objects.get(loan_id = loan.id)
                loan_account.principal_amount += amount
                loan_account.outstanding_balance += amount
                loan_account.save()
                print("One-off disbursement to loan account completed.")

            elif loanapp.loantype.disbursement_beneficiary == 'pay_milestone':
                milestone_account = MilestoneAccount.objects.get(loan_id = loan.id)
                milestone_account.milestone_cost += amount
                milestone_account.status += 'Completed'
                milestone_account.save()
                print("One-off disbursement to milestone wallet account completed.")

        # Create disbursement
        instance = Disbursement.objects.create(
            company_id=company_id,
            loan_id = loan_id,
            disbursement_id=disbursement_id,
            customer_id_id=customer_id,
            loan_application_id=loan_application_id,
            amount=amount,
            disbursement_type=disbursement_type,
            disbursement_method = disbursement_method,
            disbursement_status=disbursement_status,
            currency_id = currency_id,
            bank_id = bank,
            notes=notes,
        )
        # update the workflow status in loan application and loan table
        loan.disbursement_amount = float(loan.disbursement_amount) + float(amount)
        loanapp.workflow_stats = 'Disbursment'
        loan.workflow_stats = 'Disbursment'
        loan.disbursement_amount = amount
        loanapp.save()
        loan.save()

        try:
            log_audit_trail(request.user.id,'Disbursement Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f'Successfully created disbursement {instance}')
    
    except Company.DoesNotExist:
        return error('Invalid Company ID')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID')
    except LoanApplication.DoesNotExist:
        return error('Invalid Loan Application ID')
    except Currency.DoesNotExist:
        return error('Invalid Payment Method ID')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_disbursement(disbursement_id, company_id, customer_id,loan_id, loan_application_id, amount, disbursement_type, disbursement_status,disbursement_method,currency_id,bank=None,notes=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
      
      
        instance = Disbursement.objects.get(pk=disbursement_id)

        # Validate foreign keys
        if company_id is not None:
            Company.objects.get(pk=company_id)
        if customer_id is not None:
            Customer.objects.get(pk=customer_id)
        if loan_application_id is not None:
            LoanApplication.objects.get(pk=loan_application_id)
        if currency_id is not None:
            Currency.objects.get(pk=currency_id)

        # Update fields
        instance.company_id = company_id if company_id is not None else instance.company_id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id.id
        instance.loan_id = loan_id if loan_id is not None else instance.loan.id
        instance.loan_application_id = loan_application_id if loan_application_id is not None else instance.loan_application_id.id
        instance.amount = amount if amount is not None else instance.amount
        instance.currency_id = currency_id if currency_id is not None else instance.currency.id
        instance.disbursement_type = disbursement_type if disbursement_type is not None else instance.disbursement_type
        instance.disbursement_method = disbursement_method if disbursement_method is not None else instance.disbursement_method
        instance.disbursement_status = disbursement_status if disbursement_status is not None else instance.disbursement_status
        instance.bank_id = bank if bank is not None else instance.bank.id
        instance.notes = notes if notes is not None else instance.notes
        
        instance.save()

        try:
            log_audit_trail(request.user.id,'Disbursement Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success('Successfully updated disbursement')
    
    except Disbursement.DoesNotExist:
        return error('Disbursement does not exist')
    except Company.DoesNotExist:
        return error('Invalid Company ID')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID')
    except LoanApplication.DoesNotExist:
        return error('Invalid Loan Application ID')
    except Currency.DoesNotExist:
        return error('Invalid Payment Method ID')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_disbursement(disbursement_id=None, company_id=None):
    try:
        if disbursement_id is not None:
            record = Disbursement.objects.get(pk=disbursement_id)
            serializer = DisbursementSerializer(record)
        elif company_id is not None:
            records = Disbursement.objects.filter(company_id=company_id)
            serializer = DisbursementSerializer(records, many=True)
        else:
            records = Disbursement.objects.all()
            serializer = DisbursementSerializer(records, many=True)

        return success(serializer.data)

    except Disbursement.DoesNotExist:
        return error('Disbursement does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_disbursement(disbursement_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Disbursement.objects.get(pk=disbursement_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Disbursement Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted disbursement")

    except Disbursement.DoesNotExist:
        return error('Disbursement does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_disbursementloans(company_id):
    try:
        instance = LoanApplication.objects.filter(company_id=company_id,workflow_stats__in=['Disbursment','Processing'])
        serializer = LoanapplicationSerializer(instance,many=True)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_repayment_schedules(company_id,loanapp_id):
    try:
        instance = RepaymentSchedule.objects.filter(company_id=company_id,loan_id_id = loanapp_id)
        serializer = RepaymentscheduleSerializer(instance,many=True)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def confirmed_schedule(loan_id):
    try:
        loans = RepaymentSchedule.objects.filter(loan_id_id = loan_id)
        for data in loans:
            data.confirmed_status = 'Confirmed'
            data.save()
        return success('Sucessfully Confirmed') 
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_collaterals(company_id, loanapp_id, customer_id, collateral_type_id, collateral_value, valuation_date, collateral_status, insurance_status,description=None):
    """ ================= collateral creations ======================== """
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if loanapp_id is not None: 
            LoanApplication.objects.get(pk=loanapp_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)
        if collateral_type_id is not None: 
            CollateralType.objects.get(pk=collateral_type_id)

        # generate Unique id 
        generate_id = Collaterals.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.collateral_id[9:]
        collateral_id = unique_id('CL',last_id)

        instance = Collaterals.objects.create(
            company_id=company_id,
            collateral_id=collateral_id,
            loanapp_id_id=loanapp_id,
            customer_id_id=customer_id,
            collateral_type_id=collateral_type_id,
            collateral_value=collateral_value,
            valuation_date=valuation_date,
            collateral_status=collateral_status,
            insurance_status=insurance_status,
        )

        try:
            log_audit_trail(request.user.id,'Collaterals Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except LoanApplication.DoesNotExist:
        return error('Invalid Loan ID: LoanApplication not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Customer not found.')
    except CollateralType.DoesNotExist:
        return error('Invalid Collateraltype ID: CollateralType not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def upload_collateraldocument(company_id,loanapplication_id,document_name,attachment=None,desctioption=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        Company.objects.get(pk=company_id)
        LoanApplication.objects.get(pk=loanapplication_id)

        instance = CollateralDocuments.objects.create(
            company_id = company_id,
            application_id_id = loanapplication_id,
            document_name = document_name,
            additional_documents = attachment,
            description = desctioption,
        )

        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Company not found.')
    except LoanApplication.DoesNotExist:
        return error('Invalid LoanApplication ID: LoanApplication not found.')   
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_collateraldocument(loan_application_id):
    try:
        records = CollateralDocuments.objects.filter(application_id_id = loan_application_id)
        serializer = CollateralDocumentsSerializer(records, many=True).data
        return success(serializer)
    except LoanApplication.DoesNotExist:
        return error('Invalid LoanApplication ID: LoanApplication not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")


def update_collaterals(collaterals_id,company_id=None, collateral_id=None, loanapp_id=None, customer_id=None, collateral_type_id=None, collateral_value=None, valuation_date=None, collateral_status=None, insurance_status=None,valuation_report=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if loanapp_id is not None: 
            LoanApplication.objects.get(pk=loanapp_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)
        if collateral_type_id is not None: 
            CollateralType.objects.get(pk=collateral_type_id)

        instance = Collaterals.objects.get(pk=collaterals_id)
        instance.company_id = company_id if company_id is not None else instance.company_id
        instance.collateral_id = collateral_id if collateral_id is not None else instance.collateral_id
        instance.loanapp_id_id = loanapp_id if loanapp_id is not None else instance.loanapp_id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id
        instance.valuation_report = valuation_report if valuation_report is not None else instance.valuation_report 
        instance.collateral_type_id = collateral_type_id if collateral_type_id is not None else instance.collateral_type_id
        instance.collateral_value = collateral_value if collateral_value is not None else instance.collateral_value
        instance.valuation_date = valuation_date if valuation_date is not None else instance.valuation_date
        instance.collateral_status = collateral_status if collateral_status is not None else instance.collateral_status
        instance.insurance_status = insurance_status if insurance_status is not None else instance.insurance_status
        instance.save()

        try:
            log_audit_trail(request.user.id,'Collaterals Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except LoanApplication.DoesNotExist:
        return error('Invalid LoanApplication ID: LoanApplication not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except CollateralType.DoesNotExist:
        return error('Invalid Collateraltype ID: Destination not found.')
    except  Collaterals.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_collaterals(company_id,collaterals_id=None,customer_id = None,loan_appliaction_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if collaterals_id is not None:
            record = Collaterals.objects.get(pk=collaterals_id)
            serializer = CollateralsSerializer(record)
        elif loan_appliaction_id is not None:
            records = Collaterals.objects.filter(loanapp_id = loan_appliaction_id)
            serializer = CollateralsSerializer(records, many=True)
        elif customer_id is not None:
            records = Collaterals.objects.filter(customer_id_id = customer_id,company_id = company_id)
            serializer = CollateralsSerializer(records, many=True)
        else:
            records = Collaterals.objects.all()
            serializer = CollateralsSerializer(records, many=True)
        return success(serializer.data)
    
    except Collaterals.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Collaterals does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_collaterals(collaterals_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Collaterals.objects.get(pk=collaterals_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'Collaterals Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except Collaterals.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def check_eligibility(customer_id):
    """
    Checks if the customer is eligible for the loan.

    Parameters:
    customer (Customer): The customer object related to the loan.

    Returns:
    bool: True if eligible, False otherwise.
    """
    customers = Customer.objects.get(id = customer_id)
    # Example criteria: Check credit score, income, or other conditions
    if customers.credit_score < 650:
        return False
    if customers.customer_income < 5000:
        return False
    return True


def verify_collateral(collateral_id):
    """
    Verifies the value and legitimacy of collateral.

    Parameters:
    collateral (Collateral): The collateral associated with the loan.

    Returns:
    bool: True if the collateral is verified, False otherwise.
    """
    collateral = Collaterals.objects.get(id = collateral_id)
    # Example: Check if collateral is above a minimum value
    if collateral.collateral_value < float(5000):
        return False
    return True

def create_payment(company_id,loanid, amount, payment_method_id, transaction_reference=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        company = Company.objects.get(pk=company_id)
        payment_method = PaymentMethod.objects.get(pk=payment_method_id)
        loan = Loan.objects.get(pk = loanid)

        # Generate a unique payment ID
        last_payment = Payments.objects.last()
        last_id = '00'
        if last_payment:
            last_id = last_payment.payment_id[9:]
        payment_id = unique_id('PAY', last_id)

        # Create the payment
        payment = Payments.objects.create(
            company_id = company_id,
            payment_id = payment_id,
            loan_id_id = loanid,
            amount = amount,
            payment_method_id = payment_method_id,
            transaction_refference=transaction_reference
        )

        loan.paid_amount = float(loan.paid_amount) + float(amount)
        loan.save()

        try:
            log_audit_trail(request.user.id,'Payment Registration', payment, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Payment created successfully with ID: {payment.payment_id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except Loan.DoesNotExist:
        return error("Invalid Loan Application ID")
    except PaymentMethod.DoesNotExist:
        return error("Invalid Payment Method ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_payment(payment_id=None, company_id=None):
    try:
        if payment_id:
            payment = Payments.objects.get(pk=payment_id)
            serializer = PaymentsSerializer(payment)
        elif company_id:
            payments = Payments.objects.filter(company_id=company_id)
            serializer = PaymentsSerializer(payments, many=True)
        else:
            payments = Payments.objects.all()
            serializer = PaymentsSerializer(payments, many=True)

        return success(serializer.data)

    except Payments.DoesNotExist:
        return error(f"Payment with ID {payment_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_payment(payment_id, company_id=None, loanapp_id=None, amount=None, payment_method_id=None, transaction_reference=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        payment = Payments.objects.get(pk=payment_id)

        if company_id:
            payment.company = Company.objects.get(pk=company_id)
        if loanapp_id:
            payment.loanapp_id = LoanApplication.objects.get(pk=loanapp_id)
        if amount:
            payment.amount = amount
        if payment_method_id:
            payment.payment_method = PaymentMethod.objects.get(pk=payment_method_id)
        if transaction_reference:
            payment.transaction_refference = transaction_reference

        payment.save()

        try:
            log_audit_trail(request.user.id,'Payment Registration', payment, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Payment updated successfully")

    except Payments.DoesNotExist:
        return error(f"Payment with ID {payment_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except PaymentMethod.DoesNotExist:
        return error("Invalid Payment Method ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_payment(payment_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        payment = Payments.objects.get(pk=payment_id)
        payment.delete()

        try:
            log_audit_trail(request.user.id,'Payment Registration', payment, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Payment with ID {payment_id} deleted successfully")

    except Payments.DoesNotExist:
        return error(f"Payment with ID {payment_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_penalties(company_id, loanapp_id, repaymentschedule_id, penalty_amount, penalty_reason, payment_status, transaction_reference=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        company = Company.objects.get(pk=company_id)
        loan_application = LoanApplication.objects.get(pk=loanapp_id)
        repayment_schedule = RepaymentSchedule.objects.get(pk=repaymentschedule_id)

        # Generate a unique penalty ID
        last_penalty = Penalties.objects.last()
        last_id = '00'
        if last_penalty:
            last_id = last_penalty.penalty_id[9:]
        penalty_id = unique_id('PEN', last_id)

        # Create the penalty
        penalty = Penalties.objects.create(
            company=company,
            penalty_id=penalty_id,
            loan_application=loan_application,
            repaymentschedule_id=repayment_schedule,
            penalty_amount=penalty_amount,
            penalty_reason=penalty_reason,
            payment_status=payment_status,
            transaction_refference=transaction_reference
        )

        try:
            log_audit_trail(request.user.id,'penalty Registration', penalty, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f"Penalty created successfully with ID: {penalty.penalty_id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except RepaymentSchedule.DoesNotExist:
        return error("Invalid Repayment Schedule ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_penalties(penalty_id=None, company_id=None):
    try:
        if penalty_id:
            penalty = Penalties.objects.get(pk=penalty_id)
            serializer = PenaltiesSerializer(penalty)
        elif company_id:
            penalties = Penalties.objects.filter(company_id=company_id)
            serializer = PenaltiesSerializer(penalties, many=True)
        else:
            penalties = Penalties.objects.all()
            serializer = PenaltiesSerializer(penalties, many=True)

        return success(serializer.data)

    except Penalties.DoesNotExist:
        return error(f"Penalty with ID {penalty_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_penalties(penalty_id, company_id=None, loanapp_id=None, repaymentschedule_id=None, penalty_amount=None, penalty_reason=None, payment_status=None, transaction_reference=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        penalty = Penalties.objects.get(pk=penalty_id)

        if company_id:
            penalty.company = Company.objects.get(pk=company_id)
        if loanapp_id:
            penalty.loan_application = LoanApplication.objects.get(pk=loanapp_id)
        if repaymentschedule_id:
            penalty.repaymentschedule_id = RepaymentSchedule.objects.get(pk=repaymentschedule_id)
        if penalty_amount:
            penalty.penalty_amount = penalty_amount
        if penalty_reason:
            penalty.penalty_reason = penalty_reason
        if payment_status:
            penalty.payment_status = payment_status
        if transaction_reference:
            penalty.transaction_refference = transaction_reference

        penalty.save()

        try:
            log_audit_trail(request.user.id,'penalty Registration', penalty, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success("Penalty updated successfully")

    except Penalties.DoesNotExist:
        return error(f"Penalty with ID {penalty_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except RepaymentSchedule.DoesNotExist:
        return error("Invalid Repayment Schedule ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_penalties(penalty_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        penalty = Penalties.objects.get(pk=penalty_id)
        penalty.delete()
        try:
            log_audit_trail(request.user.id,'penalty Registration', penalty, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f"Penalty with ID {penalty_id} deleted successfully")

    except Penalties.DoesNotExist:
        return error(f"Penalty with ID {penalty_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_loan_closure(company_id, loanapp_id, closure_date, closure_amount, remaining_balance, closure_method, closure_reason, transaction_reference=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        company = Company.objects.get(pk=company_id)
        loan_application = LoanApplication.objects.get(pk=loanapp_id)

        # Generate a unique closure ID
        last_closure = LoanClosure.objects.last()
        last_id = '00'
        if last_closure:
            last_id = last_closure.closure_id[9:]
        closure_id = unique_id('CLO', last_id)

        # Create the loan closure
        closure = LoanClosure.objects.create(
            company=company,
            closure_id=closure_id,
            loanapp_id=loan_application,
            closure_date=closure_date,
            closure_amount=closure_amount,
            remaining_balance=remaining_balance,
            closure_method=closure_method,
            closure_reason=closure_reason,
            transaction_refference=transaction_reference
        )
        try:
            log_audit_trail(request.user.id,'penalty Registration', closure, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f"Loan closure created successfully with ID: {closure.closure_id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")


def view_loan_closure(closure_id=None, company_id=None):
    try:
        if closure_id:
            closure = LoanClosure.objects.get(pk=closure_id)
            serializer = LoanClosureSerializer(closure)
        elif company_id:
            closures = LoanClosure.objects.filter(company_id=company_id)
            serializer = LoanClosureSerializer(closures, many=True)
        else:
            closures = LoanClosure.objects.all()
            serializer = LoanClosureSerializer(closures, many=True)

        return success(serializer.data)

    except LoanClosure.DoesNotExist:
        return error(f"Loan closure with ID {closure_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_loan_closure(closure_id, company_id=None, loanapp_id=None, closure_date=None, closure_amount=None, remaining_balance=None, closure_method=None, closure_reason=None, transaction_reference=None):
    try:

        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        closure = LoanClosure.objects.get(pk=closure_id)

        if company_id:
            closure.company = Company.objects.get(pk=company_id)
        if loanapp_id:
            closure.loanapp_id = LoanApplication.objects.get(pk=loanapp_id)
        if closure_date:
            closure.closure_date = closure_date
        if closure_amount is not None:
            closure.closure_amount = closure_amount
        if remaining_balance is not None:
            closure.remaining_balance = remaining_balance
        if closure_method:
            closure.closure_method = closure_method
        if closure_reason:
            closure.closure_reason = closure_reason
        if transaction_reference:
            closure.transaction_refference = transaction_reference

        closure.save()

        try:
            log_audit_trail(request.user.id,'closure Registration', closure, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")



        return success("Loan closure updated successfully")

    except LoanClosure.DoesNotExist:
        return error(f"Loan closure with ID {closure_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_loan_closure(closure_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        closure = LoanClosure.objects.get(pk=closure_id)
        closure.delete()

        try:
            log_audit_trail(request.user.id,'closure Registration', closure, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f"Loan closure with ID {closure_id} deleted successfully")

    except LoanClosure.DoesNotExist:
        return error(f"Loan closure with ID {closure_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_support_ticket(company_id, customer_id, subject=None, description=None, status='Open', priority='Low', assigned_to=None, resolution=None, resolution_date=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        company = Company.objects.get(pk=company_id)
        customer = Customer.objects.get(pk=customer_id)

        # Generate a unique ticket ID
        last_ticket = SupportTickets.objects.last()
        last_id = '00'
        if last_ticket:
            last_id = last_ticket.ticket_id[9:]
        ticket_id = unique_id('TICKET', last_id)

        # Create the support ticket
        ticket = SupportTickets.objects.create(
            company=company,
            ticket_id=ticket_id,
            customer_id=customer,
            subject=subject,
            description=description,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            resolution=resolution,
            resolution_date=resolution_date
        )
        try:
            log_audit_trail(request.user.id,'Ticket Registration', ticket, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f"Support ticket created successfully with ID: {ticket.ticket_id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except Customer.DoesNotExist:
        return error("Invalid Customer ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_support_ticket(ticket_id=None, company_id=None):
    try:
        if ticket_id:
            ticket = SupportTickets.objects.get(pk=ticket_id)
            serializer = SupportTicketSerializer(ticket)
        elif company_id:
            tickets = SupportTickets.objects.filter(company_id=company_id)
            serializer = SupportTicketSerializer(tickets, many=True)
        else:
            tickets = SupportTickets.objects.all()
            serializer = SupportTicketSerializer(tickets, many=True)

        return success(serializer.data)

    except SupportTickets.DoesNotExist:
        return error(f"Support ticket with ID {ticket_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_support_ticket(ticket_id, company_id=None, customer_id=None, subject=None, description=None, status=None, priority=None, assigned_to=None, resolution=None, resolution_date=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        ticket = SupportTickets.objects.get(pk=ticket_id)

        if company_id:
            ticket.company = Company.objects.get(pk=company_id)
        if customer_id:
            ticket.customer_id = Customer.objects.get(pk=customer_id)
        if subject:
            ticket.subject = subject
        if description:
            ticket.description = description
        if status:
            ticket.status = status
        if priority:
            ticket.priority = priority
        if assigned_to:
            ticket.assigned_to = assigned_to
        if resolution:
            ticket.resolution = resolution
        if resolution_date:
            ticket.resolution_date = resolution_date

        ticket.save()
        try:
            log_audit_trail(request.user.id,'Ticket Registration', ticket, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success("Support ticket updated successfully")

    except SupportTickets.DoesNotExist:
        return error(f"Support ticket with ID {ticket_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except Customer.DoesNotExist:
        return error("Invalid Customer ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_support_ticket(ticket_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        ticket = SupportTickets.objects.get(pk=ticket_id)
        ticket.delete()
        try:
            log_audit_trail(request.user.id,'Ticket Registration', ticket, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f"Support ticket with ID {ticket_id} deleted successfully")

    except SupportTickets.DoesNotExist:
        return error(f"Support ticket with ID {ticket_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_customer_feedback(customer_id, feedback_date, feedback_type, subject, description=None, feedback_status='Open'):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        customer = Customer.objects.get(pk=customer_id)

        # Generate a unique feedback ID
        last_feedback = CustomerFeedBack.objects.last()
        last_id = '00'
        if last_feedback:
            last_id = last_feedback.feedback_id[9:]
        feedback_id = unique_id('FB', last_id)

        # Create the feedback
        feedback = CustomerFeedBack.objects.create(
            feedback_id=feedback_id,
            customer_id=customer,
            feedback_date=feedback_date,
            feedback_type=feedback_type,
            subject=subject,
            description=description,
            feedback_status=feedback_status
        )
        try:
            log_audit_trail(request.user.id,'Customer Feedback Registration', feedback, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        
        return success(f"Customer feedback created successfully with ID: {feedback.feedback_id}")

    except Customer.DoesNotExist:
        return error("Invalid Customer ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_customer_feedback(feedback_id=None, customer_id=None):
    try:
        if feedback_id:
            feedback = CustomerFeedBack.objects.get(pk=feedback_id)
            serializer = CustomerFeedbackSerializer(feedback)
        elif customer_id:
            feedbacks = CustomerFeedBack.objects.filter(customer_id=customer_id)
            serializer = CustomerFeedbackSerializer(feedbacks, many=True)
        else:
            feedbacks = CustomerFeedBack.objects.all()
            serializer = CustomerFeedbackSerializer(feedbacks, many=True)

        return success(serializer.data)

    except CustomerFeedBack.DoesNotExist:
        return error(f"Customer feedback with ID {feedback_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_customer_feedback(feedback_id, customer_id=None, feedback_date=None, feedback_type=None, subject=None, description=None, feedback_status=None):
    try:

        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        feedback = CustomerFeedBack.objects.get(pk=feedback_id)

        if customer_id:
            feedback.customer_id = Customer.objects.get(pk=customer_id)
        if feedback_date:
            feedback.feedback_date = feedback_date
        if feedback_type:
            feedback.feedback_type = feedback_type
        if subject:
            feedback.subject = subject
        if description:
            feedback.description = description
        if feedback_status:
            feedback.feedback_status = feedback_status

        feedback.save()

        try:
            log_audit_trail(request.user.id,'Customer Feedback Registration', feedback, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Customer feedback updated successfully")

    except CustomerFeedBack.DoesNotExist:
        return error(f"Customer feedback with ID {feedback_id} not found")
    except Customer.DoesNotExist:
        return error("Invalid Customer ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_customer_feedback(feedback_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        feedback = CustomerFeedBack.objects.get(pk=feedback_id)
        feedback.delete()

        try:
            log_audit_trail(request.user.id,'Customer Feedback Registration', feedback, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Customer feedback with ID {feedback_id} deleted successfully")

    except CustomerFeedBack.DoesNotExist:
        return error(f"Customer feedback with ID {feedback_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")



def calculate_repayment_schedule(loan_amount, interest_rate, tenure, tenure_type, repayment_schedule, loan_calculation_method, repayment_start_date, repayment_mode):
    """
    Main function to execute the repayment calculations based on the selected method.
    
    Parameters:
    loan_amount (Decimal): The total loan amount.
    interest_rate (Decimal): The interest rate applied on the loan.
    tenure (int): The tenure of the loan (e.g., in months or years).
    tenure_type (str): Specifies whether the tenure is in 'months' or 'years'.
    repayment_schedule (str): The schedule of repayments ('monthly', 'quarterly', etc.).
    loan_calculation_method (str): The method used for loan calculation (e.g., 'reducing_balance', 'flat_rate').
    repayment_start_date (str): The start date for repayment.
    repayment_mode (str): The repayment mode ('principal_only', 'interest_only', 'both', etc.).

    Returns:
    repayment_plan (list): A list containing the repayment plan details.
    """
    # Convert the tenure to days based on the tenure type (months, years)
    tenure_in_days = convert_tenure_to_days(tenure, tenure_type)
    
    # Determine the number of periods and the interval (e.g., monthly, quarterly) for repayments
    periods, interval = determine_periods_and_interval(tenure_in_days, repayment_schedule)
    
    # Select the appropriate loan calculation method
    if loan_calculation_method == 'reducing_balance':
        repayment_plan = calculate_reducing_balance(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'flat_rate':
        repayment_plan = calculate_flat_rate(loan_amount, interest_rate,tenure, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'constant_repayment':
        repayment_plan = calculate_constant_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'simple_interest':
        repayment_plan = calculate_simple_interest(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'compound_interest':
        repayment_plan = calculate_compound_interest(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'graduated_repayment':
        repayment_plan = calculate_graduated_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'balloon_payment':
        repayment_plan = calculate_balloon_payment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode, balloon_percentage=20)  # Example percentage
    elif loan_calculation_method == 'bullet_repayment':
        repayment_plan = calculate_bullet_repayment(loan_amount, interest_rate, periods, interval, repayment_start_date, repayment_mode)
    elif loan_calculation_method == 'interest_first':
        repayment_plan = calculate_interest_only(loan_amount, interest_rate, periods, interval, repayment_start_date)
    else:
        raise ValueError(f"Unsupported loan calculation method: {loan_calculation_method}")

    # Display the repayment schedule in a table (Optional: You can adjust how to display it)
    display_repayment_table(repayment_plan)
    return success(repayment_plan)



# =========================== Start Masters ===============================
def create_identificationtype(company_id,type_name, description, is_active):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = IdentificationType.objects.create(
            company_id_id = company_id,
            type_name = type_name,
            description = description,
            is_active = is_active,
        )
        try:
            log_audit_trail(request.user.id,'IdentificationType Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return error(f"Validation Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        return error(f"An error occurred: {e}")

def update_identificationtype(identificationtype_id,type_name=None, description=None, is_active=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = IdentificationType.objects.get(pk = identificationtype_id)
        instance.type_name = type_name if type_name is not None else instance.type_name
        instance.description = description if description is not None else instance.description
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'IdentificationType Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except  IdentificationType.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_identificationtype(identificationtype_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')  
        
        if identificationtype_id is not None:
            record = IdentificationType.objects.get(pk=identificationtype_id)
            serializer = IdentificationtypeSerializer(record)
        elif company_id is not None:
            records = IdentificationType.objects.filter(company_id_id = company_id)
            serializer = IdentificationtypeSerializer(records, many=True)
        else:
            records = IdentificationType.objects.all()
            serializer = IdentificationtypeSerializer(records, many=True)
        return success(serializer.data)
    except IdentificationType.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Identificationtype does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_identificationtype(identificationtype_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        instance = IdentificationType.objects.get(pk=identificationtype_id)
        instance.delete()
        try:
            log_audit_trail(request.user.id,'IdentificationType Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except IdentificationType.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_loantype(company_id,loantype,disbursement_beneficiary=None,interest_rate=None,loan_teams=None,min_loan_amt=None,max_loan_amt=None,eligibility=None,collateral_required=False,charges=None,is_active=False,description = None ):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')    

        if company_id is not None: 
            Company.objects.get(pk=company_id)

        # generate Unique id 
        generate_id = LoanType.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.loantype_id[9:]
        loantype_id = unique_id('LT',last_id)

        instance = LoanType.objects.create(
            company_id = company_id,
            loantype_id = loantype_id,
            loantype = loantype, # personal loan, housing loan
            description = description,
            interest_rate = interest_rate, # percentage
            loan_teams = loan_teams, # Standard loan term duration for this type, in months.
            min_loan_amt = min_loan_amt,
            max_loan_amt = max_loan_amt,
            disbursement_beneficiary = disbursement_beneficiary,
            eligibility = eligibility, # Conditions a borrower must meet to qualify for this loan.
            collateral_required = collateral_required,
            charges = charges, # Any associated fees like processing or administration fees.
            is_active = is_active,
            )
        try:
            log_audit_trail(request.user.id,'LoanType Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_loantype(company_id,loantype_id,loantype,disbursement_beneficiary=None,interest_rate=None,loan_teams=None,min_loan_amt=None,max_loan_amt=None,eligibility=None,collateral_required=False,charges=None,is_active=False,description = None ):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)

        instance = LoanType.objects.get(pk=loantype_id)

        instance.company_id_id = company_id if company_id is not None else instance.company_id.id
        instance.loantype = loantype if loantype is not None else instance.loantype
        instance.disbursement_beneficiary = disbursement_beneficiary if disbursement_beneficiary is not None else instance.disbursement_beneficiary
        instance.description = description if description is not None else instance.description
        instance.interest_rate = interest_rate if interest_rate is not None else instance.interest_rate
        instance.loan_teams = loan_teams if loan_teams is not None else instance.loan_teams
        instance.min_loan_amt = min_loan_amt if min_loan_amt is not None else instance.min_loan_amt
        instance.max_loan_amt = max_loan_amt if max_loan_amt is not None else instance.max_loan_amt
        instance.eligibility = eligibility if eligibility is not None else instance.eligibility
        instance.collateral_required = collateral_required if collateral_required is not None else instance.collateral_required
        instance.charges = charges if charges is not None else instance.charges
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.save()
        try:
            log_audit_trail(request.user.id,'LoanType Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except ValidationError as e:    
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loantype(loantype_id=None,company_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        if loantype_id is not None:
            record = LoanType.objects.get(pk=loantype_id)
            serializer = LoanTypeSerializer(record)

        elif company_id is not None:
            records = LoanType.objects.filter(company_id = company_id)
            serializer = LoanTypeSerializer(records, many=True)
        else:
            records = LoanType.objects.all()
            serializer = LoanTypeSerializer(records, many=True)
        return success(serializer.data)
    
    except LoanType.DoesNotExist:
        return error('LoanType does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_loantype(loantype_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = LoanType.objects.get(pk=loantype_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'LoanType Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except LoanType.DoesNotExist:
        return error('LoanType does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    



def create_collateraltype(company_id,name, description,category):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        instance = CollateralType.objects.create(
            company_id = company_id,
            name=name,
            description=description,
            category = category,
        )
        try:
            log_audit_trail(request.user.id,'CollateralType Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_collateraltype(company_id,collateraltype_id,name=None, description=None,category = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = CollateralType.objects.get(pk=collateraltype_id)
        instance.name = name if name is not None else instance.name
        instance.description = description if description is not None else instance.description
        instance.category = category if category is not None else instance.category
        instance.save()
        try:
            log_audit_trail(request.user.id,'CollateralType Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except  CollateralType.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_collateraltype(collateraltype_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if collateraltype_id is not None:
            record = CollateralType.objects.get(pk=collateraltype_id)
            serializer = CollateraltypeSerializer(record)
        elif company_id is not None:
            record = CollateralType.objects.filter(company_id=company_id)
            serializer = CollateraltypeSerializer(record, many=True)
        else:
            records = CollateralType.objects.all()
            serializer = CollateraltypeSerializer(records, many=True)
        return success(serializer.data)
    
    except CollateralType.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Collateraltype does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_collateraltype(collateraltype_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = CollateralType.objects.get(pk=collateraltype_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'CollateralType Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success("Successfully deleted")
    
    except CollateralType.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_paymentmethod(company_id,method_name, description, is_active):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = PaymentMethod.objects.create(
            company_id = company_id,
            method_name=method_name,
            description=description,
            is_active=is_active,
        )

        try:
            log_audit_trail(request.user.id,'PaymentMethod Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_paymentmethod(paymentmethod_id,company_id,method_name=None, description=None, is_active=False):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = PaymentMethod.objects.get(pk=paymentmethod_id)
        instance.method_name = method_name if method_name is not None else instance.method_name
        instance.description = description if description is not None else instance.description
        instance.is_active = is_active
        instance.save()

        try:
            log_audit_trail(request.user.id,'PaymentMethod Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Successfully Updated')
    except  PaymentMethod.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_paymentmethod(paymentmethod_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if paymentmethod_id is not None:
            record = PaymentMethod.objects.get(pk=paymentmethod_id)
            serializer = PaymentmethodSerializer(record)
        elif company_id is not None:
            records = PaymentMethod.objects.filter(company_id = company_id)
            serializer = PaymentmethodSerializer(records, many=True)
        else:
            records = PaymentMethod.objects.all()
            serializer = PaymentmethodSerializer(records, many=True)
        return success(serializer.data)
    
    except PaymentMethod.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Paymentmethod does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_paymentmethod(paymentmethod_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = PaymentMethod.objects.get(pk=paymentmethod_id)
        instance.delete()

        try:
            log_audit_trail(request.user.id,'PaymentMethod Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success("Successfully deleted")
    
    except PaymentMethod.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_currency(company_id,code, name, symbol, exchange_rate, is_active=False):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Currency.objects.create(
            company_id = company_id,
            code = code,
            name = name,
            symbol = symbol,
            exchange_rate = exchange_rate,
            is_active=is_active,
        )

        try:
            log_audit_trail(request.user.id,'Currency Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f'Successfully created {instance}')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_currency(company_id,currency_id,code=None, name=None, symbol=None, exchange_rate=None, is_active=False):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Currency.objects.get(pk=currency_id)
        instance.code = code if code is not None else instance.code
        instance.name = name if name is not None else instance.name
        instance.symbol = symbol if symbol is not None else instance.symbol
        instance.exchange_rate = exchange_rate if exchange_rate is not None else instance.exchange_rate
        instance.is_active = is_active
        instance.save()
        try:
            log_audit_trail(request.user.id,'Currency Registration', instance, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success('Successfully Updated')
    except  Currency.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_currency(currency_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if currency_id is not None:
            record = Currency.objects.get(pk=currency_id)
            serializer = CurrencySerializer(record)
        elif company_id is not None:
            records = Currency.objects.filter(company_id = company_id)
            serializer = CurrencySerializer(records, many=True)
        else:
            records = Currency.objects.all()
            serializer = CurrencySerializer(records, many=True)
        return success(serializer.data)
    
    except Currency.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Currency does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_currency(currency_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Currency.objects.get(pk=currency_id)
        instance.delete()
        try:
            log_audit_trail(request.user.id,'Currency Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        
        return success("Successfully deleted")
    
    except Currency.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_bank_account(company_id,account_number, account_holder_name, bank_name, branch, nrfc_number=None, swift_code=None, ifsc_code=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        # Create a new BankAccount instance
        bank_account = BankAccount.objects.create(
            company_id = company_id,
            account_number=account_number,
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            branch=branch,
            nrfc_number=nrfc_number,
            swift_code=swift_code,
            ifsc_code=ifsc_code
        )
        try:
            log_audit_trail(request.user.id,'BankAccount Registration', bank_account, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        

        return success(f"Bank account created successfully with ID: {bank_account.id}")
    
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def view_bank_account(account_number=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        if account_number:
            # Fetch a specific bank account by account number
            bank_account = BankAccount.objects.get(id=account_number)
            serializer = BankAccountSerializer(bank_account)
        elif company_id is not None:
            bank_accounts = BankAccount.objects.filter(company_id = company_id)
            serializer = BankAccountSerializer(bank_accounts, many=True)
        else:
            # Fetch all bank accounts
            bank_accounts = BankAccount.objects.all()
            serializer = BankAccountSerializer(bank_accounts, many=True)
        
        return success(serializer.data)
    
    except BankAccount.DoesNotExist:
        return error(f"Bank account with number {account_number} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_bank_account(bank_id,company_id,account_number, account_holder_name=None, bank_name=None, branch=None, nrfc_number=None, swift_code=None, ifsc_code=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        # Find the bank account by account number
        bank_account = BankAccount.objects.get(id=bank_id)
        
        # Update fields if provided
        bank_account.account_holder_name = account_holder_name if account_holder_name else bank_account.account_holder_name
        bank_account.bank_name_id = bank_name if bank_name else bank_account.bank_name
        bank_account.branch = branch if branch else bank_account.branch
        bank_account.nrfc_number = nrfc_number if nrfc_number else bank_account.nrfc_number
        bank_account.swift_code = swift_code if swift_code else bank_account.swift_code
        bank_account.ifsc_code = ifsc_code if ifsc_code else bank_account.ifsc_code
        
        bank_account.save()
        try:
            log_audit_trail(request.user.id,'BankAccount Registration', bank_account, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Bank account updated successfully with ID: {bank_account.id}")
    
    except BankAccount.DoesNotExist:
        return error(f"Bank account with number account_number not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_bank_account(back_id,account_number=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if account_number is not None:
            # Find the bank account by account number
            bank_account = BankAccount.objects.get(account_number=account_number)
            bank_account.delete()
        else:
            bank_account = BankAccount.objects.get(id=back_id)
            bank_account.delete()
        try:
            log_audit_trail(request.user.id,'BankAccount Registration', bank_account, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Bank account with number {account_number} deleted successfully")
    
    except BankAccount.DoesNotExist:
        return error(f"Bank account with number {account_number} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def create_creditscores(company_id, customer_id, credit_score, retrieved_at):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)

        # generate Unique id 
        generate_id = Creditscores.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.scores_id[9:]
        scores_id = unique_id('CS',last_id)
        
        instance = Creditscores.objects.create(
            company_id=company_id,
            scores_id=scores_id,
            customer_id_id=customer_id,
            credit_score=credit_score,
            retrieved_at=retrieved_at,
        )
        try:
            log_audit_trail(request.user.id,'Creditscores Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_creditscores(creditscores_id,company_id=None, scores_id=None, customer_id=None, credit_score=None, retrieved_at=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None: 
            Company.objects.get(pk=company_id)
        if customer_id is not None: 
            Customer.objects.get(pk=customer_id)

        instance = Creditscores.objects.get(pk=creditscores_id)
        instance.company_id = company_id if company_id is not None else instance.company_id
        instance.scores_id = scores_id if scores_id is not None else instance.scores_id
        instance.customer_id_id = customer_id if customer_id is not None else instance.customer_id
        instance.credit_score = credit_score if credit_score is not None else instance.credit_score
        instance.retrieved_at = retrieved_at if retrieved_at is not None else instance.retrieved_at
        instance.save()

        try:
            log_audit_trail(request.user.id,'Creditscores Registration', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success('Successfully Updated')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except  Creditscores.DoesNotExist:
        return error('Instance does not exist')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_creditscores(creditscores_id=None,company_id = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if creditscores_id is not None:
            record = Creditscores.objects.get(pk=creditscores_id)
            serializer = CreditscoresSerializer(record)
        elif company_id is not None:
            records = Creditscores.objects.filter(company_id = company_id)
            serializer = CreditscoresSerializer(records, many=True)
        else:
            records = Creditscores.objects.all()
            serializer = CreditscoresSerializer(records, many=True)
        return success(serializer.data)
    
    except Creditscores.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Creditscores does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def delete_creditscores(creditscores_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Creditscores.objects.get(pk=creditscores_id)
        instance.delete()
        try:
            log_audit_trail(request.user.id,'Creditscores Registration', instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Successfully deleted")
    
    except Creditscores.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_loan_offer(company_id, application_id, loanamount, interest_rate, tenure, monthly_instalment, terms_condition=None, offer_status='Pending'):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        company = Company.objects.get(pk=company_id)
        application = LoanApplication.objects.get(pk=application_id)

        # Generate a unique offer ID
        last_offer = LoanOffer.objects.last()
        last_id = '0000'
        if last_offer:
            last_id = last_offer.offer_id[5:]
        offer_id = unique_id('LO', last_id)

        # Create the loan offer
        offer = LoanOffer.objects.create(
            company=company,
            offer_id=offer_id,
            application_id=application,
            loanamount=loanamount,
            interest_rate=interest_rate,
            tenure=tenure,
            monthly_instalment=monthly_instalment,
            terms_condition=terms_condition,
            offer_status=offer_status
        )

        try:
            log_audit_trail(request.user.id,'LoanOffer Registration', offer, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success(f"Loan offer created successfully with ID: {offer.offer_id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loan_offer(offer_id=None, application_id=None, company_id=None):
    try:
        if offer_id:
            offer = LoanOffer.objects.get(pk=offer_id)
            serializer = LoanOfferSerializer(offer)
        elif application_id:
            offers = LoanOffer.objects.filter(application_id=application_id)
            serializer = LoanOfferSerializer(offers, many=True)
        elif company_id:
            offers = LoanOffer.objects.filter(company_id=company_id)
            serializer = LoanOfferSerializer(offers, many=True)
        else:
            offers = LoanOffer.objects.all()
            serializer = LoanOfferSerializer(offers, many=True)

        return success(serializer.data)

    except LoanOffer.DoesNotExist:
        return error(f"Loan offer with ID {offer_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_loan_offer(offer_id, company_id=None, application_id=None, loanamount=None, interest_rate=None, tenure=None, monthly_instalment=None, terms_condition=None, offer_status=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        offer = LoanOffer.objects.get(pk=offer_id)

        if company_id:
            offer.company = Company.objects.get(pk=company_id)
        if application_id:
            offer.application_id = LoanApplication.objects.get(pk=application_id)
        if loanamount is not None:
            offer.loanamount = loanamount
        if interest_rate is not None:
            offer.interest_rate = interest_rate
        if tenure is not None:
            offer.tenure = tenure
        if monthly_instalment is not None:
            offer.monthly_instalment = monthly_instalment
        if terms_condition is not None:
            offer.terms_condition = terms_condition
        if offer_status is not None:
            offer.offer_status = offer_status

        offer.save()
        try:
            log_audit_trail(request.user.id,'LoanOffer Registration', offer, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success("Loan offer updated successfully")

    except LoanOffer.DoesNotExist:
        return error(f"Loan offer with ID {offer_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_loan_offer(offer_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        offer = LoanOffer.objects.get(pk=offer_id)
        offer.delete()
        try:
            log_audit_trail(request.user.id,'LoanOffer Registration', offer, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Loan offer with ID {offer_id} deleted successfully")

    except LoanOffer.DoesNotExist:
        return error(f"Loan offer with ID {offer_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_repayment_schedule(company_id, loan_application_id, repayment_date, instalment_amount, principal_amount, interest_amount, remaining_balance, repayment_status, payment_method_id, transaction_id=None, notes=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')


        company = Company.objects.get(pk=company_id)
        loan_application = LoanApplication.objects.get(pk=loan_application_id)
        payment_method = PaymentMethod.objects.get(pk=payment_method_id)

        # Create the repayment schedule
        repayment_schedule = RepaymentSchedule.objects.create(
            company=company,
            loan_application=loan_application,
            repayment_date=repayment_date,
            instalment_amount=instalment_amount,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            remaining_balance=remaining_balance,
            repayment_status=repayment_status,
            payment_method=payment_method,
            transaction_id=transaction_id,
            notes=notes
        )
        try:
            log_audit_trail(request.user.id,'RepaymentSchedule Registration', repayment_schedule, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Repayment schedule created successfully with ID: {repayment_schedule.id}")

    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except PaymentMethod.DoesNotExist:
        return error("Invalid Payment Method ID")
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_repayment_schedule(repayment_schedule_id=None, company_id=None):
    try:
        if repayment_schedule_id:
            repayment_schedule = RepaymentSchedule.objects.get(pk=repayment_schedule_id)
            serializer = RepaymentscheduleSerializer(repayment_schedule)
        elif company_id:
            repayment_schedules = RepaymentSchedule.objects.filter(company_id=company_id)
            serializer = RepaymentscheduleSerializer(repayment_schedules, many=True)
        else:
            repayment_schedules = RepaymentSchedule.objects.all()
            serializer = RepaymentscheduleSerializer(repayment_schedules, many=True)

        return success(serializer.data)

    except RepaymentSchedule.DoesNotExist:
        return error(f"Repayment Schedule with ID {repayment_schedule_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def update_repayment_schedule(repayment_schedule_id, company_id=None, loan_application_id=None, repayment_date=None, instalment_amount=None, principal_amount=None, interest_amount=None, remaining_balance=None, repayment_status=None, payment_method_id=None, transaction_id=None, notes=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        repayment_schedule = RepaymentSchedule.objects.get(pk=repayment_schedule_id)

        if company_id:
            repayment_schedule.company = Company.objects.get(pk=company_id)
        if loan_application_id:
            repayment_schedule.loan_application = LoanApplication.objects.get(pk=loan_application_id)
        if repayment_date:
            repayment_schedule.repayment_date = repayment_date
        if instalment_amount:
            repayment_schedule.instalment_amount = instalment_amount
        if principal_amount:
            repayment_schedule.principal_amount = principal_amount
        if interest_amount:
            repayment_schedule.interest_amount = interest_amount
        if remaining_balance:
            repayment_schedule.remaining_balance = remaining_balance
        if repayment_status:
            repayment_schedule.repayment_status = repayment_status
        if payment_method_id:
            repayment_schedule.payment_method = PaymentMethod.objects.get(pk=payment_method_id)
        if transaction_id:
            repayment_schedule.transaction_id = transaction_id
        if notes:
            repayment_schedule.notes = notes

        repayment_schedule.save()
        try:
            log_audit_trail(request.user.id,'RepaymentSchedule Registration', repayment_schedule, 'Update', 'Object Updated.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        return success("Repayment schedule updated successfully")

    except RepaymentSchedule.DoesNotExist:
        return error(f"Repayment Schedule with ID {repayment_schedule_id} not found")
    except Company.DoesNotExist:
        return error("Invalid Company ID")
    except LoanApplication.DoesNotExist:
        return error("Invalid Loan Application ID")
    except PaymentMethod.DoesNotExist:
        return error("Invalid Payment Method ID")
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_repayment_schedule(repayment_schedule_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')        
        repayment_schedule = RepaymentSchedule.objects.get(pk=repayment_schedule_id)
        repayment_schedule.delete()
        try:
            log_audit_trail(request.user.id,'RepaymentSchedule Registration', repayment_schedule, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success(f"Repayment schedule with ID {repayment_schedule_id} deleted successfully")

    except RepaymentSchedule.DoesNotExist:
        return error(f"Repayment Schedule with ID {repayment_schedule_id} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")




# def update_loan(loan_id,company_id=None, loanid=None, customer_id=None, loan_amount=None, loan_date=None, loan_term=None, interest_rate=None, status=None):
#     """
#     Updates a Loan instance with the provided data.
    
#     Args:
#         loan_id (int): ID of the Loan to update.
#         company_id=None, loanid=None, customer_id=None, loan_amount=None, loan_date=None, loan_term=None, interest_rate=None, status=None: Keyword arguments for Loan fields to update.

#     Returns:
#         dict: Success or error message.
#     """
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         if company_id is not None and company_id != '': 
#              Company.objects.get(pk=company_id)
#         if customer_id is not None and customer_id != '': 
#              Customer.objects.get(pk=customer_id)
#         instance = Loan.objects.get(pk=loan_id)
#         instance.company_id = company_id if company_id is not None else instance.company_id
#         instance.loanid = loanid if loanid is not None else instance.loanid
#         instance.customer_id = customer_id if customer_id is not None else instance.customer_id
#         instance.loan_amount = loan_amount if loan_amount is not None else instance.loan_amount
#         instance.loan_date = loan_date if loan_date is not None else instance.loan_date
#         instance.loan_term = loan_term if loan_term is not None else instance.loan_term
#         instance.interest_rate = interest_rate if interest_rate is not None else instance.interest_rate
#         instance.status = status if status is not None else instance.status
#         instance.save()
#         return success('Successfully Updated')
#     except Company.DoesNotExist:
#         return error('Invalid Company ID: Destination not found.')
#     except Customer.DoesNotExist:
#         return error('Invalid Customer ID: Destination not found.')
#     except  Loan.DoesNotExist:
#         return error('Instance does not exist')
#     except ValidationError as e:
#         return error(f"Validation Error: {{e}}")
#     except Exception as e:
#         return error(f"An error occurred: {{e}}")



# def delete_loan(loan_id):
#     """
#     Deletes a Loan instance with the given ID.
    
#     Args:
#         loan_id (int): ID of the Loan to delete.

#     Returns:
#         dict: A success response if deletion is successful,
#               or an error response if an exception occurs.
#     """
    
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         instance = Loan.objects.get(pk=loan_id)
#         instance.delete()
#         return success("Successfully deleted")
    
#     except Loan.DoesNotExist:
#         return error('Instance does not exist')
#     except Exception as e:
#         return error(f"An error occurred: {{e}}")
# def create_notifications(company_id, notification_id, customer_id_id, message, status, priority):
#     """
#     Creates a Notifications instance with the provided data.
#         Args:
#         company_id, notification_id, customer_id_id, message, status, priority: Keyword arguments for Notifications fields.

#     Returns:
#         dict: Success or error message.
#     """
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         if company_id is not None and company_id != '': 
#              Company.objects.get(pk=company_id)
#         if customer_id_id is not None and customer_id_id != '': 
#              Customer.objects.get(pk=customer_id_id)
#         instance = Notifications.objects.create(
#             company_id=company_id,
#             notification_id=notification_id,
#             customer_id_id=customer_id_id,
#             message=message,
#             status=status,
#             priority=priority,
#         )
#         return success(f'Successfully created {instance}')
#     except Company.DoesNotExist:
#         return error('Invalid Company ID: Destination not found.')
#     except Customer.DoesNotExist:
#         return error('Invalid Customer ID: Destination not found.')
#     except ValidationError as e:
#         return error(f"Validation Error: {e}")
#     except Exception as e:
#         return error(f"An error occurred: {e}")

# def update_notifications(notifications_id,company_id=None, notification_id=None, customer_id_id=None, message=None, status=None, priority=None):
#     """
#     Updates a Notifications instance with the provided data.
    
#     Args:
#         notifications_id (int): ID of the Notifications to update.
#         company_id=None, notification_id=None, customer_id_id=None, message=None, status=None, priority=None: Keyword arguments for Notifications fields to update.

#     Returns:
#         dict: Success or error message.
#     """
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         if company_id is not None and company_id != '': 
#              Company.objects.get(pk=company_id)
#         if customer_id_id is not None and customer_id_id != '': 
#              Customer.objects.get(pk=customer_id_id)
#         instance = Notifications.objects.get(pk=notifications_id)
#         instance.company_id = company_id if company_id is not None else instance.company_id
#         instance.notification_id = notification_id if notification_id is not None else instance.notification_id
#         instance.customer_id_id = customer_id_id if customer_id_id is not None else instance.customer_id_id
#         instance.message = message if message is not None else instance.message
#         instance.status = status if status is not None else instance.status
#         instance.priority = priority if priority is not None else instance.priority
#         instance.save()
#         return success('Successfully Updated')
#     except Company.DoesNotExist:
#         return error('Invalid Company ID: Destination not found.')
#     except Customer.DoesNotExist:
#         return error('Invalid Customer ID: Destination not found.')
#     except  Notifications.DoesNotExist:
#         return error('Instance does not exist')
#     except ValidationError as e:
#         return error(f"Validation Error: {{e}}")
#     except Exception as e:
#         return error(f"An error occurred: {{e}}")

# def view_notifications(notifications_id=None):
#     """
#     Retrieves and serializes a Notifications instance by its ID or all instances if ID is None.
    
#     Args:
#         Notifications_id (int, optional): ID of the Notifications to retrieve.

#     Returns:
#         dict: A success response with the serialized data if found,
#               or an error response if an exception occurs.
#     """
    
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         if notifications_id is not None:
#             record = Notifications.objects.get(pk=notifications_id)
#             serializer = NotificationsSerializer(record)
#         else:
#             records = Notifications.objects.all()
#             serializer = NotificationsSerializer(records, many=True)
#         return success(serializer.data)
    
#     except Notifications.DoesNotExist:
#         # Return an error response if the {model_name} does not exist
#         return error('Notifications does not exist')
#     except Exception as e:
#         # Return an error response with the exception message
#         return error(f"An error occurred: {{e}}")

# def delete_notifications(notifications_id):
#     """
#     Deletes a Notifications instance with the given ID.
    
#     Args:
#         notifications_id (int): ID of the Notifications to delete.

#     Returns:
#         dict: A success response if deletion is successful,
#               or an error response if an exception occurs.
#     """
    
#     try:
#         request = get_current_request()
#         if not request.user.is_authenticated:
#             return error('Login required')
        
#         instance = Notifications.objects.get(pk=notifications_id)
#         instance.delete()
#         return success("Successfully deleted")
    
#     except Notifications.DoesNotExist:
#         return error('Instance does not exist')
#     except Exception as e:
#         return error(f"An error occurred: {{e}}")

# ===================  Credit Scores ================

# def calculate_credit_score(customer_id):
#     """
#     Calculates the credit score for a customer based on various factors such as 
#     loan history and payment behavior.
    
#     The logic here is a placeholder. You can replace it with more sophisticated 
#     business rules or fetch from an external service.
#     """

#     try:
#         # Fetch the customer
#         customer = Customer.objects.get(pk=customer_id)

#         # Retrieve all loans and payments made by the customer
#         loans = Loan.objects.filter(customer_id=customer_id)
#         payments = Payment.objects.filter(loan__customer_id=customer_id)

#         # Initialize a base credit score
#         base_score = 650

#         # Penalize for any unpaid loans or delayed payments
#         for loan in loans:
#             if loan.balance > 0:  # Loan still has balance
#                 base_score -= 10  # Decrease score for unpaid loans

#         # Bonus points for consistent payments
#         for payment in payments:
#             if payment.payment_date <= loan.payment_due_date:
#                 base_score += 5  # Increase score for timely payments

#         # Cap the score between 300 and 850
#         if base_score < 300:
#             base_score = 300
#         if base_score > 850:
#             base_score = 850

#         return base_score
    
#     except Customer.DoesNotExist:
#         raise ValueError("Customer does not exist")
#     except Exception as e:
#         raise ValueError(f"An error occurred while calculating the credit score: {e}")



#======================DMS===============

def entity_master_view(entity_id=None):
    print("entity_master_view34567890")
    try:
        if entity_id:
            if isinstance(entity_id,int):
                records = CustomDocumentEntity.objects.filter(id=entity_id)
            else:
                records = CustomDocumentEntity.objects.filter(entity_id=entity_id)
            if records.exists():
                record = records.last()
                serializer = CustomDocumentEntitySerializer(record)
            return success(serializer.data)
        else:
            records = CustomDocumentEntity.objects.all()
            serializer = CustomDocumentEntitySerializer(records,many=True)
            return success(serializer.data)
    except Exception as e:
        return error(e)
    
def entity_folders_list(entity_id):
    try:
        print("entity_iderrort67890+++;;;;",entity_id)
        entity_instance = CustomDocumentEntity.objects.get(entity_id=entity_id)
        print('entity_instance=====',entity_instance)
        records = FolderMaster.objects.filter(entity=entity_instance,default_folder=True)
        serializer = FolderMasterSerializer(records,many=True)
        return success(serializer.data)
    except CustomDocumentEntity.DoesNotExist:
        return error('Entity_id is invalid')
    except Exception as e:
        return error(e)  
    
def folder_master_view(folder_id=None):
    print('folder_idiuiuy789098',folder_id)
    try:
        if folder_id:
            records = FolderMaster.objects.filter(parent_folder__folder_id=folder_id)
            serializer = FolderMasterSerializer(records,many=True)
            return success(serializer.data)
        else:
            records = FolderMaster.objects.filter(parent_folder__isnull=True)
            serializer = FolderMasterSerializer(records,many=True)
            return error(serializer.data)
    except Exception as e:
        print('folder_list',e)
        return error(e)


def folder_documents_list(folder_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        print("folder_id--",folder_id)          
        records = DocumentUpload.objects.filter(folder__folder_id=folder_id)
        print("records___folder",records)
        document_data = []
        for data in records:
       
            doc_obj = DocumentAccess.objects.filter(document_id=data.document_id,access_to=request.user).last()
           
            if request.user.is_superuser:
                permission = ['edit', 'view', 'download', 'delete','share']
            else:
              
                if doc_obj:
                   expiry_time = is_valid_current_datetime(doc_obj.expiry_from_at, doc_obj.expiry_to_at)
                   print('expiry_time',expiry_time)
                   if expiry_time:
                        permission = doc_obj.permission
                   else:
                       permission=[]
                else:
                    permission = []
            if data.end_date and data.start_date:
                remaining_days = (data.end_date - data.start_date).days
            else: 
                remaining_days = None    
            print(f"Remaining days: {remaining_days}")            

            document_data.append({                       
                'document_id': data.document_id,
                'document_title': data.document_title,
                'folder': data.folder.folder_id,
                'document_size': data.document_size,
                'description': data.description,
                'document_upload': settings.MEDIA_URL + data.document_upload.name if data.document_upload else None,
                'upload_date': data.upload_date,
                'update_at': data.update_at,
                'start_date':data.start_date,
                'remaining_days':remaining_days,
                'end_date':data.end_date,
                'permission': permission,
              
            })
        return success(document_data)
    except Exception as e:
        return error(str(e))


def document_category_view(document_category_id=None):
    try:
        if document_category_id:
            records = DocumentCategory.objects.filter(id=document_category_id)
            if records.exists():
                record=records.last()
                serializer = DocumentCategorySerializer(record)
                return success(serializer.data)
            else:
                return error('document_category_id is invalid')
        else:
            records = DocumentCategory.objects.all()
            serializer = DocumentCategorySerializer(records,many=True)
            return success(serializer.data)
    except Exception as e:
        return error(e)
    
def document_type_view(document_type_id=None):
    try:
        if document_type_id:

            records = DocumentType.objects.filter(id=document_type_id)
            if records.exists():
                record=records.last()
                serializer = DocumentTypeSerializer(record)
                return success(serializer.data)
            else:
                return error('document_type_id is invalid')
        else:
            records = DocumentType.objects.all()
            serializer = DocumentTypeSerializer(records,many=True)
            return success(serializer.data)
    except Exception as e:
        return error(e)


def folder_master_create(folder_name, entity_id, default_folder=False, customer_id=None, company_id=None, description=None, parent_folder_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        obj_count=FolderMaster.objects.all().count()

        if customer_id:
            customer_instances=Customer.objects.filter(id=customer_id)
            if customer_instances.exists():
                customer_id = customer_instances.last()
            else:
                return error("customer_id is invalid")
        print('customer_id99099',customer_id)
        if company_id:
            company_instances=Company.objects.filter(id=company_id)
            print('company_instances',company_instances)
            if company_instances.exists():
                company_id = company_instances.last()
            else:
                return error("company_id is invalid")
            
        if parent_folder_id:
            parent_folder=FolderMaster.objects.filter(folder_id=parent_folder_id)
            if parent_folder.exists():
                parent_folder_id = parent_folder.last()
                company_id = parent_folder_id.company
            else:
                return error("parent_folder_id is invalid")
        entity_instance = CustomDocumentEntity.objects.get(entity_id=entity_id)
        record = FolderMaster.objects.create(
            folder_id=unique_id('FID',obj_count),
            folder_name=folder_name,
            description=description,
            parent_folder=parent_folder_id,
            entity=entity_instance,
            customer=customer_id,
            company=company_id,
            default_folder=default_folder,
            created_by=request.user,
            update_by=request.user
        )  
        try:
            log_audit_trail(request.user.id,'FolderMaster Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Folder created successfully')
    except CustomDocumentEntity.DoesNotExist:
        return error('Entity_id is invalid')
    except Exception as e:
        return error(e)


def document_category_view(document_category_id=None):
    try:
        if document_category_id:
            records = DocumentCategory.objects.filter(id=document_category_id)
            if records.exists():
                record=records.last()
                serializer = DocumentCategorySerializer(record)
                return success(serializer.data)
            else:
                return error('document_category_id is invalid')
        else:
            records = DocumentCategory.objects.all()
            serializer = DocumentCategorySerializer(records,many=True)
            return success(serializer.data)
    except Exception as e:
        return error(e)



def department_view(department_id=None):
    try:
        if department_id:
            records = Department.objects.filter(id=department_id)
            if records.exists():
                record=records.last()
                serializer = DepartmentSerializer(record)
                return success(serializer.data)
            else:
                return error('department_id is invalid')
        else:
            records = Department.objects.all()
            serializer = DepartmentSerializer(records,many=True)
            return success(serializer.data)
    except Exception as e:
        return error(e)


def document_category_create(category_name,department_id,description=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        record = DocumentCategory.objects.create(
                category_name=category_name,
                department_id=department_id,
                description=description,
                created_by=request.user,
                update_by=request.user,
            )
        try:
            log_audit_trail(request.user.id,'DocumentCategory Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
    
    
        return success('Document type create successfully')
    except Exception as e:
        return error(e)

def department_create(department_name,description=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        record = Department.objects.create(
                department_name=department_name,
                description=description,
                created_by=request.user,
                update_by=request.user,
            )
        try:
            log_audit_trail(request.user.id,'Department Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")


        return success('Document type create successfully')
    except Exception as e:
        return error(e)

def entity_master_create(entity_id,entity_name,entity_type,description=None,db_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        record = CustomDocumentEntity.objects.create(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                created_by=request.user,
                update_by=request.user,
            )
        try:
            log_audit_trail(request.user.id,'CustomDocumentEntity Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        

        return success('Custom entity create successfully')
    except Exception as e:
        return error(e)    

def document_type_create(document_type_name,short_name,description=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')

        record = DocumentType.objects.create(
                type_name=document_type_name,
                short_name=short_name,
                description=description,
                created_by=request.user,
                update_by=request.user,
            )
        try:
            log_audit_trail(request.user.id,'DocumentType Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        

        return success('Document type create successfully')
    except Exception as e:
        return error(e)
    

def document_upload(document_title,document_category,document_type,entity_type,description,document_upload,folder_id,start_date=None,end_date=None):
    try:
        print('entity_type==+++',entity_type,folder_id)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        # obj_count=DocumentUpload.objects.all().last()

        # print("folder_instance---+++",folder_instance)
    
        folder_instance = FolderMaster.objects.get(folder_id=folder_id)
        print("folder_instance---+++",folder_instance)
        print("document_upload56789",document_upload)
        record = DocumentUpload.objects.create(
                document_id = unique_id_generate_doc('DID'),
                document_title=document_title,
                document_category_id=document_category,
                document_type_id=document_type,
                description=description,
                document_upload=document_upload,
                folder=folder_instance,
                # upload_date=datetime.now(),
                start_date=start_date,
                end_date=end_date,
                created_by=request.user,
                update_by=request.user,
                document_size=document_upload.size,
            )        
        print("document_id///++++",record.document_id) 
        document = document_upload_history(record.document_id)
        print("documentclientup",document)
        document_audit = document_upload_audit('created',record.document_id)
        print("document_upload_history///",document)    
        print("document_audit///",document_audit)          
        for data in entity_type:
            entity = CustomDocumentEntity.objects.get(entity_id=data)
            record.entity_type.add(entity)
            record.save()
        try:
            log_audit_trail(request.user.id,'DocumentUpload Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success('Document uploaded successfully')
    except Exception as e:
        return error(e)   


def document_content_view(document_id):
    try:
        request = get_current_request()
        obj = DocumentUpload.objects.get(document_id=document_id)
        document_url = request.build_absolute_uri(obj.document_upload.url)
        with obj.document_upload.open('rb') as file:
                content = base64.b64encode(file.read()).decode('utf-8')
            
        response = {
            'content': content,  # Read the content of the file
            'url': document_url  # Construct the base URL for the document
        }
        return success(response)
    except DocumentUpload.DoesNotExist:
        return error('document_id is invalid')
    except Exception as e:
        return error(str(e))

def document_version(document_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')       
        print("document_id---",document_id)
        record = DocumentUploadHistory.objects.filter(document_id=document_id).order_by('-version')
        print('record---',record)
        serializer = DocumentUploadHistorySerializer(record,many=True)
        return success(serializer.data)
       
    except DocumentUploadHistory.DoesNotExist:
        return error('Folder id not found')
    except Exception as e:
        return error(e) 

#==================

def folder_delete(entity_id=None,folder_id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')          
        if entity_id:
            entity_instance = CustomDocumentEntity.objects.get(entity_id=entity_id)
            #records = FolderMaster.objects.filter(entity=entity_instance,default_folder=True,matter__isnull=True)
            print('records==-===',entity_instance)
            entity_instance.delete()
            return success('Entity Deleted Sucessfully')
        if folder_id:
            folder_instance=FolderMaster.objects.get(folder_id=folder_id)
            folder_instance.delete()
            return success('Folder Deleted Sucessfully')
        try:
            log_audit_trail(request.user.id,'FolderMaster Registration', folder_instance, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")


    except CustomDocumentEntity.DoesNotExist:
        return error('Entity_id is invalid')
    except Exception as e:
        return error(e)  
    
def document_delete(document_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        obj = DocumentUpload.objects.get(document_id=document_id)
        print("document_delete+++",obj.document_id)
        document_delete=document_upload_audit('deleted',obj.document_id)
        print("document_delete---",document_delete)
        obj.delete()
    
        try:
            log_audit_trail(request.user.id,'DocumentUpload Registration', obj, 'delete', 'Object deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")
     
        return success('Deleted Successfully')
    except DocumentUpload.DoesNotExist:
        return error('document_id is invalid')
    except Exception as e:
        return error(str(e))
