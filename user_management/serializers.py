from rest_framework import serializers
from .models import *

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        exclude=['permissions']


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = "__all__"

class UserProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    class Meta:
        model = UserProfile
        fields = "__all__"

class FunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Function
        fields = "__all__"