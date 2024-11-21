import json
from django.core.exceptions import ValidationError
from django.apps import apps
from .models import *
from .serializers import *
from mainapp.middleware import get_current_request
from mainapp.scripts import *
from django.db.models import Q
from django.contrib.auth.hashers import make_password


    
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
        
        instance = UserProfile.objects.get(pk=id)
        instance.name=name
        instance.role=role
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
    
