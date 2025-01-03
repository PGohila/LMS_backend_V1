import json
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.serializers import UserSerializer
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import importlib
from .serializers import*
from django.shortcuts import render,redirect
import inspect
from datetime import datetime
from rest_framework import permissions
from django.contrib.auth.hashers import make_password,check_password
from .scripts import *
from user_management.service import generate_and_send_otp

# MS setup views
def common_response(status_code=0,message=None):
    response = {    
        'status_code':status_code,
        'data':f"""{message}""",
    }
    return response

def check_ms_id_exists_or_not(ms_id):
    try:   
        obj = MSRegistration.objects.get(mservice_id=ms_id) 
        return 'valid_ms_id'
    except MSRegistration.DoesNotExist:
        print('not exits')
        return common_response(status_code=0,message="Invalid micro service id")
    except Exception as error:
        print('Error',error)
        return common_response(status_code=0,message=error)


def get_module(function_name):
    print('FUNCTION NAME ',function_name)
    module = inspect.getmodule(function_name)
    print('module ',module)
    return module.__name__


def call_all_function(module_name, function_name):
    try:
        # Dynamically import the module containing the function
        module = importlib.import_module(module_name)

        # Get the function object from the module
        function = getattr(module, function_name)

        return function

    except ImportError:
        print(f"Failed to import module: {module_name}")

    except AttributeError:
        print(f"Function not found in module: {function_name}")

    except Exception as e:
        print(f"Error occurred while importing function {function_name} from module {module_name}: {e}")

def check_ms_id_exists_or_not(ms_id):
    try:   
        obj = MSRegistration.objects.get(mservice_id=ms_id) 
        return 'valid_ms_id'
    except MSRegistration.DoesNotExist:
        print('not exits')
        return common_response(status_code=0,message="Invalid micro service id")
    except Exception as error:
        print('Error',error)
        return common_response(status_code=0,message=error)
    
def payload_key_validation(ms_id,payload):
    try:
        obj = MSRegistration.objects.get(mservice_id=ms_id)
        mservice_name = obj.mservice_name
        arguments_list = obj.arguments_list
        payload_key = payload.keys()
        for key in payload_key:
            if key not in arguments_list:
                return False
        else:
            return True                
    except MSRegistration.DoesNotExist:
        return common_response(status_code=0,message='micro services id does not exists')
    
def get_module_msid_wise(ms_id):
    try:
        obj = MsToModuleMapping.objects.get(mservice_id=ms_id)  
        print('obj.module_id.module_name   ',obj.module_id.module_name)    
        return obj.module_id.module_name     
    except MsToModuleMapping.DoesNotExist:
        return common_response(status_code=0,message='micro services id does not exists')


