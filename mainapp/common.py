from mainapp.models import *
from .scripts import *

def log_audit_trail(user, screen_name,instance, action, details=None):
    print("bdjshbjfhfjadsnhjaction",action,user,screen_name,instance,details)
    #Create 1 Customer Registration CM211124001 Object Created.
    try:
        content_type = ContentType.objects.get_for_model(instance.__class__)
        print("content_type2345678",content_type)
        Audit_Trail=AuditTrail.objects.create(
            user_id = user,
            screen_name=screen_name,
            content_type = content_type,
            object_id = instance.id,
            content_object = instance,
            action = action,
            details = details,
        )
        print("Audit_Traile4r5y67u8io",Audit_Trail)
        return 'Audittrail successfully Added'
    except Exception as e:
        return error(str(e))