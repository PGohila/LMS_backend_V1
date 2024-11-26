from django.urls import path
from .views import *
from .ms_crud import *

urlpatterns = [
    path("micro-service/",MSAPIModule.as_view(), name="MS"),
    path("api/",EDMSModule.as_view(), name="edms"),
    path("dashboard_repayment/" , dashboard_repayment, name="dashboard_repayment")
	]
