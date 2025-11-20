from rest_framework import serializers
from .models import RegistrationLog, ChangeReguslationLog

class RegistrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationLog
        fields = '__all__'
        read_only_fields = ['created_at']


class ChangeReguslationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeReguslationLog
        fields = '__all__'
        read_only_fields = ['created_at']
