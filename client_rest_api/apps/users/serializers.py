from rest_framework import serializers
from .models import RegistrationLog

class RegistrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationLog
        fields = [
            "id",
            "country",
            "document_type",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "dob",
            "id_number",
            "address",
            "issue_date",
            "expiry_date",
            "confidence_notes",
            "wpotpverified",
            "wpqrverified",
            "smsotpverified",
            "created_at",
        ]
