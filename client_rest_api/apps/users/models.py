from django.db import models

# Create your models here.
from django.db import models


class RegistrationLog(models.Model):
    # User details
    country = models.CharField(max_length=100, blank=True, null=True)
    document_type = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    dob = models.CharField(max_length=20, blank=True, null=True)          # or DateField
    id_number = models.CharField(max_length=150, blank=True, null=True)
    address = models.JSONField(blank=True, null=True)
    issue_date = models.CharField(max_length=20, blank=True, null=True)   # or DateField
    expiry_date = models.CharField(max_length=20, blank=True, null=True)  # or DateField
    confidence_notes = models.TextField(blank=True, null=True)

    # Verification flags
    wpotpverified = models.BooleanField(default=False)
    wpqrverified = models.BooleanField(default=False)
    smsotpverified = models.BooleanField(default=False)

    # Auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}"

class ChangeReguslationLog(models.Model):
    email = models.EmailField(blank=True, null=True, unique=True)
    old_email = models.EmailField(blank=True, null=True)
    uuid = models.CharField(max_length=100, blank=True, null=True, unique=True)
    def __str__(self):
        return f"{self.old_email}"




class KYCStatus(models.Model):
    email = models.EmailField(blank=True, null=True, unique=True)
    kyc_status = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return f"{self.email}"