class MSAPIModule(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MSSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializers = MSSerializer(data=request.data)
            if serializers.is_valid():
                ms_id = serializers.data['ms_id']
                ms_payload = serializers.data['ms_payload']
                if request.FILES:
                    attachments = request.FILES.keys()
                    for key in attachments:
                        ms_payload[key] = request.data.get(str(key))
                get_response = check_ms_id_exists_or_not(ms_id)
                get_ms_payload = payload_key_validation(ms_id, ms_payload)
                if get_response == 'valid_ms_id':
                    get_obj = MSRegistration.objects.get(mservice_id=ms_id)
                    ms_function = get_obj.mservice_name
                    get_module_name = get_module_msid_wise(ms_id)
                    print('get_module_name',get_module_name,ms_function)
                    my_function = call_all_function(get_module_name, str(ms_function))
                    if my_function:
                        try:
                            fun_response = my_function(**ms_payload)
                            print('fun_response', fun_response)
                            if fun_response['status_code'] == 0:
                                data = fun_response['data']
                                if not isinstance(data, list):
                                    data = [data]
                                return Response(data=data, status=status.HTTP_200_OK)
                            else:
                                return Response(data=fun_response['data'], status=status.HTTP_403_FORBIDDEN)
                        except Exception as error:
                            print('error in function call:', error)
                            return Response({'error': str(error)}, status=status.HTTP_404_NOT_FOUND)
                    else:
                        print('Function Import Error')
                        return Response({'error': 'Function Import Error'}, status=status.HTTP_404_NOT_FOUND)
                else:
                    print('get_response', get_response)
                    return Response({'error': get_response}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('error in main exception:', error)
            return Response({'error': str(error)}, status=status.HTTP_404_NOT_FOUND)
   
class EDMSModule(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MSSerializer

    def post(self,request,*args,**kwargs):
        try:
            serializers = MSSerializer(data=request.data)
            if serializers.is_valid():
                ms_id = serializers.data['ms_id']
                ms_payload = serializers.data['ms_payload']
                if isinstance(ms_payload,str):
                    ms_payload = json.loads(ms_payload)
                file = request.data.get('files')                
                if file:
                    ms_payload['document_upload'] = file
                get_response = check_ms_id_exists_or_not(ms_id)
                # check payaload key are exists or not
                get_ms_payload=payload_key_validation(ms_id,ms_payload)
                if get_response == 'valid_ms_id':
                # get micro service name 
                    get_obj = MSRegistration.objects.get(mservice_id=ms_id)
                    ms_function = get_obj.mservice_name
                    is_auth = get_obj.is_authenticate
                    get_module_name = get_module_msid_wise(ms_id)
                    # call_all_function(app name,micro service filename), function name
                    my_funtion = call_all_function(get_module_name,str(ms_function))
                    print('my_funtion ',my_funtion)
                    if my_funtion:
                        # calling function
                        try:
                            fun_response = my_funtion(**ms_payload)
                            print('fun_response ',fun_response)
                            # return Response(data=common_response(status_code=1,message=fun_response),status=status.HTTP_200_OK)
                            if fun_response['status_code']==0:
                                return Response(data=fun_response['data'],status=status.HTTP_200_OK)
                            else:
                                return Response(data=fun_response['data'], safe=False,status=status.HTTP_403_FORBIDDEN)
                        except Exception as error:
                            print('error sub ',error)
                            return Response(data=str(error),status=status.HTTP_404_NOT_FOUND)                     
                    else:
                        print('somethin error here....')
                        return Response(data="Function Import Error",status=status.HTTP_404_NOT_FOUND)
                else:
                    print('get_response',get_response)
                    return Response(data=get_response,status=status.HTTP_404_NOT_FOUND)    
            else:
                # write handling logic
                return Response(data=serializers.errors,status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print('error main excepiton ',error)
            return Response(data=str(error),status=status.HTTP_404_NOT_FOUND)                       

@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    print('email',email)
    password = request.data.get('password')

    user = authenticate(email=email, password=password)
    data_list = get_permissions_for_session(user)
    if user is not None:
        # Generate tokens using SimpleJWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        serializers=UserSerializer(user).data
        # Include user details along with the tokens
        user_data = {
            'user_data': serializers,
            'access_token': access_token,
            'refresh_token': str(refresh),
            'multi_factor_auth':user.multi_factor_auth,
            'user_permission':data_list
        }
         
        return Response(user_data)
    else:
        return Response({'error': 'Invalid credentials'}, status=400)
    


def get_permissions_for_session(user):
    try:
        
        # request = get_current_request()        
        # if not request.user.is_authenticated:
        #     return error('Login required')
        if user.is_superuser:
            records = Function.objects.all()
            print(user)
            records_list = [record.function_name for record in records]      
            
        else:
            # Filter permissions based on the user's roles
            record = UserProfile.objects.get(pk=user.user_profile.id)
            role_records = record.role.all()
            records_list = []
            for role in role_records:
                permission_records = role.permissions.all()  # Directly use `role`
                records_list.extend([permission.function_name for permission in permission_records]) 

        print('records_list',records_list)
        data_list = [{'permission': records_list}]     
        print('data_list',data_list)   
        return {'permission': records_list}
    except Exception as e:
        return error(str(e))


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
    