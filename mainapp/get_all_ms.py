import inspect
import random
from .models import *
import json
import requests
from datetime import datetime
from mainapp import ms_crud as microservices
# service import

def create_module(module_name):
    try:
        obj = ModuleRegistration.objects.filter(module_name=module_name)
        if obj.exists():
            return obj.last().id

        obj = ModuleRegistration.objects.create(
            module_name=module_name,
        )
        return obj.id
    except Exception as error:
        print('Error:', error)
        return False
        
def ms_module_mapping(mservice_id,module_id):
    try:
        if MsToModuleMapping.objects.filter(mservice_id=mservice_id).exists():
            return 'already registered'

        print('mservice_id',mservice_id,module_id,type(mservice_id),type(module_id))
        ms_reg_obj = MSRegistration.objects.get(mservice_id=mservice_id)
        print('ms_reg_obj',ms_reg_obj)
        obj = MsToModuleMapping.objects.create(
            # mservice_id_id=ms_reg_obj,
            mservice_id_id=mservice_id,
            module_id_id=module_id,
        )
        print('obj',obj)
        return obj.id
    except Exception as error:
        print('Error: error is here....', error)
        return False


def so_registration(register):
    try:
        description = register.formatted_mservice_name()

        service_data = {
            'ms_id': register.mservice_id,
            'serviceplan_id': None,
            'channel_id': None,
            'description': description,
        }

        service_json_data = json.dumps(service_data)
        service_api_url = 'http://127.0.0.1:8000/register-serviceplan/'
        headers = {
            'Content-Type': 'application/json',  # Specify the correct Content-Type
        }

        service_response = requests.post(service_api_url, data=service_json_data, headers=headers)

        if service_response.status_code == 200:
            print("Service Request successful",service_response)
        else:
            print(f"Service Request failed with status code: {service_response.status_code}")
            print(f"Service Request failed with: {service_response.json()}")
        
        return service_response
    except Exception as error:
        print('Error: error is here....', error)
        return False

def registered_the_ms(mservice_name, arguments_list, required_parameter, optional_parameter, arguments=None):
    """
    Register a microservice in the MS Registration Table with its parameters.

    Args:
        mservice_name (str): The name of the microservice.
        arguments_list (list): A list of arguments of the microservice.
        required_parameter (list): A list of required parameters.
        optional_parameter (list): A list of optional parameters.
        arguments (dict, optional): Additional arguments for the microservice. Defaults to None.

    Returns:
        str or bool: Returns 'already registered' if the microservice is already registered, True if registration is successful, False otherwise.
    """
    try:
        if MSRegistration.objects.filter(mservice_name=mservice_name).exists():
            return 'already registered'

        today = datetime.now()
        MS_ID = 'MS' + str(today.day) + str(today.strftime('%m')) + str(random.randint(1111, 9999))

        register = MSRegistration.objects.create(
            mservice_id = MS_ID,
            mservice_name=mservice_name,
            arguments=arguments,
            arguments_list=arguments_list,
            required_parameter=required_parameter,
            optional_parameter=optional_parameter
        )

        so_register = so_registration(register)

        print('so_register',so_register)
                
        return register.mservice_id
    except Exception as error:
        print('Error:', error)
        return False

def get_functions_with_parameters(module):
    """
    Get all function names and their parameters from the provided module.

    Args:
        module (module): The module to inspect.

    Returns:
        tuple: A tuple containing lists of function names, all parameters, mandatory parameters, and optional parameters.
    """
    functions_list = inspect.getmembers(module, inspect.isfunction)
    function_name_list = []
    function_all_parameter = []
    function_mandatory_parameter = []
    function_optional_parameter = []
    
    for name, func in functions_list:
        signature = inspect.signature(func)
        parameters = list(signature.parameters.keys())
        parameters_values = list(signature.parameters.values())

        function_name_list.append(name)
        function_all_parameter.append(parameters)
        function_mandatory_parameter.append([param for param in parameters if parameters_values[parameters.index(param)].default == inspect.Parameter.empty])
        function_optional_parameter.append([param for param in parameters if parameters_values[parameters.index(param)].default != inspect.Parameter.empty])

    return function_name_list, function_all_parameter, function_mandatory_parameter, function_optional_parameter

# service list
module_lists=[microservices]
all_module_list = [module_lists] # here combining all the module here

# Register microservices for all modules
for module_list in all_module_list: 
    print('module_list ',module_list)
    for module in module_list:
        module_name = module.__name__
        get_resp = create_module(module_name)
        if get_resp == 'already registered':
            continue
        print('module ',module.__name__)
        function_name_list, function_all_parameter, function_mandatory_parameter, function_optional_parameter = get_functions_with_parameters(module)
        for function_name, function_all_parameter, function_mandatory_parameter, function_optional_parameter in zip(function_name_list, function_all_parameter, function_mandatory_parameter, function_optional_parameter):
            resp = registered_the_ms(function_name, function_all_parameter, function_mandatory_parameter, function_optional_parameter, arguments=None)
            if resp == 'already registered':
                print('Microservice already registered:', function_name)
                continue
            # let mapped module to ms
            print('module id ',get_resp)
            print('ms id ',resp)
            # let mapped module to ms
            get_mmm_resp =  ms_module_mapping(resp,get_resp)
            # get_mmm_resp =  (resp,get_resp)
            print('get_mmm_resp ',get_mmm_resp)
print('Process completed.')

