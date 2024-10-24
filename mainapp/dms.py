from datetime import timezone
import random
from django.core.exceptions import ValidationError
from .models import *
from .serializers import *
from .middleware import get_current_request
from .scripts import *
from .loan_calculation import *
from django.shortcuts import get_object_or_404



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


