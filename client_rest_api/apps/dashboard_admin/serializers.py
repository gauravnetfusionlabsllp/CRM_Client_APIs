from rest_framework import serializers
from .models import WithdrawalApprovals

class WithdrawalApprovalSerializer(serializers.ModelSerializer):
    tradingId = serializers.SerializerMethodField()
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
            "paymentMethod",
            "first_approval_by",
            "first_approval_name",
            "first_approval_action",
            "first_approval_at",
            "first_approval_note",
            "second_approval_name",
            "second_approval_by",
            "second_approval_action",
            "second_approval_at",
            "second_approval_note",
            "brokerBankingId",
            "ordertransactionid",
            "bankDetails",
            "tradingId",
            "created_at"
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

    def get_tradingId(self, obj):
        # If FK exists, return tradingId, else None
        if obj.ordertransactionid:
            return obj.ordertransactionid.tradingId
        return None