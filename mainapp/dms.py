from datetime import timezone,datetime
import random
from django.core.exceptions import ValidationError
from .models import *
from .serializers import *
from .middleware import get_current_request
from .scripts import *
from .loan_calculation import *
from django.shortcuts import get_object_or_404



def unique_id_generate_doc(prefix='DID'):
    while True:
        # Get current date and time
        current_datetime = datetime.now()
        current_date_str = current_datetime.strftime("%m%d")  # Format as MMDD
        current_year_str = current_datetime.strftime("%y")  # 2-digit year
        current_time_str = current_datetime.strftime("%H%M")  # HHMM
        current_seconds_str = current_datetime.strftime("%S")[:2]  # 2-digit seconds

        # Generate a 2-digit random number
        random_number = random.randint(0, 99)

        # Combine prefix, date, year, time, seconds, and random number
        unique_id = f"{prefix}{current_date_str}{current_year_str}{current_time_str}{current_seconds_str}{random_number:02d}"

        # Check if the ID already exists in the database
        if not DocumentUpload.objects.filter(document_id=unique_id).exists():
            return unique_id


def is_valid_current_datetime(from_date, to_date):
    # Get current datetime in UTC timezone
    current_datetime = timezone.now()

    # Convert strings to datetime objects
    # from_datetime = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")
    # to_datetime = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

    # Check if current datetime falls within the range
    print('from_date',from_date)
    print('current_datetime',current_datetime)
    print('to_date',to_date)
    if from_date <= current_datetime <= to_date:
        return True
    else:
        return False

def create_entity(entity_name,entity_type):
    try:
        request = get_current_request()
        entity_id = str(random.randint(10000, 999999))
        CustomDocumentEntity.objects.create(
                entity_type=entity_type,
                entity_name=entity_name,
                entity_id=entity_id,
                created_by=request.user,
            )
        return success('Successfully Created')
    except Exception as e:
        return error(str(e))


def create_folder_for_all_customer(customer_id, company_id):
    print("customer_idcustomer_id456789", customer_id)
    try:
        customer = Customer.objects.get(id=customer_id)
        print("customerobjectsdf", customer, company_id)
        company1 = Company.objects.get(id=company_id)
        entity_instance = CustomDocumentEntity.objects.get(entity_name=company1.name)
        print('Entity_instafghjnceentity_type777:', entity_instance)

        # Extract the entity_id from the retrieved entity instance
        entity_id = entity_instance.entity_id

        request = get_current_request()
        if customer:
            # Create the main folder for the customer
            customer_folder = FolderMaster.objects.create(
                folder_id=f"folder_{customer.customer_id}",
                folder_name=f"{customer.firstname}",  
                description=f"Folder for Customer {customer.firstname}",
                entity=entity_instance,
                customer=customer,
                company=company1,
                master_checkbox_file=False,
                default_folder=True,
                created_by=request.user
            )
            print(f"Folder_created_for_customer889 {customer.firstname}")

            # Create two child subfolders inside the customer's folder
            collateral_folder = FolderMaster.objects.create(
                folder_id=f"folder_collateral_{customer.customer_id}",
                folder_name="Collateral Folder List",
                description="Default Collateral Folder",
                parent_folder=customer_folder,  # Make it a child of the customer's folder
                entity=entity_instance,
                customer=customer,
                company=company1,
                master_checkbox_file=False,
                default_folder=False,
                created_by=request.user
            )
            print(f"Collateral Folder created as a child of {collateral_folder}'s folder")

            loan_agreement_folder = FolderMaster.objects.create(
                folder_id=f"folder_loan_agreement_{customer.customer_id}",
                folder_name="Loan Agreement",
                description="Default Loan Agreement Folder",
                parent_folder=customer_folder,  # Make it a child of the customer's folder
                entity=entity_instance,
                customer=customer,
                company=company1,
                master_checkbox_file=False,
                default_folder=False,
                created_by=request.user
            )
            print(f"Loan Agreement Folder created as a child of {loan_agreement_folder}'s folder")

        return success('Folders created for customer including default child folders.')

    except CustomDocumentEntity.DoesNotExist:
        return error('Entity not found.')
    except Exception as e:
        return error(str(e))

def document_upload_history(document_id):
    print("------------",document_id)
    try:
        record=DocumentUpload.objects.get(document_id=document_id)
     
        print('entity_type==///',record.folder_id)
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        record_count = DocumentUploadHistory.objects.filter(document_id=document_id).count()
        new_version = record_count + 1
        records=DocumentUploadHistory.objects.create(
            document_id=document_id,
            document_title=record.document_title,
            document_category_id=record.document_category.id,
            document_type_id=record.document_type.id,
            description=record.description,
            document_upload=record.document_upload,
            folder_id=record.folder_id,
            upload_date=datetime.now(),
            start_date=record.start_date,
            end_date=record.end_date,         
            document_size=record.document_upload.size,
            version=new_version
            )    
        print('record+++',records.document_id)
        
     
        for data in record.entity_type:
            entity = CustomDocumentEntity.objects.get(entity_id=data)
            records.entity_type.add(entity)
            records.save()
    except Exception as e:
        return error(e)   

def document_upload_audit(status,document_id):
    print("statusdocument_id",status,document_id)
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login requried')
        
        record=DocumentUpload.objects.get(document_id=document_id)

        records=DocumentUploadAudit.objects.create(
            document_id=document_id,
            document_title=record.document_title,
            document_category_id=record.document_category.id,
            document_type_id=record.document_type.id,
            description=record.description,
            document_upload=record.document_upload,
            folder_id=record.folder_id,
            upload_date=datetime.now(),
            start_date=record.start_date,
            end_date=record.end_date,         
            document_size=record.document_upload.size,
            status=status,          
            created_by=request.user,
        )    
        for data in records.entity_type:
            entity = CustomDocumentEntity.objects.get(entity_id=data)
            records.entity_type.add(entity)
            records.save()
    except Exception as e:
        return error(e)       
