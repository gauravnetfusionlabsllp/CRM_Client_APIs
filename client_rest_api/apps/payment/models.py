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
        ('SUCCESS', 'Success'),
        ('CANCELLED', 'Cancelled')
    ]
    userId = models.CharField(max_length=150, null=True, blank=True)
    full_name = models.CharField(max_length=250, null=True, blank=True)
    email = models.CharField(max_length=250, null=True, blank=True)
    brokerUserId = models.CharField(max_length=150, null=True, blank=True)
    transactionId = models.CharField(max_length=250, unique=False, blank=True, null=True, default=None)
    orderId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order_type = models.CharField(max_length = 250,  null=True, default=None)
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

class Userpermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    userid = models.CharField(db_column='userId', max_length=150, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(max_length=150, blank=True, null=True)
    min_visible_amount = models.IntegerField()
    max_visible_amount = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'UserPermissions'



