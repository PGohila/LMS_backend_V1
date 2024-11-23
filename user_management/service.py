import json
import random
from django.core.exceptions import ValidationError
from django.apps import apps
from .models import *
from .serializers import *
from mainapp.middleware import get_current_request
from mainapp.scripts import *
from django.db.models import Q
from django.contrib.auth.hashers import make_password,check_password
from lms_backend.settings import EMAIL,PASSWORD

import uuid

def simple_unique_id_generation(prefix, identifier):

    unique_part = str(uuid.uuid4())
    
    return f"{prefix}-{identifier}-{unique_part}"



    
def get_user(id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        if id is not None:
            record=User.objects.get(pk=id)
            serializers=UserSerializer(record)
            return success(serializers.data)
        else:
            instance = User.objects.filter(is_active=True)
            serializers=UserSerializer(instance,many=True)
            return success(serializers.data)
    
    except User.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def change_password(user_id, old_password, new_password, confirm_password):
    try:
        user = User.objects.get(id=user_id)
        if not check_password(old_password, user.password):
            return error("Old password is incorrect.")
        if new_password != confirm_password:
            return error("New password and confirm password do not match.")
        user.password = make_password(new_password)
        user.save()
        return success("Password changed successfully.")
    except User.DoesNotExist:
        return error("User does not exist.")
    except Exception as e:
        return error(f"An error occurred: {e}")


def forgot_password(email):
    try:
        user = User.objects.get(email=email)
        generate_and_send_otp(user)
        return success("Password changed successfully.")
    except User.DoesNotExist:
        return error("User does not exist.")
    except Exception as e:
        return error(f"An error occurred: {e}")

def verify_forgot_password(email,otp):
    try:
        user = User.objects.get(email=email)
        otp_record = OTP.objects.filter(user=user,status = 'UNUSED').order_by('-created_at').first()
        if otp_record.otp != otp:
            return error('Invalid OTP')
        otp_record.status = 'USED'
        otp_record.save()

        return success("OTP Verification successfully.")
    except User.DoesNotExist:
        return error("User does not exist.")
    except OTP.DoesNotExist:
        return error("User does not exist.")
    except Exception as e:
        return error(f"An error occurred: {e}")

def set_password(email,new_password, confirm_password):
    try:
        user = User.objects.get(email=email)
        if new_password != confirm_password:
            return error("New password and confirm password do not match.")
        user.password = make_password(new_password)
        user.save()
        return success("Password changed successfully.")
    except User.DoesNotExist:
        return error("User does not exist.")
    except Exception as e:
        return error(f"An error occurred: {e}")
    
def user_registration(first_name, last_name, email, phone_number, password,user_profile):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required') 
        
        instance = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password=make_password(password),
            user_profile_id=user_profile
            # maker=maker,
            # checker=checker
        )
        return success(f'Successfully created {instance} ')
    
    except User.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    

def user_edit(id ,first_name, last_name, email, phone_number, password,user_profile):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = User.objects.get(pk=id)
        instance.first_name=first_name
        instance.last_name=last_name
        instance.email=email
        instance.phone_number=phone_number
        instance.password=make_password(password)
        instance.user_profile_id=user_profile
        # instance.maker=maker
        # instance.checker=checker
        instance.save()
        return success(f'Successfully Updated {instance} ')
    
    except User.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    
    
def user_delete(id):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = User.objects.get(pk=id)
        instance.is_active=False
        instance.save()
           
        return success(f'Successfully deleted {instance} ')
    
    except User.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def get_user_record():
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        user_record = User.objects.filter(~Q(pk=request.user.pk))
        serializers=UserSerializer(user_record,many=True).data
        return success(serializers)

    except Exception as e:
        # Return an error response with the exception message
        return error(f"An error occurred: {e}")


