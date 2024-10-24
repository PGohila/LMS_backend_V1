from django.urls import path
from .views import *

urlpatterns = [
    path("micro-service/",MSAPIModule.as_view(), name="MS"),
    path("api/",EDMSModule.as_view(), name="edms"),
	]
