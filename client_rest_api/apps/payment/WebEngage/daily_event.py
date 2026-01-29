from django.db import transaction
from django.db.models.functions import TruncDate
from apps.users.models import KYCStatus, LowMarginNotifiedRec
from apps.core.DBConnection import *
from apps.core.WebEngage import *
timestamp = current_webengage_time(offset_hours=-8)
from datetime import datetime, timezone, timedelta
import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')

def _to_iso(dt):
    """
    Convert a datetime object to ISO 8601 string compatible with WebEngage
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return dt  # assume string

def trade_login():
    query = f"""
                SELECT
                    uldr.user_agent,
                    uldr.ip,
                    u.email,
                    uldr.last_seen
                FROM crmdb.user_login_device_rel AS uldr
                JOIN crmdb.users AS u
                    ON u.id = uldr.user_id
                WHERE uldr.last_seen >= CURDATE() - INTERVAL 1 DAY
                AND uldr.last_seen < CURDATE()
                ORDER BY uldr.last_seen DESC;
            """
    try:
        data = DBConnection._forFetchingJson(query, using='replica')
    except Exception as e:
        print(f"[ERROR] DB fetch failed: {e}")
        return
    if not data:
        print("[INFO] No transactions found in last 1 day")
        return

    for transaction in data:
        try:
            email = transaction.get('email')
            login_device = transaction.get('user_agent')
            ip_address = transaction.get('ip_address')
            last_seen = transaction.get('timestamp')

            res = last_login(
                            user_id=email,
                            login_device=login_device,
                            ip_address=ip_address,
                            timestamp=last_seen
                        )
            logger.error(f"[SUCCESS] last_login: {res}", exc_info=True)
                
        except Exception as e:
            print(f"[ERROR] Failed processing transaction {transaction}: {e}")
    
    query = f"""
                SELECT u.email , u.last_trade_opened_time FROM crmdb.users AS u
                WHERE u.last_trade_opened_time >= CURDATE() - INTERVAL 1 DAY
                AND u.last_trade_opened_time < CURDATE()
                ORDER BY u.last_trade_opened_time DESC;
            """
    
    try:
        data = DBConnection._forFetchingJson(query, using='replica')
    except Exception as e:
        print(f"[ERROR] DB fetch failed: {e}")
        return
    if not data:
        print("[INFO] No transactions found in last 1 day")
        return

    for transaction in data:
        try:
            email = transaction.get('email')
            last_trade_opened_time = transaction.get('last_trade_opened_time')

            res = upsert_user(
                user_id=email,
                attributes={
                    'last_trade_time': _to_iso(last_trade_opened_time)
                }
            )
            logger.error(f"[SUCCESS] last_trade: {res}", exc_info=True)
                
        except Exception as e:
            print(f"[ERROR] Failed processing transaction {transaction}: {e}")
    