def role_list(id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if id is not None:
            record=Role.objects.get(pk=id)
            serializers=RoleSerializer(record).data
            return success(serializers)
        else:
            record=Role.objects.all()
            serializers=RoleSerializer(record,many=True).data
            return success(serializers)
    
    except Role.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
def role_create(name, description):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Role.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        return success(f'Successfully created {instance} ')
    
    except Role.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    

def role_edit(id,name, description):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Role.objects.get(pk=id)
        instance.name=name
        instance.description=description
        instance.update_by=request.user
        instance.save()
        return success(f'Successfully Updated {instance} ')
    
    except Role.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    

def role_delete(id):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = Role.objects.get(pk=id)
        instance.delete()           
        return success(f'Successfully deleted {instance} ')
    
    except Role.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


# User Profile

def userprofile_list(id=None):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        if id is not None:
            record=UserProfile.objects.get(pk=id)
            serializers=UserProfileSerializer(record).data
            return success(serializers)
        else:
            record=UserProfile.objects.all()
            serializers=UserProfileSerializer(record,many=True).data
            return success(serializers)
    
    except UserProfile.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")

def userprofile_create(name,role, description):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        role_instances = Role.objects.filter(id__in=role)

        instance = UserProfile.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        instance.role.set(role_instances)
        instance.save()
        return success(f'Successfully created {instance} ')
    
    except UserProfile.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    

def userprofile_edit(id,name,role, description):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        role_instances = Role.objects.filter(id__in=role)

        instance = UserProfile.objects.get(pk=id)
        instance.name=name
        instance.role.set(role_instances)
        instance.description=description
        instance.update_by=request.user
        instance.save()
        return success(f'Successfully Updated {instance} ')
    
    except UserProfile.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")
    

def userprofile_delete(id):

    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        instance = UserProfile.objects.get(pk=id)
        instance.delete()           
        return success(f'Successfully deleted {instance} ')
    
    except UserProfile.DoesNotExist:
        return error('Instance does not exist')
    except Exception as e:
        return error(f"An error occurred: {e}")


def get_user_permission(id):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        role_obj = Role.objects.get(pk=id)
        permission_records = role_obj.permissions.all()
        serializers=FunctionSerializer(permission_records,many=True).data
        return success(serializers)

    except Exception as e:
        return error(f"An error occurred: {e}")


def function_all():
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        permission_records=Function.objects.all()
        serializers=FunctionSerializer(permission_records,many=True).data
        return success(serializers)

    except Exception as e:
        return error(f"An error occurred: {e}")


def update_user_permission(id,permission):
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        role_obj = Role.objects.get(pk=id)
        role_obj.permissions.set(permission)
        role_obj.save()
        return success('success')

    except Exception as e:
        return error(f"An error occurred: {e}")


def logout():
    request = get_current_request()
    if not request.user.is_authenticated:
        return error('Login required')
    return success('logout successfully')


# Load the function names from the configuration file
def load_function_names_from_config(config_path='config/function_config.json'):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        return config.get('functions', [])

# Example usage in a view:
def function_setup():
    try:
        request = get_current_request()
        if not request.user.is_authenticated:
            return error('Login required')
        
        user = request.user  # Use the currently logged-in user
        function_names = load_function_names_from_config()  # Load from the configuration file
        print('function name',function_names)
        records_list = []
        print('data is comming')
        for function_name in function_names:
            # Check if the function already exists
            if not Function.objects.filter(function_name=function_name).exists():
                # Create a new function
                function = Function.objects.create(
                    function_name=function_name,
                    description=None,  # You can modify this to add descriptions if needed
                    created_by=user
                )
                # Assign a unique ID to the function
                function.function_id = simple_unique_id_generation("FUN", function.id)
                function.save()  # Save only if it's a new record
                records_list.append(function.function_name)
            else:
                # Log if the function already exists
                print(f"Function '{function_name}' already exists.")

    except Exception as e:
        return error(f"An error occurred: {e}")
    
def multi_factor_authentication(otp=None):
    request = get_current_request()
    if not request.user.is_authenticated:
        return error('Login required')
    user = request.user
    otp_record = OTP.objects.filter(user=user,status = 'UNUSED').order_by('-created_at').first()
    if otp_record.otp != otp:
        return error('Invalid OTP')
    user.multi_factor_auth = True  
    user.save()
    otp_record.status = 'USED'
    otp_record.save()

    return success('OTP verified successfully')


def generate_and_send_otp(user=None):
    if user is None:
        request = get_current_request()
    
        if not request.user.is_authenticated:
            return error('Login required')
        user = request.user
    otp_record = OTP.objects.create(user=user)
    otp_code = otp_record.otp
    send_otp_to_user(otp_code)
    return success('OTP generated successfully')

import requests

def get_access_token():
    url = "https://genericdelivery.pythonanywhere.com/api/token/"
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers)
    access_data = response.json()
    return access_data.get('access')
    

def send_otp_to_user( otp_code):
    request = get_current_request()
    if not request.user.is_authenticated:
        return error('Login required')
    user = request.user
    access_token = get_access_token()
    print('access_token',access_token)

    url = "https://genericdelivery.pythonanywhere.com/templatemanage/api/message/"
    
    # Prepare the request data
    payload = {
        "channel_id": 1,
        "template_id": "TMP22112407355106",
        "recipient_list": [user.email],  
        "task_data": {
            "otp": otp_code,
            "name":user.first_name 
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"  
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return success("OTP sent successfully!")
    else:
        return success(f"Failed to send OTP. Status Code: {response.status_code}, Response: {response.text}")


