from django.db import transaction
from apps.users.models import KYCStatus

def check_pending_kyc():
    pending_kyc = KYCStatus.objects.filter(KYC_status='pending')
    if pending_kyc:
        for kyc in pending_kyc:
            # Call your external API or logic
            # status = get_kyc_status(kyc)  # implement this

            # if status in ['approved', 'rejected']:
            #     kyc.KYC_status = status
            #     kyc.save(update_fields=['KYC_status'])
            print(kyc)
