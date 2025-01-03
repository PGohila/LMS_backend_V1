import base64
from pyexpat.errors import messages
from django.core.exceptions import ValidationError
import requests

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
from django.utils.timezone import now
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

        # =============== create central funding account for company ===============
        CentralFundingAccount.objects.create(
            company_id = instance.id,
            account_name = instance.name,
            account_no = f"000{instance.id}",
            account_type = 'investment',
        )

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
      
        create_folder_for_all_customer(customer_id,company_id)
        #==================== createborrower Account ==================
        CustomerAccount.objects.create(
            company_id = company_id,
            customer_id = customer_id,
            account_number = f"B00{customer_id}",
            bank_name = 'BB',
            branch_name = None,
            ifsc_code = None,  # For Indian banks, or SWIFT code for international banks
            account_balance = 0.0,
            account_status = 'active'
        )
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


def create_customer_v1(firstname, lastname, email, phone_number, address, dateofbirth):
    """ ============== Customer Creation ==================="""
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')    

        # if company_id is not None: 
        company_id = Company.objects.all().last().id
        age = 30
        customer_income = 50000
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
         
            expiry_date = datetime.now(),
            is_active = True,
        )
        customer_id=instance.id
      
        create_folder_for_all_customer(customer_id,company_id)
        #==================== createborrower Account ==================
        CustomerAccount.objects.create(
            company_id = company_id,
            customer_id = customer_id,
            account_number = f"B00{customer_id}",
            bank_name = 'BB',
            branch_name = None,
            ifsc_code = None,  # For Indian banks, or SWIFT code for international banks
            account_balance = 0.0,
            account_status = 'active'
        )
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

