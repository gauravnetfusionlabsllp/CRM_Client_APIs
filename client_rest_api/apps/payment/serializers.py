# orders/serializers.py
from rest_framework import serializers
from .models import OrderDetails
from apps.dashboard_admin.models  import BankingDetails

class OrderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = "__all__"


class WithdrawalApprovalActionSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.DictField()

    def validate(self, attrs):
        data = attrs.get("data", {})

        if "action" not in data:
            raise serializers.ValidationError({"action": "This field is required."})

        if "userId" not in data:
            raise serializers.ValidationError({"userId": "This field is required."})

        if not isinstance(data.get("action"), bool):
            raise serializers.ValidationError({"action": "Action must be true/false."})

        return attrs
    

class BankingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingDetails
        fields = '__all__'