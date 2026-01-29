from django.db import transaction
from apps.users.models import KYCStatus
from apps.core.DBConnection import *
from apps.core.WebEngage import *
timestamp = current_webengage_time(offset_hours=-8)

import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')


def check_pending_kyc():
    pending_kyc = KYCStatus.objects.filter(kyc_status='pending')
    for kyc in pending_kyc:
        query = f"""
            SELECT u.email, u.kyc_status, u.kyc_note
            FROM crmdb.users AS u
            WHERE u.email = '{kyc.email}'
        """

        data = DBConnection._forFetchingJson(query, using='replica')
        if not data:
            continue
        
        external_status = data[0].get('kyc_status')
        kyc_note = data[0].get('kyc_note', '')
        email = data[0].get('email')

        if external_status == 4:
            # kyc_approved(email, timestamp, timestamp)
            kyc_rejected(email, kyc_note, timestamp)
            kyc.kyc_status = 'approved'
        elif external_status == 5:
            kyc.kyc_status = 'rejected'
        else:
            continue


        dict_ = {
            2: 'Partial KYC',
            3: 'Partial KYC Can Trade',
            4: 'approved',
            5: 'rejected',
            10: 'SumSub Failed',
            11: 'SumSub Approved'
        }

        # Check if the external_status is in the dictionary
        if external_status in dict_:
            kyc.kyc_status = dict_[external_status]  # Map and assign
            kyc.save(update_fields=['kyc_status'])
            logger.error(f"KYC updated for {email} → {kyc.kyc_status}")
