from rest_framework import serializers
from .models import WithdrawalApprovals

class WithdrawalApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalApprovals
        fields = [
            "id",
            "userId",
            "brokerUserId",
            "email",
            "amount",
            "walletAddress",
            "currency",
            "pspName",
            "first_approval_by",
            "first_approval_action",
            "first_approval_at",
            "first_approval_note",
            "second_approval_by",
            "second_approval_action",
            "second_approval_at",
            "second_approval_note",
            "brokerBankingId",
            "ordertransactionid",
            "bankDetails"
        ]
        read_only_fields = [
            "first_approval_by",
            "first_approval_action",
            "first_approval_at",
            "first_approval_note",
            "second_approval_by",
            "second_approval_action",
            "second_approval_at",
            "second_approval_note",
        ]