def getting_customeraccount(customer_id):
    try:
        records = CustomerAccount.objects.get(customer_id = customer_id)
        serializers = CustomerAccountSerializer(records)

        return success(serializers.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def delete_customer(customer_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Customer.objects.get(pk=customer_id)
        try:
            log_audit_trail(request.user.id,'Customer Registration', instance, 'Delete', 'Object Deleted.')
        except Exception as e:
            return error(f"An error occurred: {e}")         
        instance.delete()
        print("instance4567u8io234567",instance)
       
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
            log_audit_trail(request.user.id,'Customer Document Upload', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")
        folder_instance = FolderMaster.objects.filter(customer_id=customer_id, company_id=company_id,folder_name='Common Customer Folder').last()
        start_date=None
        end_date=None
        document_title = attachment.name
        record = DocumentUpload.objects.create(
            document_id = unique_id_generate_doc('DID'),
            company_id=company_id,
            document_title=document_title,
            document_type_id=document_type_id,
            description=description,
            document_upload=attachment,
            folder=folder_instance,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user,
            update_by=request.user,
            document_size=attachment.size,
        )  
        print("record34567890p",record)      
        document_upload_history(record.document_id)

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
            is_active = True,
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
        is_eligible = None
        errors = None
        instance = LoanApplication.objects.filter(is_active = True,company_id = company_id)
        for applications in instance:
            applicant_deatils = Customer.objects.get(pk=applications.customer_id.id)
            existing_loan = Loan.objects.filter(customer_id = applications.id)
            loanids = [data.id for data in existing_loan ]
            # Calculate Exsisting loan liabilities
            existing_loan_liabilities = calculate_existing_liabilities(loanids)
            applicant_deatils.existing_liabilities = existing_loan_liabilities
            applicant_deatils.save()
            print("===================sdfdfd=====")
            # Perform eligibility check
            is_eligible, errors = check_loan_eligibility(applicant_deatils, applications.loan_amount)
            print("========================",is_eligible)
            
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


def post_method(data,BASE_URL,END_POINT):
    try:
        print('data',data)
        url = BASE_URL+END_POINT
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {access_token}"  
        }

        response = requests.post(url, headers=headers, json=data)  
        
        return response.json()

    except requests.exceptions.RequestException as e:
        return error(f"Request error: {e}")  
    except Exception as e:
        return error(f"An error occurred: {e}")

def get_method(BASE_URL,END_POINT):
    try:      
        url = BASE_URL+END_POINT
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {access_token}"  
        }
        response = requests.get(url, headers=headers)  
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return error(f"Request error: {e}")  
    except Exception as e:
        return error(f"An error occurred: {e}")



def loan_approval(company_id,loanapp_id, approval_status = None,rejected_reason = None,loantype_id=None):
    BASE_URL = "https://bbaccountingtest.pythonanywhere.com/loan-setup/"
    
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        instance = LoanApplication.objects.get(pk=loanapp_id)
        if approval_status == "Approved":
            instance.application_status = "Approved"
            instance.workflow_stats = "Approved"
            instance.save()

            # ============ create loan ================
            loan1 = Loan.objects.filter(loanapp_id_id = loanapp_id)
            if loan1:
                return success("Successfully Approved Your Application")
            else:
                loan = create_loan(loanapp_id)
                
            
            loan_id = loan['data']

            # 1. Create Loan Account
     
            loan_account = LoanAccount.objects.create(
                account_no=f'LA00{loan_id}',
                company_id=company_id,
                loan_id=loan['data'],
                principal_amount=0.0,
                outstanding_balance=instance.loan_amount,
            )

            print('loan acc created')
            # 2. Create Loan Disbursement Account

            loan_disbursement_account = LoanDisbursementAccount.objects.create(
                account_no=f'DA00{loan_id}',
                company_id=company_id,
                loan_id=loan['data'],
                amount=0.0,
                loan_account=loan_account,
            )
            print('loan disbursement created')

            # 3. Create Repayment Account
    
            loan_repayment_account = LoanRepaymentAccount.objects.create(
                    account_no=f'RA00{loan_id}',
                    company_id=company_id,
                    loan_id=loan['data'],
                    amount=0.0,  # Initial amount can be set to 0.00
                    payment_method='bank_transfer',  # Default method, adjust as needed
                )

            print('loan repayment created')

            # 4. Create Penalty Account (optional)

            loan_penalty_account = PenaltyAccount.objects.create(
                account_no = f'PA00{loan_id}',
                company_id=company_id,
                loan_id=loan['data'],
                penalty_amount=0.0,  # Initial penalty amount can be set to 0.00
                penalty_reason='N/A',  # Placeholder, adjust as necessary
            )

            # 5. Create Interest Account (optional)
            print('loan penalty created')

            loan_interest_account = InterestAccount.objects.create(
                    account_no = f'IA00{loan_id}',
                    company_id=company_id,
                    loan_id=loan['data'],
                    interest_accrued=0.0,  # Initial interest accrued can be set to 0.00
                )
            print('loan intrest created')
            
            loan_milestone_account = MilestoneAccount.objects.create(
                    # account_no = f'IA00{loan_id}',
                    company_id=company_id,
                    loan_id=loan['data'],
                    milestone_cost=0.0,  # Initial milestone accrued can be set to 0.00
                )
            print('loan milestone created')

            #====================================== approved amount transfer to loanaccount from centralfunding account ===============
            get_loan = Loan.objects.get(id = loan_id)
            get_centralaccount = CentralFundingAccount.objects.get(company_id = company_id)
            get_centralaccount.account_balance -= get_loan.approved_amount    # the loan amount depit from centralfundingaccount
            get_loanaccount = LoanAccount.objects.get(loan_id = loan_id)
            get_loanaccount.principal_amount += get_loan.approved_amount      # the loan amount credit from centralfundingaccount
            get_centralaccount.save()
            get_loanaccount.save()

            # =============== calling repayment schedule  =====================
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
            print('loan repayment created')
            
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
    # For approval Loans
def account_list(loan_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')    
        
        record = LoanAccount.objects.get(loan_id=loan_id)
        LoanAccount_record = LoanAccountSerializer(record).data
        print('LoanAccount_record',LoanAccount_record)

        record = LoanDisbursementAccount.objects.get(loan_id=loan_id)
        loandisbursement_record = LoanDisbursementAccountSerializer(record).data
        
        record = LoanRepaymentAccount.objects.get(loan_id=loan_id)
        loanrepaymentaccount_record = LoanRepaymentAccountSerializer(record).data

        record = PenaltyAccount.objects.get(loan_id=loan_id)
        penaltyaccount_record = PenaltyAccountSerializer(record).data

        record = InterestAccount.objects.get(loan_id=loan_id)
        interestaccount_record = InterestAccountSerializer(record).data

        records = {
            "LoanAccount_record":LoanAccount_record,
            "loandisbursement_record":loandisbursement_record,
            "loanrepaymentaccount_record":loanrepaymentaccount_record,
            "penaltyaccount_record":penaltyaccount_record,
            "interestaccount_record":interestaccount_record,

        }
        return success(records)

    except LoanAccount.DoesNotExist:
        return error('Invalid LoanAccount: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
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
            loan_calculation_method = records.loan_calculation_method,

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
            print("==================",record.id)
            serializer = LoanSerializer(record)
        elif loanapp_id is not None:
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

def getting_loan_tranches(company_id):
    try:
        records = Loan.objects.filter(company_id = company_id,loanapp_id__disbursement_type = 'trenches')
        serializer = LoanSerializer(records, many=True)
        return success(serializer.data)
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


def create_loanagreement(company_id,loan_id, loanapp_id, customer_id, agreement_template,agreement_template_value=None):
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
            agreement_template_id=agreement_template,
            agreement_template_value=agreement_template_value,
            agreement_status = 'Active',
            is_active = True,
        )

        # update the workflow status in loan application and loan table
        # loanapp = LoanApplication.objects.get(pk=loanapp_id)
        # loan = Loan.objects.get(pk = loan_id)
        # if attachment1 and attachment:
        #     loanapp.workflow_stats = "Borrower_and_Lender_Approved"
        #     loan.workflow_stats = "Borrower_and_Lender_Approved"
        # elif attachment:
        #     loanapp.workflow_stats = "Borrower_Approved"
        #     loan.workflow_stats = "Borrower_Approved"
        # elif attachment1:
        #     loanapp.workflow_stats = "Lender_Approved"
        #     loan.workflow_stats = "Lender_Approved"
        # else:
        #     loanapp.workflow_stats = "Borrower_and_Lender_Approved" # Approved
        #     loan.workflow_stats = "Borrower_and_Lender_Approved"
        # loanapp.save()
        # loan.save()

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

            #====== getting 

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
        records = Loan.objects.filter(company_id = company_id,is_active=True,status__iexact = 'approved',disbursement_status__in = ["Pending","Partially Paid"]).order_by("-id")
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

def create_disbursement(company_id, customer_id,loan_id, loan_application_id, amount, disbursement_type, disbursement_status,disbursement_method=None,currency_id=None,bank=None,notes=None):
    try:
        print("===================")
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        # Validate foreign keys
        Company.objects.get(pk=company_id)
        Customer.objects.get(pk=customer_id)
        LoanApplication.objects.get(pk=loan_application_id)
    

        # Generate unique disbursement ID
        generate_id = Disbursement.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.disbursement_id[10:]
        disbursement_id = unique_id('DISB', last_id)

        loanapp = LoanApplication.objects.get(pk=loan_application_id)
        loan = Loan.objects.get(pk = loan_id)

        #=== customer account ======
        customeraccount = CustomerAccount.objects.get(id = bank)

        # 1 st scenario disbursement type one-off and Disbursement Beneficiary Pay Self
        if loanapp.disbursement_type == 'one_off':
            if loanapp.loantype.disbursement_beneficiary == 'pay_self':
                #============= transfer amount loanamount from loan account to disbursement account ======
                loanact = LoanAccount.objects.get(loan_id = loan.id)
                loanact.principal_amount -= loan.approved_amount   # amount depit from loanaccount
                disbursementact = LoanDisbursementAccount.objects.get(loan_id = loan.id)
                disbursementact.amount += loan.approved_amount # amount credit to disbursement account
                loanact.save()
                disbursementact.save()

                # ========= amount transfer to customer account =============
                customeraccount.account_balance = loan.approved_amount # amount credit to borrower account
                customeraccount.save()
                disbursementact.amount -= loan.approved_amount # amount debit to disbursement account
                disbursementact.save()


                print("One-off disbursement to loan account completed.")
            elif loanapp.loantype.disbursement_beneficiary == 'pay_milestone':  
                # Prevent customer from withdrawing the loan amount for controlled purposes
                return error("Disbursement cannot proceed as the amount is designated for a milestone.")

        elif loanapp.disbursement_type == 'trenches': 
            if loanapp.loantype.disbursement_beneficiary == 'pay_self':
                #============= transfer amount loanamount from loan account to disbursement account ======
                loanact = LoanAccount.objects.get(loan_id = loan.id)
                loanact.principal_amount -= loan.approved_amount   # amount depit from loanaccount
                disbursementact = LoanDisbursementAccount.objects.get(loan_id = loan.id)
                disbursementact.amount += loan.approved_amount # amount credit to disbursement account
                loanact.save()
                disbursementact.save()

                # ========= amount transfer to customer account =============
                customeraccount.account_balance = loan.approved_amount # amount credit to borrower account
                customeraccount.save()
                disbursementact.amount -= loan.approved_amount # amount debit to disbursement account
                disbursementact.save()
                print("One-off disbursement to loan account completed.")

            elif loanapp.loantype.disbursement_beneficiary == 'pay_milestone':
                #============= transfer amount loanamount from loan account to disbursement account ======
                loanact = LoanAccount.objects.get(loan_id = loan.id)
                loanact.principal_amount -= amount   # amount depit from loanaccount
                disbursementact = LoanDisbursementAccount.objects.get(loan_id = loan.id)
                disbursementact.amount += amount # amount credit to disbursement account
                loanact.save()
                disbursementact.save() 
                milestone_obj = MilestoneAccount.objects.filter(loan_id = loan.id)
                if not milestone_obj.exists():
                    milestone_account = MilestoneAccount.objects.create(
                        # account_no = f'IA00{loan_id}',
                        company_id=company_id,
                        loan_id=loan.id,
                        milestone_cost=0.0,  # Initial milestone accrued can be set to 0.00
                    )
                else:
                    milestone_account =milestone_obj.last()
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
       
            bank_id = bank,
            notes=notes,
        )
        # update the workflow status in loan application and loan table
        loan.disbursement_amount = float(loan.disbursement_amount) + float(amount)
        loanapp.workflow_stats = 'Disbursment'
        loan.workflow_stats = 'Disbursment'
        loan.disbursement_amount += float(amount)
        loan.save()
        loanapp.save()
    
        if loan.disbursement_amount >= loan.approved_amount :
            
            loan.disbursement_status = "Paid"
        elif loan.disbursement_amount < loan.approved_amount and loan.paid_amount != 0.0:
            loan.disbursement_status = "Partially_Paid"
        else:
            loan.disbursement_status = "Pending"

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


def getting_repayment_schedules(company_id,loanapp_id=None,loanapplication_id=None):
    try:
        if loanapp_id:
            instance = RepaymentSchedule.objects.filter(company_id=company_id,loan_id_id = loanapp_id)
            serializer = RepaymentscheduleSerializer(instance,many=True)
        else:
            instance = RepaymentSchedule.objects.filter(company_id=company_id,loan_application_id = loanapplication_id)
            serializer = RepaymentscheduleSerializer(instance,many=True)

        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_next_schedules(company_id, loanapp_id=None,loanapplication_id=None):
    try:
        print(company_id, loanapp_id,loanapplication_id)
        if loanapp_id:
        # Filter repayment schedules based on company and loan application
            instance = RepaymentSchedule.objects.filter(company_id=company_id, loan_id_id=loanapp_id, repayment_status='Pending')
            total=len(instance)
            # Order by repayment date to find the earliest pending repayment
            next_due_schedule = instance.order_by('repayment_date').first()

            if next_due_schedule:
                # Fetch next due date and instalment amount
                next_due_date = next_due_schedule.repayment_date
                amount_due = next_due_schedule.instalment_amount
                return success({
                    "next_due_date": next_due_date,
                    "amount_due": amount_due,
                    "total":total
                })
        elif loanapplication_id:
            # Filter repayment schedules based on company and loan application
# Filter repayment schedules based on company and loan application
            instance = RepaymentSchedule.objects.filter(company_id=company_id, loan_application_id=loanapplication_id)
            total = 0

            # Filter further based on 'Pending' repayment status if needed
            pending_instance = instance.filter(repayment_status='Pending')
            if pending_instance.exists():  # Check if there are any "Pending" repayments
                # Order by repayment date to find the earliest pending repayment
                next_due_schedule = pending_instance.order_by('repayment_date').first()
                total=len(pending_instance)
                if next_due_schedule is not None:
                    # Fetch next due date and instalment amount
                    next_due_date = next_due_schedule.repayment_date
                    amount_due = next_due_schedule.instalment_amount
                    return success({
                        "next_due_date": next_due_date,
                        "amount_due": amount_due,
                        "total": total
                    })
            else:
                # If no "Pending" repayments, still return the earliest repayment from all available ones
                next_due_schedule = instance.order_by('repayment_date').first()

                if next_due_schedule is not None:
                    # Fetch next due date and instalment amount
                    next_due_date = next_due_schedule.repayment_date
                    amount_due = next_due_schedule.instalment_amount
                    return success({
                        "next_due_date": next_due_date,
                        "amount_due": amount_due,
                        "total": total
                    })

            # If no repayments were found at all
            return error("No repayments found.")
            
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


def getting_schedule(schedule_id = None,uniques_id = None):
    try:
        if uniques_id is not None:
            instance=RepaymentSchedule.objects.get(id= uniques_id)
            serializer=RepaymentscheduleSerializer(instance)
        else:
            instance=RepaymentSchedule.objects.get(schedule_id= schedule_id)
            serializer=RepaymentscheduleSerializer(instance)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")



def paid_schedule(schedule_id):
    try:
        schedule=RepaymentSchedule.objects.get(id = schedule_id)
        if schedule:
            schedule.repayment_status = 'Paid'
            schedule.paid_amount=schedule.instalment_amount

            schedule.save()
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

def upload_collateraldocument(company_id,collateral_id,loanapplication_id,document_name,attachment=None,desctioption=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')

        Company.objects.get(pk=company_id)
        LoanApplication.objects.get(pk=loanapplication_id)
        Collaterals.objects.get(pk=collateral_id)

        instance = CollateralDocuments.objects.create(
            company_id = company_id,
            collateral_id = collateral_id,
            application_id_id = loanapplication_id,
            document_name = document_name,
            additional_documents = attachment,
            description = desctioption,
        )

        print("instance34567890",instance)
        try:
            log_audit_trail(request.user.id,'Collaterals Document Upload', instance, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        folder_instance = FolderMaster.objects.filter(company_id=company_id,folder_name='Collateral Folder List').last()
        print("folder_instance34567890-54675678", folder_instance)
        start_date=None
        end_date=None
        document_type_id=None
        record = DocumentUpload.objects.create(
            document_id = unique_id_generate_doc('DID'),
            company_id=company_id,
            document_title=document_name,
            document_type_id=document_type_id,
            description=desctioption,
            document_upload=attachment,
            folder=folder_instance,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user,
            update_by=request.user,
            document_size=attachment.size,
        )  
        print("collateralrecord34567890p",record)      
        document_upload_history(record.document_id)


        return success(f'Successfully created {instance}')
    except Company.DoesNotExist:
        return error('Invalid Company ID: Company not found.')
    except LoanApplication.DoesNotExist:
        return error('Invalid LoanApplication ID: LoanApplication not found.') 
    except Collaterals.DoesNotExist:
        return error('Invalid Collaterals ID: Collaterals not found.')   
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_collateraldocument(company_id,collateral_id):
    try:
       
        records = CollateralDocuments.objects.filter(company_id = company_id,collateral_id = collateral_id)
        serializer = CollateralDocumentsSerializer(records, many=True).data
        return success(serializer)
    except LoanApplication.DoesNotExist:
        return error('Invalid LoanApplication ID: LoanApplication not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")

def get_collateraldocument_withloanapp(company_id,loan_application_id):
    try:
       
        records = CollateralDocuments.objects.filter(company_id = company_id,application_id_id = loan_application_id)
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

def view_collaterals_withdocuments(company_id,loan_appliaction_id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        records = Collaterals.objects.filter(company_id =company_id, loanapp_id = loan_appliaction_id)
        serializer = CollateralsSerializer(records, many=True).data
        for data in serializer:
            documents=CollateralDocuments.objects.filter(collateral_id=data.get('id'))
            data['documents']=CollateralDocumentsSerializer(documents,many=True).data
        return success(serializer)
    except ValidationError as e:
        return error(f"Validation Error: {e}")

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



def calculate_repayment_schedule(loan_amount, interest_rate, tenure, tenure_type, repayment_schedule, loan_calculation_method, repayment_start_date, repayment_mode,loantype_id=None):
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
    print(loan_calculation_method)
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


def create_loantype(company_id,loantype,disbursement_beneficiary=None,interest_rate=None,loan_calculation_method=None,loan_teams=None,min_loan_amt=None,max_loan_amt=None,eligibility=None,collateral_required=False,charges=None,is_active=False,description = None ):
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
            loan_calculation_method=loan_calculation_method,
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

def update_loantype(company_id,loantype_id,loantype,disbursement_beneficiary=None,interest_rate=None,loan_calculation_method=None,loan_teams=None,min_loan_amt=None,max_loan_amt=None,eligibility=None,collateral_required=False,charges=None,is_active=False,is_refinance=False,description = None ):
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
        instance.loan_calculation_method = loan_calculation_method if loan_calculation_method is not None else instance.loan_calculation_method
        instance.loan_teams = loan_teams if loan_teams is not None else instance.loan_teams
        instance.min_loan_amt = min_loan_amt if min_loan_amt is not None else instance.min_loan_amt
        instance.max_loan_amt = max_loan_amt if max_loan_amt is not None else instance.max_loan_amt
        instance.eligibility = eligibility if eligibility is not None else instance.eligibility
        instance.collateral_required = collateral_required if collateral_required is not None else instance.collateral_required
        instance.charges = charges if charges is not None else instance.charges
        instance.is_active = is_active if is_active is not None else instance.is_active
        instance.is_refinance = is_refinance if is_refinance is not None else instance.is_refinance
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
    

from django.http import JsonResponse

def get_loan_type_details(id=None,loantype_id=None): 
    try:
        if id:
            instance = LoanType.objects.get(id = id)
            serializer = LoanTypeSerializer(instance)
        elif loantype_id:
            instance = LoanType.objects.get(loantype_id = loantype_id)
            serializer = LoanTypeSerializer(instance)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def get_tenure_details(loantype): 
    try:
        instance = LoanType.objects.get(loantype = loantype)
        serializer = LoanTypeSerializer(instance)
        return success(serializer.data) 
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


# ============= Value Chain==================================

def create_valuechainsetup(company_id,loan_type_id,valuechain_name,max_amount,min_amount,status=True,description = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')  
        
        # Generate a unique offer ID
        chainid = ValueChainSetUps.objects.last()
        last_id = '000'
        if chainid:
            last_id = chainid.unique_id[6:]
        uniqueid = unique_id('VC', last_id)
        print("63e753")
        ValueChainSetUps.objects.create(
            company_id = company_id,
            unique_id = uniqueid,
            loan_type_id = loan_type_id,
            valuechain_name = valuechain_name,
            max_amount  = max_amount,
            min_amount = min_amount,
            description = description,
            status = status,
        )
        return success('success')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_valuechainsetups(company_id = None, loantype_id = None,valuechain_id = None):
    try:
        if valuechain_id is not None:
            value_chains = ValueChainSetUps.objects.get(id = valuechain_id)
            serializers = ValueChainSetUpsSerializer(value_chains).data
        else:
            value_chains = ValueChainSetUps.objects.filter(company_id =company_id, loan_type_id=loantype_id)
            serializers = ValueChainSetUpsSerializer(value_chains,many = True).data

        return success(serializers)
    except Exception as e:
        return error(f"An error occurred: {e}")

def valuechain_setup_edit(valuechain_id,valuechain_name,max_amount,min_amount,description,status):
    try:
        value_chains = ValueChainSetUps.objects.get(id = valuechain_id)
        value_chains.valuechain_name = valuechain_name
        value_chains.max_amount = float(max_amount)
        value_chains.min_amount = float(min_amount)
        value_chains.description = description
        value_chains.status = status
        value_chains.save()
        return success('Sucessfully updated')
    except ValueChainSetUps.DoesNotExist:
        return error('Invalid ValueChainSetUps ID: ValueChainSetUps not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def valuechain_setup_delete(valuechain_id):
    try:
        value_chains = ValueChainSetUps.objects.get(id = valuechain_id)
        value_chains.delete()
        return success('Sucessfully Deleted')
    except Exception as e:
        return error(f"An error occurred: {e}")


def create_milestonesetup(company_id,loan_type,valuechain_id,milestone_name,max_amount,min_amount,description = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        # Generate a unique offer ID
        chainid = MilestoneSetUp.objects.last()
        
        last_id = '000'
        if chainid:
            last_id = chainid.unique_id[9:]
        
        uniqueid = unique_id('MS', last_id)
        MilestoneSetUp.objects.create(
            company_id = company_id,
            unique_id = uniqueid,
            loan_type_id = loan_type,
            valuechain_id_id = valuechain_id,
            milestone_name = milestone_name,
            max_amount = max_amount,
            min_amount = min_amount,
            description = description,
        )

        return success('success')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_milestonesetup(company_id,valuechain_id = None,miletone_id = None):
    try:
        if miletone_id is not None:
            records = MilestoneSetUp.objects.get(id = miletone_id)
            serializers = MilestoneSetUpSerializer(records).data
        else:
            records = MilestoneSetUp.objects.filter(company_id = company_id,valuechain_id_id = valuechain_id)
            serializers = MilestoneSetUpSerializer(records,many=True).data
        return success(serializers)
    except Exception as e:
        return error(f"An error occurred: {e}")

def milestone_setup_edit(milestone_id,milestone_name,max_amount,min_amount,description,status):
    try:
        milestones = MilestoneSetUp.objects.get(id = milestone_id)
        milestones.milestone_name = milestone_name
        milestones.max_amount = float(max_amount)
        milestones.min_amount = float(min_amount)
        milestones.description = description
        milestones.status = status
        milestones.save()
        return success('Sucessfully updated')
    except ValueChainSetUps.DoesNotExist:
        return error('Invalid ValueChainSetUps ID: ValueChainSetUps not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def milestone_setup_delete(milestone_id):
    try:
        milestones = MilestoneSetUp.objects.get(id = milestone_id)
        milestones.delete()
        return success('Sucessfully Deleted')
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_stagesetup(company_id,milestone_id,stage_name,min_amount,max_amount,sequence,description = None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        MilestoneStagesSetup.objects.create(
            company_id = company_id,
            milestone_id_id = milestone_id,
            stage_name = stage_name,
            sequence = sequence,
            max_amount = max_amount,
            min_amount = min_amount,
            description = description,
        )
        return success('success')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_milestonestagessetup(company_id,miletone_id = None,stages_id = None):
    try:
        if stages_id is not None:
            records = MilestoneStagesSetup.objects.get(id = stages_id)
            serializers = MilestoneStagesSetupSerializer(records).data
        else:
            records = MilestoneStagesSetup.objects.filter(company_id = company_id,milestone_id_id = miletone_id)
            serializers = MilestoneStagesSetupSerializer(records,many=True).data
        return success(serializers)
    except Exception as e:
        return error(f"An error occurred: {e}")

def stages_setup_edit(stages_id,stage_name,max_amount,min_amount,description,sequence):
    try:
        stages = MilestoneStagesSetup.objects.get(id = stages_id)
        stages.stage_name = stage_name
        stages.max_amount = float(max_amount)
        stages.min_amount = float(min_amount)
        stages.description = description
        stages.sequence = sequence
        stages.save()
        return success('Sucessfully updated')
    except ValueChainSetUps.DoesNotExist:
        return error('Invalid ValueChainSetUps ID: ValueChainSetUps not found.')
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def stages_setup_delete(stages_id):
    try:
        milestones = MilestoneStagesSetup.objects.get(id = stages_id)
        milestones.delete()
        return success('Sucessfully Deleted')
    except Exception as e:
        return error(f"An error occurred: {e}") 

def create_loanvaluechain(company_id,loanapp_id):
    try:
        records = Loan.objects.filter(company_id = company_id,loanapp_id__disbursement_type = 'trenches',id=loanapp_id)

        for data in records:
            valuechain = ValueChainSetUps.objects.filter(loan_type_id = data.loanapp_id.loantype.id)
        
            for data1 in valuechain: # looping valuechain
                # Generate a unique offer ID
                chainid = LoanValuechain.objects.last()
                last_id = '000'
                if chainid:
                    last_id = chainid.unique_id[10:]
                uniqueid = unique_id('LVC', last_id)

                loanchain = LoanValuechain.objects.create(
                    company_id = company_id,
                    loan_id = data.id,
                    unique_id = uniqueid,
                    loan_type_id = data1.loan_type.id,
                    valuechain_name = data1.valuechain_name,
                    amount  = 0.0,
                    description = data1.description,
                    active = True,
                    sequence = 1,  # Order of milestones
                )

                milestone = MilestoneSetUp.objects.filter(valuechain_id_id = data1.id) # milestone 
                for data2 in milestone: # looping milestone
                    # Generate a unique offer ID
                    milestoneid = LoanMilestone.objects.last()
                    last_id = '000'
                    if milestoneid:
                        last_id = milestoneid.unique_id[10:]
                    uniqueid = unique_id('LMS', last_id)

                    milestone = LoanMilestone.objects.create(
                        company_id = company_id,
                        loan_id = data.id,
                        unique_id = uniqueid,
                        loan_type_id = data1.loan_type.id,
                        valuechain_id_id = loanchain.id,
                        milestone_name = data2.milestone_name,
                        amount  = 0.0,
                        description = data2.description,
                        active = True,
                        sequence = 1,
                    )

                    milestonestages = MilestoneStagesSetup.objects.filter(milestone_id_id = data2.id) # milestone
                    for data3 in milestonestages:
                        LoanMilestoneStages.objects.create(
                            company_id = company_id,
                            loan_id = data.id,
                            milestone_id_id = milestone.id,
                            stage_name = data3.stage_name,
                            description = data3.description,  # Optional description of the stage
                            sequence = 1,
                        )
            data.disbursement_trenches = True
            data.save()

        return success("success")
    except Exception as e:
        return error(f"An error occurred: {e}") 


def loan_detail_value_chain_get(loanapp_id):
    try:
        loanchain_records = LoanValuechain.objects.filter(loan_id=loanapp_id)
        print('loanchain_records',loanchain_records)
        loan_valuechain_data = LoanValuechainSerializer(loanchain_records,many=True)
        for data in loan_valuechain_data.data:
            milestone_records = LoanMilestone.objects.filter(valuechain_id=data.get('id'))
            data['milestone'] = LoanMilestoneSerializer(milestone_records,many=True).data
            for milestone in data['milestone']:
                milestone_records = LoanMilestoneStages.objects.filter(milestone_id=milestone.get('id'))
                milestone['activity'] = LoanMilestoneStagesSerializer(milestone_records,many=True).data
        print('loan_valuechain_data.data',loan_valuechain_data.data,'\n\n\n\n')
        return success(loan_valuechain_data.data)
    except Exception as e:
        return error(f"An error occurred: {e}") 


def value_chain_edit_v1(value_chain_id,amount):
    try:
        records = LoanMilestone.objects.filter(id=value_chain_id)
        if records.exists():
            record = records.last()
            record.amount = amount
            record.save()
        return success('Updated successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")

def value_chain_delete_v1(value_chain_id):
    try:
        records = LoanMilestone.objects.filter(id=value_chain_id)
        if records.exists():
            records.last().delete()
        return success('deleted successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")

def milestone_edit_v1(milestone_id,amount):
    try:
        records = LoanMilestone.objects.filter(id=milestone_id)
        if records.exists():
            record = records.last()
            record.amount = amount
            record.save()
        return success('Updated successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")

def milestone_compelete(milestone_id):
    try:
        records = LoanMilestone.objects.filter(id=milestone_id)
        if records.exists():
            record = records.last()
            record.actual_completion_date = datetime.now()
            record.save()
        return success('Updated successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")

def milestone_activity_delete_v1(activity_id):
    try:
        records = LoanMilestoneStages.objects.filter(id=activity_id)
        if records.exists():
            records.last().delete()
        return success('deleted successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")


def milestone_activity_edit_v1(activity_id,amount):
    try:
        records = LoanMilestoneStages.objects.filter(id=activity_id)
        if records.exists():
            record = records.last()
            record.amount = amount
            record.save()
        return success('Updated successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")

def milestone_delete_v1(milestone_id):
    try:
        records = LoanMilestone.objects.filter(id=milestone_id)
        if records.exists():
            records.last().delete()
        return success('deleted successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")


def milestone_activity_create_v1(milestone_id,activity_name,amount,description=None,start_date=None,end_date=None):
    try:
        milestone = LoanMilestone.objects.get(id=milestone_id)
        records = LoanMilestoneStages.objects.create(
            company=milestone.company,
            loan=milestone.loan,
            milestone_id=milestone,
            stage_name=activity_name,
            amount=amount,
            description=description,
            start_date=start_date,
            end_date=end_date,
            )
        return success('Created successfully')
    except Exception as e:
        return error(f"An error occurred: {e}")


def milestone_create_v1(valuechain_id,milestone_name,amount,description=None,due_date=None):
    try:
        valuechain_record = LoanValuechain.objects.get(id=valuechain_id)
        milestoneid = LoanMilestone.objects.last()
        last_id = '000'
        if milestoneid:
            last_id = milestoneid.unique_id[10:]
        uniqueid = unique_id('LMS', last_id)

        records = LoanMilestone.objects.create(
            company=valuechain_record.company,
            unique_id=uniqueid,
            loan=valuechain_record.loan,
            loan_type=valuechain_record.loan_type,
            valuechain_id=valuechain_record,
            milestone_name=milestone_name,
            amount=amount,
            description=description,
            due_date=due_date,
            sequence=0,
            active=True,
            )
        return success('Created successfully')
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



# def department_view(department_id=None):
#     try:
#         if department_id:
#             records = Department.objects.filter(id=department_id)
#             if records.exists():
#                 record=records.last()
#                 serializer = DepartmentSerializer(record)
#                 return success(serializer.data)
#             else:
#                 return error('department_id is invalid')
#         else:
#             records = Department.objects.all()
#             serializer = DepartmentSerializer(records,many=True)
#             return success(serializer.data)
#     except Exception as e:
#         return error(e)


def document_category_create(category_name,description=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        
        record = DocumentCategory.objects.create(
                category_name=category_name,
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
    

def document_upload(document_title,document_type,entity_type,description,document_upload,folder_id,start_date=None,end_date=None,company_id=None):
    try:
        print('entity_type==+++',entity_type,folder_id)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')

        # obj_count=DocumentUpload.objects.all().last()

        # print("folder_instance---+++",folder_instance)
    
        folder_instance = FolderMaster.objects.get(folder_id=folder_id)
        document_type= IdentificationType.objects.get(id=document_type)
        print("document_type345678o",document_type)
        print("folder_instance---+++",folder_instance)
        print("document_upload56789",document_upload)
        record = DocumentUpload.objects.create(
                document_id = unique_id_generate_doc('DID'),
                company_id=company_id,
                document_title=document_title,
                document_type=document_type,
                description=description,
                document_upload=document_upload,
                folder=folder_instance,
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



def template_create(template_name,content):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')

        record = Template.objects.create(
                template_name=template_name,
                content=content,
                created_by=request.user,
                updated_by=request.user,
            )
        try:
            log_audit_trail(request.user.id,'Template Registration', record, 'Create', 'Object Created.')
        except Exception as e:
            return error(f"An error occurred: {e}")

        return success('Template create successfully')
    except Exception as e:
        return error(e)
    

def view_template(template_id=None):
    try:
        if template_id:
            template = Template.objects.get(pk=template_id)
            serializer = TemplateSerializer(template)
        else:
            template = Template.objects.all()
            serializer = TemplateSerializer(template,many=True)
        return success(serializer.data)

    except Template.DoesNotExist:
        return error(f"Template with ID {template_id} not found")
    except Exception as e:
        return error(e)
      
def folder_delete(entity_id=None,folder_id=None):
    print("entity_id45678o",entity_id,folder_id)
    try:
        if entity_id:
            entity_instance = CustomDocumentEntity.objects.get(entity_id=entity_id)
            #records = FolderMaster.objects.filter(entity=entity_instance,default_folder=True,matter__isnull=True)
            print('recordsdelete=====',entity_instance)
            entity_instance.delete()
            return success('Entity Deleted Sucessfully')
        if folder_id:
            folder_instance=FolderMaster.objects.get(folder_id=folder_id)
            folder_instance.delete()
            return success('Folder Deleted Sucessfully')
        
    except CustomDocumentEntity.DoesNotExist:
        return error('Entity_id is invalid')
    except Exception as e:
        return error(e)  

def document_edit(document_id,document_name,document_upload):
    try:
        print("document_upload---",document_upload,document_id,document_name)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')        
        
        obj = DocumentUpload.objects.get(document_id=document_id)
        obj.document_title = document_name
        obj.document_upload = document_upload
        obj.save()
        print("document_upload_history+++",obj.document_id) 
        document = document_upload_history(obj.document_id)
        document_audit = document_upload_audit('updated',obj.document_id)
        print("document_upload_history///",document) 
        print("document_audit/",document_audit) 
        return success("Updated successfully")
    except DocumentUpload.DoesNotExist:
        return error('document_id is invalid')
    except Exception as e:
        return error(str(e))





def user_check():
    try:
        request = get_current_request()
        user_check=request.user.is_superuser
        print("user_check",user_check)
        return success(user_check)
    except Exception as e:
        return error(f"An error occurred: {e}")
    
# def view_audit():
#     try:
#         audit_trail = AuditTrail.objects.all().order_by('-datetime')
#         serializer = AuditTrailSerializer(audit_trail, many=True)

#         return success(serializer.data)

#     except AuditTrail.DoesNotExist:
#         return error(f"Audit with ID {AuditTrail} not found")
#     except Exception as e:
#         return error(f"An error occurred: {e}")



def view_audit():
    try:
        audit_trail = AuditTrail.objects.all().order_by('-datetime')
        serializer = AuditTrailSerializer(audit_trail, many=True)
        serialized_data = serializer.data

        # Format the datetime field for each record
        for record in serialized_data:
            if 'datetime' in record:
                original_datetime_str = record['datetime']
                parsed_datetime = datetime.strptime(original_datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                record['datetime'] = parsed_datetime.strftime('%Y-%m-%d / %H:%M:%S')

        return success(serialized_data)

    except AuditTrail.DoesNotExist:
        return error(f"Audit with ID {AuditTrail} not found")
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_penalty_loans(company_id):
    try:
        overdue_schedules = RepaymentSchedule.objects.filter(company_id = company_id,
            repayment_date__lt=now().date(),  # Repayment date is in the past
            repayment_status="Pending"        # Status is still pending
        )
        print("===============",overdue_schedules)
        loans = [data.loan_id.id for data in overdue_schedules]

        records = Loan.objects.filter(id__in = loans)
        serializer = LoanSerializer(records,many = True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_overdue(company_id,loan_ID):
    try:
        overdue_schedules = RepaymentSchedule.objects.filter(company_id = company_id,
            repayment_date__lt=now().date(),  # Repayment date is in the past
            repayment_status="Pending",loan_id_id = loan_ID        # Status is still pending
        )
        serializer = RepaymentscheduleSerializer(overdue_schedules,many = True)
        
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def create_penalty(company, loan, penalty_amount, penalty_reason, repayment_schedule):
    try:

        # Generate a unique offer ID
        chainid = Penalty.objects.last()
        last_id = '000'
        if chainid:
            last_id = chainid.penalty_id[6:]
        uniqueid = unique_id('SP', last_id)

        penalty = Penalty.objects.create(
            company_id=company,
            penalty_id=uniqueid,
            loan_id=loan,
            repayment_schedule_id=repayment_schedule,
            penalty_date=date.today(),
            penalty_amount=penalty_amount,
            penalty_reason=penalty_reason,
            status="unpaid",
        )
        schedule = RepaymentSchedule.objects.get(id = repayment_schedule)
        schedule.total_penalty_amt += penalty_amount
        schedule.payable_penalty_amt += penalty_amount
        schedule.penalty_reason = penalty_reason
        schedule.save()

        return success('Successfully saved')
    except Exception as e:
        return error(f"An error occurred: {e}")

def get_penalties_for_loan(company_id):
    try:
        records = Penalty.objects.filter(company_id=company_id)
        loan_id = [data.loan.id for data in records]
        loan_data = Loan.objects.filter(id__in = loan_id)
        serializer = LoanSerializer(loan_data,many = True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_penalities_withloan(company_id,loan_id):
    try:
        records = Penalty.objects.filter(company_id=company_id,loan_id = loan_id )
        serializer = PenaltySerializer(records,many = True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")


def get_unpaid_penalties(loan):
    """
    Retrieve all unpaid penalties for a given loan.

    Args:
        loan (Loan): The loan instance.
    
    Returns:
        QuerySet: A queryset of unpaid penalty instances.
    """


    return Penalty.objects.filter(loan=loan, status="unpaid")


def calculate_late_penalty(loan, repayment_schedule, penalty_rate):
    """
    Calculate the penalty for a late repayment.

    Args:
        loan (Loan): The loan instance.
        repayment_schedule (RepaymentSchedule): The specific repayment schedule.
        penalty_rate (float): Penalty rate (e.g., 0.05 for 5% of the installment amount).
    
    Returns:
        float: The calculated penalty amount.
    """
    if repayment_schedule.repayment_status == "Pending" and repayment_schedule.repayment_date < date.today():
        overdue_days = (date.today() - repayment_schedule.repayment_date).days
        penalty_amount = repayment_schedule.instalment_amount * penalty_rate * overdue_days
        return round(penalty_amount, 2)
    return 0.0


import re
from django.utils.html import escape

def template_fields(loan_id,template_id):
    try:
        template = Template.objects.get(pk=template_id)
        # loan = Loan.objects.get(loanapp_id_id=loan_id)

        # Find all placeholders in the template content for initial form rendering
        placeholders = [placeholder.strip() for placeholder in re.findall(r'\{\{(\s*\w+\s*)\}\}', template.content)]
        placeholders_with_value = tag_replacement(placeholders, loan_id)
        return success(placeholders_with_value)

    except Template.DoesNotExist:
        return error(f"Template with ID {template_id} not found")
    except Exception as e:
        return error(e)
    

def tag_replacement(tag_list, loan_id):
    loan = Loan.objects.filter(loanapp_id_id=loan_id)
    print('loan',loan)
    print('loan',loan)
    loan=loan.last()
    result = []
    
    for data in tag_list:
        dic = {'name': data, 'value': None}  # Initialize the dictionary
        print('loan.customer',loan.customer)
        if data == 'customer_first_name' or data == 'cutomer_first_name':
            dic['value'] = loan.customer.firstname
        elif data == 'customer_lastname' or data == 'cutomer_lastname':
            dic['value'] = loan.customer.lastname
        elif data == 'customer_email' or data == 'cutomer_email':
            dic['value'] = loan.customer.email
        elif data == 'customer_age' or data == 'cutomer_age':
            dic['value'] = loan.customer.age
        elif data == 'customer_phone_number' or data == 'cutomer_phone_number':
            dic['value'] = loan.customer.phone_number
        elif data == 'customer_address' or data == 'cutomer_address':
            dic['value'] = loan.customer.address
        elif data == 'dateofbirth':
            dic['value'] = loan.customer.dateofbirth
        elif data == 'application_id':
            dic['value'] = loan.loanapp_id.application_id
        elif data == 'loan_type':
            dic['value'] = loan.loanapp_id.loantype.loantype
        elif data == 'loan_amount':
            dic['value'] = loan.loan_amount
        elif data == 'loan_purpose':
            dic['value'] = loan.loan_purpose
        elif data == 'approved_amount':
            dic['value'] = loan.approved_amount
        elif data == 'interest_rate':
            dic['value'] = loan.interest_rate
        elif data == 'tenure':
            dic['value'] = loan.tenure
        elif data == 'tenure_type':
            dic['value'] = loan.tenure_type
        elif data == 'repayment_schedule':
            dic['value'] = loan.repayment_schedule
        elif data == 'repayment_mode':
            dic['value'] = loan.repayment_mode
        elif data == 'interest_basics':
            dic['value'] = loan.interest_basics
        elif data == 'loan_calculation_method':
            dic['value'] = loan.loan_calculation_method
        
        result.append(dic)
    
    return result

def agreement_draft(loan_id,agreement_template,agreement_template_value):
    try:
        loan_objs = Loan.objects.filter(loanapp_id_id=loan_id)
        loan_obj=loan_objs.last()
        generate_id = LoanAgreement.objects.last()
        last_id = '00'
        if generate_id:
            last_id = generate_id.agreement_id[9:]
        agreement_id = unique_id('LG',last_id)

        LoanAgreement.objects.create(
            loan_id=loan_obj,
            company=loan_obj.company,
            agreement_id=agreement_id,
            loanapp_id=loan_obj.loanapp_id,
            customer_id=loan_obj.customer,
            agreement_template_id=agreement_template,
            agreement_template_value=agreement_template_value,
            agreement_status='Active',
            disbursement_approval='Active'
        )
        return success('Record created successfully')
    except Exception as e:
        return error(e)


def agreement_signature_update(agreement_id,borrower_signature=None,lender_signature=None):
    try:
        obj = LoanAgreement.objects.get(id=agreement_id)
        if borrower_signature:
            obj.borrower_signature=borrower_signature
        if lender_signature:
            obj.lender_signature=lender_signature
        obj.save()
        return success('Record created successfully')
    except Exception as e:
        return error(e)


import calendar
from django.db.models import Q
from datetime import datetime

def dashboard_records(company_id):
    print('enter dashboard')
    print('company_id',company_id)
    today = datetime.now().date()
    year = today.year
    month = today.month

    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day).date()

    # Get the count of overdue repayments for today
    report_today = RepaymentSchedule.objects.filter(repayment_date=today)
    count_today_overdue = report_today.filter(company_id=company_id).count()
    print('count_today_overdue:', count_today_overdue)

    # Get the count of overdue repayments for the current month
    start_date = today  
    end_date = last_date  
    report_month = RepaymentSchedule.objects.filter(repayment_date__range=(start_date, end_date))
    count_of_overdue_this_month = report_month.filter(company_id=company_id).count()
    print('count_of_overdue_this_month:', count_of_overdue_this_month)

    report_past = RepaymentSchedule.objects.filter(
            Q(repayment_date__lte=today) & Q(repayment_status="Pending")
        )
    count_past_overdue = report_past.filter(company_id=company_id).count()
    print('count_past_overdue:', count_past_overdue)

    #For get the data for Loan Application
    loans_data = LoanApplication.objects.all()
    loans = loans_data.filter(company_id=company_id)
    loans_records = LoanapplicationSerializer(loans,many = True)

    #For get the data for Loan Audit tracking
    audit = AuditTrail.objects.all()
    audit_data = audit.order_by('-datetime')[:10]
    for record in audit_data:
        if isinstance(record.datetime, str):
            try:
                record.datetime = datetime.strptime(record.datetime, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"Invalid datetime format for record: {record.id}")
        
        # Format datetime to desired format
        if isinstance(record.datetime, datetime):
            record.formatted_datetime = record.datetime.strftime('%d-%m-%Y: %H%M')

    audit_records = AuditTrailSerializer(audit_data,many = True)

    #For get Loan datas
    loans = view_loan_for_dashboard(company_id)
    loan_records = loans['data']
    
     

    records = {
        'count_today_overdue': count_today_overdue,
        'count_of_overdue_this_month': count_of_overdue_this_month,
        'count_past_overdue': count_past_overdue,
        'recent_application':loans_records.data,
        'audit_records':audit_records.data,
        'loan_records':loan_records
    }
    return success(records)

def view_loan_for_dashboard(company_id):
    try:
        
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if company_id is not None:
            records = Loan.objects.filter(company_id = company_id)
            serializer = LoanSerializer(records, many=True)
        else:
            print('company_with_mathan')
            records = Loan.objects.all().order_by('-id')
            serializer = LoanSerializer(records, many=True)
        return success(serializer.data)
    
    except Loan.DoesNotExist:
        # Return an error response if the {model_name} does not exist
        return error('Loan does not exist')
    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")

def loan_restructure(company_id,loanapp_id,loan_id,new_tenure,new_amount,repayment_start_date, approval_status = None,rejected_reason = None,loantype_id=None):
    BASE_URL = "https://bbaccountingtest.pythonanywhere.com/loan-setup/"
    
    try:
        print('loanapp_id',loanapp_id)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        instance1 = LoanApplication.objects.get(id=loanapp_id)

        instance = Loan.objects.get(loanapp_id_id=loanapp_id)
        if approval_status == "restructured":
            instance.tenure=new_tenure
            instance.loan_status='restructured'
            instance.loan_amount=new_amount
            # instance.workflow_stats = "restructured"
            instance.save()
            get_loan = Loan.objects.get(id = loan_id)
            get_centralaccount = CentralFundingAccount.objects.get(company_id = company_id)
            get_centralaccount.account_balance -= get_loan.approved_amount    # the loan amount depit from centralfundingaccount
            get_loanaccount = LoanAccount.objects.get(loan_id = loan_id)
            get_loanaccount.principal_amount += get_loan.approved_amount      # the loan amount credit from centralfundingaccount
            get_centralaccount.save()
            get_loanaccount.save()

            # =============== calling repayment schedule  =====================
            schedules = calculate_repayment_schedule(new_amount,instance.interest_rate, new_tenure, instance.tenure_type, instance.repayment_schedule, instance.loan_calculation_method,repayment_start_date, instance.repayment_mode)
            print('schedules created',schedules)
            if schedules['status_code'] == 1: 
                return error(f"An error occurred: {schedules['data']}")
            print('count',len(schedules))
            for data in schedules['data']:
                # generate Unique id 
                generate_id = RestructureSchedule.objects.last()
                last_id = '00'
                if generate_id:
                    last_id = generate_id.schedule_id[10:]
                schedule_id = unique_id('SID',last_id)
                print('schedule_id',schedule_id)
                aa = RestructureSchedule.objects.create(
                    company_id = instance.company.id,
                    schedule_id = schedule_id,
                    loan_application_id = instance1.id,
                    loan_id_id = loan_id,
                    period = float(data['Period']),
                    repayment_date = data['Due_Date'],
                    instalment_amount = float(data['Installment']),
                    principal_amount = float(data['Principal']),
                    interest_amount = float(data['Interest']),
                    remaining_balance = float(data['Closing_Balance']),
                )
 

        return success("Successfully Restructured Your Application")
    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def restructure_list(company_id):
    try:
        print('company_id',company_id)
        data=Loan.objects.filter(company_id=company_id,loan_status='restructured')
        # data1=Loan.objects.filter(company_id=company_id,loanapp_id_id=data.id)
        print('data',data)
        serializer = LoanSerializer(data,many=True)
        
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def create_loan_restructure(loanapp_id,new_tenure,new_amount):
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

        # create loan
    except Company.DoesNotExist:
        return error('Invalid Company ID: Destination not found.')
    except Customer.DoesNotExist:
        return error('Invalid Customer ID: Destination not found.')
    except ValidationError as e:
        return error(f"Validation Error: {e}")
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_repayment_restructure_schedules(company_id,loanapp_id):
    try:
        print(f"company_id: {company_id}, loanapp_id: {loanapp_id}")
        instance = RestructureSchedule.objects.filter(company_id=company_id,loan_id_id = loanapp_id)
        serializer = RestructurescheduleSerializer(instance,many=True)
        
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_next_restructure_schedules(company_id, loanapp_id):
    try:
        print(company_id,loanapp_id)
        print(f"company_id: {company_id}, loanapp_id: {loanapp_id}")

        # Filter repayment schedules based on company and loan application
        instance = RestructureSchedule.objects.filter(company_id=company_id, loan_id_id=loanapp_id)
        total=len(instance)
        # Order by repayment date to find the earliest pending repayment
        next_due_schedule = instance.order_by('repayment_date').first()

        if next_due_schedule:
            # Fetch next due date and instalment amount
            next_due_date = next_due_schedule.repayment_date
            amount_due = next_due_schedule.instalment_amount
            return success({
                "next_due_date": next_due_date,
                "amount_due": amount_due,
                "total":total
            })
        else:
            return error("No pending repayment schedules found.")
            
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loan_detail(company_id,loan_id):
    try:
        loan_instance=Loan.objects.filter(loan_id=loan_id,company_id=company_id)
        serializer = LoanSerializer(loan_instance,many=True)
          
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_loanapp_detail(loanapp_id,company_id):
    try:
        loan_app_instance=LoanApplication.objects.filter(application_id=loanapp_id,company_id=company_id)
        serializer = LoanapplicationSerializer(loan_app_instance,many=True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")


def view_loantype_detail(loantype_id,company_id):
    try:
        loantype_instance=LoanType.objects.filter(loantype_id=loantype_id,company_id=company_id)
        serializer = LoanTypeSerializer(loantype_instance,many=True)
        return success(serializer.data)
    except Exception as e:
        return error(f"An error occurred: {e}")

def loan_refinance(company_id,loanapp_id,loan_id,new_tenure,new_amount,repayment_start_date, approval_status = None,rejected_reason = None,loantype_id=None):
    BASE_URL = "https://bbaccountingtest.pythonanywhere.com/loan-setup/"
    
    try:
        print('loanapp_id',loanapp_id)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        instance1 = LoanApplication.objects.get(id=loanapp_id)
        if instance1:
            instance1.application_status='Cleared balance and moved for refinance'
            instance1.save()
        instance = Loan.objects.get(loanapp_id_id=loanapp_id)
        if approval_status == "refinanced":
            instance.tenure=new_tenure
            instance.loan_status='refinanced'
            instance.loan_amount=new_amount
            # instance.workflow_stats = "restructured"
            instance.save()
            get_loan = Loan.objects.get(id = loan_id)
            get_centralaccount = CentralFundingAccount.objects.get(company_id = company_id)
            get_centralaccount.account_balance -= get_loan.approved_amount    # the loan amount depit from centralfundingaccount
            get_loanaccount = LoanAccount.objects.get(loan_id = loan_id)
            get_loanaccount.principal_amount += get_loan.approved_amount      # the loan amount credit from centralfundingaccount
            get_centralaccount.save()
            get_loanaccount.save()

            repayment_instance=RepaymentSchedule.objects.filter(loan_application_id=loanapp_id)
            print('length',len(repayment_instance),repayment_instance)
            for data in repayment_instance:
                if data.repayment_status=='Pending':
                    data.repayment_status='Settled'
                    data.save()

            # =============== calling repayment schedule  =====================
            schedules = calculate_repayment_schedule(new_amount,instance.interest_rate, new_tenure, instance.tenure_type, instance.repayment_schedule, instance.loan_calculation_method,repayment_start_date, instance.repayment_mode)
            print('schedules created',schedules)
            if schedules['status_code'] == 1: 
                return error(f"An error occurred: {schedules['data']}")
            print('count',len(schedules))
            for data in schedules['data']:
                # generate Unique id 
                generate_id = RefinanceSchedule.objects.last()
                last_id = '00'
                if generate_id:
                    last_id = generate_id.schedule_id[10:]
                schedule_id = unique_id('SID',last_id)

                aa = RefinanceSchedule.objects.create(
                    company_id = instance.company.id,
                    schedule_id = schedule_id,
                    loan_application_id = instance1.id,
                    loan_id_id = loan_id,
                    period = float(data['Period']),
                    repayment_date = data['Due_Date'],
                    instalment_amount = float(data['Installment']),
                    principal_amount = float(data['Principal']),
                    interest_amount = float(data['Interest']),
                    remaining_balance = float(data['Closing_Balance']),
                )
            generate_id = LoanApplication.objects.last()
            last_id = '00'
            if generate_id:
                last_id = generate_id.application_id[9:]
            refinance_id = unique_id('RF',last_id)
            print('loan ref id',refinance_id)
            print('cus if',instance1.customer_id)
            customer=Customer.objects.get(customer_id=instance1.customer_id)
            print('id',customer.id)
            customerid=customer.id
            print('customerid',customerid)
            instance2 = LoanApplication.objects.create(
            company_id = company_id,
            application_id = refinance_id,
            customer_id_id =customerid,
            loantype_id = instance1.loantype_id,
            loan_amount = new_amount,
            loan_purpose = instance1.loan_purpose,
            application_status = 'Submitted',
            loan_calculation_method = instance1.loan_calculation_method,
            repayment_schedule = instance1.repayment_schedule,
            repayment_mode = instance1.repayment_mode,
            interest_rate = instance1.interest_rate,
            disbursement_type = instance1.disbursement_type,
            interest_basics =instance1.interest_basics,
            repayment_start_date =instance1.repayment_start_date,
            tenure = new_tenure,
            tenure_type = instance1.tenure_type,
            description = instance1.description,
            workflow_stats = "Submitted",
            is_active = True,
            )
            print('instance2',instance2)
            refinance_reference.objects.create(
                loanapp_num=instance1.application_id,
                refinance_num=refinance_id

            )
        elif approval_status == "Rejected":
            instance.application_status = "Rejected"
            instance.rejected_reason = rejected_reason
        else:
            instance.application_status = "Submitted"
        instance.save()
        return success("Successfully Refinanced Your Application")
    except LoanApplication.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_repayment_refinance_schedules(company_id,loanapp_id):
    try:
        print(f"company_id: {company_id}, loanapp_id: {loanapp_id}")
        instance = RefinanceSchedule.objects.filter(company_id=company_id,loan_id_id = loanapp_id)
        serializer = RefinancescheduleSerializer(instance,many=True)
        
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_next_refinance_schedules(company_id, loanapp_id):
    try:
        print(company_id,loanapp_id)
        print(f"company_id: {company_id}, loanapp_id: {loanapp_id}")

        # Filter repayment schedules based on company and loan application
        instance = RefinanceSchedule.objects.filter(company_id=company_id, loan_id_id=loanapp_id)
        total=len(instance)
        # Order by repayment date to find the earliest pending repayment
        next_due_schedule = instance.order_by('repayment_date').first()

        if next_due_schedule:
            # Fetch next due date and instalment amount
            next_due_date = next_due_schedule.repayment_date
            amount_due = next_due_schedule.instalment_amount
            return success({
                "next_due_date": next_due_date,
                "amount_due": amount_due,
                "total":total
            })
        else:
            return error("No pending repayment schedules found.")
            
    except Exception as e:
        return error(f"An error occurred: {e}")

def confirmed_rstructure_schedule(loan_id):
    try:
        loans = RestructureSchedule.objects.filter(loan_id_id = loan_id)
        for data in loans:
            data.confirmed_status = 'Confirmed'
            data.save()
        return success('Sucessfully Confirmed') 
    except Exception as e:
        return error(f"An error occurred: {e}")


def getting_restructure_schedule(schedule_id = None,uniques_id = None):
    try:
        if uniques_id is not None:
            instance=RestructureSchedule.objects.get(id= uniques_id)
            serializer=RestructurescheduleSerializer(instance)
        else:
            instance=RestructureSchedule.objects.get(schedule_id= schedule_id)
            serializer=RestructurescheduleSerializer(instance)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")


def paid_restructure_schedule(schedule_id):
    try:
        print('schedule_id',schedule_id)
        schedule=RestructureSchedule.objects.get(id = schedule_id)
        if schedule:
            schedule.repayment_status = 'Paid'
            schedule.paid_amount=schedule.instalment_amount

            schedule.save()
        return success('Sucessfully Confirmed') 
    except Exception as e:
        return error(f"An error occurred: {e}")


def view_active_loan(loan_id=None,loanapp_id = None,company=None):
    try:
        print(loan_id,loanapp_id,company)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loan_id is not None:
            record = Loan.objects.get(pk=loan_id)
            print("==================",record.id)
            serializer = LoanSerializer(record)
        elif loanapp_id is not None:
            record = Loan.objects.filter(loanapp_id_id=loanapp_id,loan_status='Active_Loan').last()
            serializer = LoanSerializer(record)

        elif company is not None:
            records = Loan.objects.filter(company_id = company,loan_status='Active_Loan')
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


def view_refinance_loan(loan_id=None,loanapp_id = None,company=None):
    try:
        print(loan_id,loanapp_id,company)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loan_id is not None:
            record = Loan.objects.get(pk=loan_id)
            print("==================",record.id)
            serializer = LoanSerializer(record)
        elif loanapp_id is not None:
            record = Loan.objects.filter(loanapp_id_id=loanapp_id,loan_status='refinanced').last()
            serializer = LoanSerializer(record)

        elif company is not None:
            records = Loan.objects.filter(company_id = company,loan_status='refinanced')
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


def refinance_list(company_id):
    try:
        print('company_id',company_id)
        data=Loan.objects.filter(company_id=company_id,loan_status='refinanced')
        # data1=Loan.objects.filter(company_id=company_id,loanapp_id_id=data.id)
        print('data',data)
        serializer = LoanSerializer(data,many=True)
        
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")

def getting_refinance_schedule(schedule_id = None,uniques_id = None):
    try:
        if uniques_id is not None:
            instance=RefinanceSchedule.objects.get(id= uniques_id)
            serializer=RefinancescheduleSerializer(instance)
        else:
            instance=RefinanceSchedule.objects.get(schedule_id= schedule_id)
            serializer=RefinancescheduleSerializer(instance)
        return success(serializer.data) 
    except Exception as e:
        return error(f"An error occurred: {e}")


def paid_refinance_schedule(schedule_id):
    try:
        print('schedule_id',schedule_id)
        schedule=RefinanceSchedule.objects.get(id = schedule_id)
        if schedule:
            schedule.repayment_status = 'Paid'
            schedule.paid_amount=schedule.instalment_amount

            schedule.save()
        return success('Sucessfully Confirmed') 
    except Exception as e:
        return error(f"An error occurred: {e}")

def confirmed_refinance_schedule(loan_id):
    try:
        loans = RefinanceSchedule.objects.filter(loan_id_id = loan_id)
        for data in loans:
            data.confirmed_status = 'Confirmed'
            data.save()
        return success('Sucessfully Confirmed') 
    except Exception as e:
        return error(f"An error occurred: {e}")

def view_refinance_loan(loan_id=None,loanapp_id = None,company=None):
    try:
        print(loan_id,loanapp_id,company)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if loan_id is not None:
            record = Loan.objects.get(pk=loan_id)
            print("==================",record.id)
            serializer = LoanSerializer(record)
        elif loanapp_id is not None:
            record = Loan.objects.filter(loanapp_id_id=loanapp_id).exclude(loan_status='refinanced')
            serializer = LoanSerializer(record)

        elif company is not None:
            records = Loan.objects.filter(company_id = company).exclude(loan_status='refinanced')
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
