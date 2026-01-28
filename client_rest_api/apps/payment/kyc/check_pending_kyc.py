from django.db import transaction
from apps.users.models import KYCStatus
from apps.core.DBConnection import *


import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')


# import logging
# from datetime import datetime

# logger = logging.getLogger('cron')


def check_pending_kyc():
    logger.error('---------- job working')

    pending_kyc = KYCStatus.objects.filter(kyc_status='pending')
    print(pending_kyc, '------------------')
    for kyc in pending_kyc:
        query = f"""
            SELECT u.email, u.kyc_status
            FROM crmdb.users AS u
            WHERE u.email = '{kyc.email}'
        """

        data = DBConnection._forFetchingJson(query, using='replica')
        if not data:
            continue
        
        external_status = data[0].get('kyc_status')
        email = data[0].get('email')

        if external_status == 4:
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
