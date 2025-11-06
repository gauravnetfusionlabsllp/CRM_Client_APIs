from django.db import models
import uuid

# Create your models here.


class TimeStampModel(models.Model):
    """Abstract base class for models with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderDetails(TimeStampModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success')
    ]
    userId = models.CharField(max_length=150, null=True, blank=True)
    full_name = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=250, null=True, blank=True)
    brokerUserId = models.CharField(max_length=150, null=True, blank=True)
    orderId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.CharField(max_length=150, unique=False, null=True, blank=True)
    status = models.CharField(max_length = 150, choices=STATUS_CHOICES, default='PENDING')
    tradingId = models.CharField(max_length=150, null=True, blank=True)
    brokerBankingId = models.CharField(max_length=150, null=True, blank=True)
    pspName = models.CharField(max_length=150, null=True, blank=True)
    

    def __str__(self):
        return str(self.userId)

    class Meta:
        verbose_name = "Order Details"
        verbose_name_plural = "Order Detail"
        db_table = "OrderDetails"