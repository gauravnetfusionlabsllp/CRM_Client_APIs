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
    orderId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    userId = models.CharField(max_length=150, unique=False, null=True, blank=True)
    brokerUserId = models.CharField(max_length=150, unique=False, null=True, blank=True)
    amount = models.CharField(max_length=150, unique=False, null=True, blank=True)
    

    def __str__(self):
        return str(self.orderId)

    class Meta:
        verbose_name = "Order Details"
        verbose_name_plural = "Order Detail"
        db_table = "OrderDetails"