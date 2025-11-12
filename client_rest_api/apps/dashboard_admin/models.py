from django.db import models
import uuid
from apps.payment.models import OrderDetails

# Create your models here.
class TimeStampModel(models.Model):
    """Abstract base class for models with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserPermissions(TimeStampModel):
    userId = models.CharField(max_length=150, null=True, blank=True)
    email = models.CharField(max_length=150, null=True, blank=True)
    min_visible_amount = models.IntegerField()
    max_visible_amount = models.IntegerField()

    def __str__(self):
        return str(self.userId)

    class Meta:
        db_table = "UserPermissions"



class WithdrawalApprovals(TimeStampModel):
    userId = models.CharField(max_length=150, null=True, blank=True)
    brokerUserId = models.CharField(max_length=150, null=True, blank=True)
    email = models.CharField(max_length=250, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    walletAddress = models.CharField(max_length=150, null=True, blank=True)
    currency = models.CharField(max_length=250, unique=False, blank=True, null=True)
    pspName = models.CharField(max_length=250, unique=False, blank=True, null=True)
    paymentMethod = models.CharField(max_length=250, unique=False, blank=True, null=True)
    first_approval_by = models.IntegerField(null=True,blank=True,help_text="User ID who performed the first approval.")
    first_approval_action = models.BooleanField(default=False,help_text="Whether the first approval was accepted (True) or rejected (False).")
    first_approval_at = models.DateTimeField(null=True,blank=True,help_text="Timestamp of first approval.")
    first_approval_note = models.CharField(null=True,blank=True,help_text="Message of first approval.")
    second_approval_by = models.IntegerField(null=True,blank=True,help_text="User ID who performed the second approval.")
    second_approval_action = models.BooleanField(default=False,help_text="Whether the first approval was accepted (True) or rejected (False).")
    second_approval_at = models.DateTimeField(null=True,blank=True,help_text="Timestamp of second approval.")
    second_approval_note = models.CharField(null=True,blank=True,help_text="Message of second approval.")
    brokerBankingId = models.CharField(max_length=150, null=False, blank=False)
    ordertransactionid = models.ForeignKey(OrderDetails, null=True, blank=True, on_delete=models.CASCADE)
    bankDetails = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return str(self.userId)

    class Meta:
        verbose_name = "Withdrawal Approvals"
        verbose_name_plural = "Withdrawal Approvals"
        db_table = "WithdrawalApprovals"