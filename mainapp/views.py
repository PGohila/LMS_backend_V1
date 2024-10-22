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
   
