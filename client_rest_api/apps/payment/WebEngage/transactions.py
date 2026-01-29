from django.db import transaction
from django.db.models.functions import TruncDate
from apps.users.models import KYCStatus, LowMarginNotifiedRec
from apps.core.DBConnection import *
from apps.core.WebEngage import *
timestamp = current_webengage_time(offset_hours=-8)
from datetime import datetime, timezone, timedelta
import pandas as pd
import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')

payment_type = {
    1: 'Wire Transfer',
    3: 'Crypto',
    8: 'Crypto',
    17: 'Mobile Money',
    18: 'Bank Transfer',
    19: 'Card',
}

payment_status = {
    0: 'Approved',
    1: 'Declined',
    2: 'Pending',
    4: 'Timeout',
    'default': 'Pending'
}

WD = {
    0: 'Deposit',
    1: 'Withdrawal'
}

def current_webengage_time(dt: datetime, offset_hours=0):
    """
    Converts a datetime object to WebEngage format:
    YYYY-MM-DDTHH:MM:SS±HHMM
    dt: datetime object (naive or timezone-aware)
    offset_hours: timezone offset in hours (default 0 for UTC)
    """
    tz = timezone(timedelta(hours=offset_hours))
    
    # If dt is naive, set tzinfo
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone(tz)
    
    offset = dt.strftime('%z')  # ±HHMM
    return dt.strftime(f'%Y-%m-%dT%H:%M:%S{offset}')

def can_send_low_margin_today(email: str) -> bool:
    """
    Returns True if low margin notification was NOT sent today.
    Uses UTC day boundary.
    """
    today = datetime.now(timezone.utc).date()

    return not LowMarginNotifiedRec.objects.filter(
        email=email,
        notified_at__date=today
    ).exists()

def transaction_event():

    # # ===================== check transactions for Deposit/Withdrawal ------------------
    query = """
        SELECT 
            bb.last_update_time,
            u.email,
            bb.amount,
            bb.type,
            bb.transaction_method,
            bb.is_ftd,
            bb.status
        FROM crmdb.broker_banking AS bb
        LEFT JOIN crmdb.users AS u 
            ON u.id = bb.user_id
        WHERE bb.last_update_time >= NOW() - INTERVAL 5 MINUTE
        ORDER BY bb.last_update_time DESC;
    """

    try:
        data = DBConnection._forFetchingJson(query, using='replica')
    except Exception as e:
        print(f"[ERROR] DB fetch failed: {e}")
        return

    # if not data:
    #     print("[INFO] No transactions found in last 30 minutes")
    #     return

    for transaction in data:
        try:
            email = transaction.get('email')
            amount = int(transaction.get('amount')/100)
            tx_type = transaction.get('type')
            tx_method = transaction.get('transaction_method')
            is_ftd = transaction.get('is_ftd')
            creation_time = transaction.get('last_update_time')
            status = transaction.get('status')
            timestamp = current_webengage_time(creation_time, offset_hours=-8)

            # Skip invalid records
            if not email or not amount:
                print(f"[SKIP] Missing email or amount: {transaction}")
                continue

            method = payment_type.get(tx_type, 'Unknown')

            print(
                f"[PROCESSING] email={email}, amount={amount}, "
                f"method={method}, is_ftd={is_ftd}, type={tx_type}, status={status}"
            )

            # -------------------- Deposits --------------------
            if tx_type == 0:
                # --------------- Deposits -----------------
                if status == 0:
                    if is_ftd:
                        res = first_deposit(
                            user_id=email,
                            amount=amount,
                            currency="USD",
                            method=method,
                            timestamp=timestamp
                        )
                        print("[SUCCESS] first_deposit:", res)
                    
                    res = redeposit(
                            user_id=email,
                            amount=amount,
                            currency="USD",
                            method=method,
                            timestamp=timestamp
                        )
                    print("[SUCCESS] redeposit:", res)
                elif status == 4:
                    res = deposit_failed(
                            user_id=email,
                            amount=amount,
                            currency="USD",
                            method=method,
                            failure_reason='Timeout',
                            timestamp=timestamp
                        )
                    print("[SUCCESS] deposit_failed:", res)
            # elif tx_type == 1:
            #     # --------------- Deposits -----------------
                
        except Exception as e:
            print(f"[ERROR] Failed processing transaction {transaction}: {e}")

    # ===================== check margin level ------------------
    query = f"""
                SELECT bu.email, bu.margin_level_stored, bu.equity, bu.balance FROM crmdb.broker_user AS bu where bu.margin_level_stored <= 100
            """
    try:
        data = DBConnection._forFetchingJson(query, using='replica')
    except Exception as e:
        print(f"[ERROR] DB fetch failed: {e}")
        return
    
    # if not data:
    #     print("[INFO] No transactions found in last 30 minutes")
    #     return
    
    for transaction in data:
        try:
            email = transaction.get('email')
            margin_level_stored = transaction.get('margin_level_stored', 0.0)
            equity = transaction.get('equity')
            balance = transaction.get('balance')/100

            if can_send_low_margin_today(email):
                timestamp = current_webengage_time(
                    datetime.now(timezone.utc),
                    offset_hours=-8
                )

                res = low_margin(
                    user_id=email,
                    account_balance=balance,
                    equity=equity,
                    margin_level=int(margin_level_stored),
                    timestamp=timestamp
                )
                print("[SUCCESS] low_margin:", res)

                # Save notification record
                LowMarginNotifiedRec.objects.create(email=email)
            else:
                print(f"[SKIP] Low margin already sent today for {email}")
        except Exception as e:
            print(f"[ERROR] Failed processing transaction {transaction}: {e}")


    query = f"""
                SELECT bu.last_update_time, bu.email, bu.balance FROM crmdb.broker_user as bu
                WHERE bu.last_update_time >= NOW() - INTERVAL 5 MINUTE
                        ORDER BY bu.last_update_time DESC;
            """
    
    try:
        data = DBConnection._forFetchingJson(query, using='replica')
        data_df = pd.DataFrame(data)
    except Exception as e:
        print(f"[ERROR] DB fetch failed: {e}")
        return
    
    # if not data:
    #     print("[INFO] No transactions found in last 5 minutes")
    #     return
    
    balance_emails = set(data_df['email'])
    for email in balance_emails:
        temp_query = f"""
                            SELECT
                                bu.email,
                                SUM(bu.balance) AS total_balance
                            FROM crmdb.broker_user AS bu
                            WHERE bu.email = '{email}'
                            GROUP BY bu.email;
                        """
        temp_data = DBConnection._forFetchingJson(temp_query, using='replica')
        email = temp_data[0].get('email')
        total_balance = temp_data[0].get('total_balance')
        res = upsert_user(
                user_id=email,
                attributes={
                    'Balance': int(total_balance)/100
                }
            )
        print("[SUCCESS] last_trade:", res, email, int(total_balance))


