from django.urls import path
from .views import *

urlpatterns = [
    path("micro-service/",MSAPIModule.as_view(), name="MS"),
    path("micro-service-forgot/",MSAPIPASS.as_view(), name="MSAPIPASS"),
    path("api/",EDMSModule.as_view(), name="edms"),
	]
