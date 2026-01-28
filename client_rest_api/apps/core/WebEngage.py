import requests
from requests.exceptions import RequestException
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
load_dotenv()


# -------------------- Configuration --------------------
WBHOST = os.environ['WBHOST']
WBLICENSE_CODE = os.environ['WBLICENSE_CODE']
WBAPI_KEY = os.environ['WBAPI_KEY']

HEADERS = {
    "Authorization": f"Bearer {WBAPI_KEY}",
    "Content-Type": "application/json",
}


def current_webengage_time(offset_hours=0):
    """
    Returns current datetime in WebEngage format:
    YYYY-MM-DDTHH:MM:SS±HHMM
    offset_hours: timezone offset in hours (default 0 for UTC)
    """
    tz = timezone(timedelta(hours=offset_hours))
    now = datetime.now(tz)
    # Format ±HHMM
    offset = now.strftime('%z')
    # Combine date, time and offset
    return now.strftime(f'%Y-%m-%dT%H:%M:%S{offset}')

timestamp = current_webengage_time(offset_hours=-8)

# -------------------- Helper Functions --------------------
def _to_iso(dt):
    """
    Convert a datetime object to ISO 8601 string compatible with WebEngage
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return dt  # assume string

def _post_request(url, payload):
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print("ERROR: ", str(e))
        return {"success": False, "error": str(e), "response": getattr(e.response, "text", None)}

def track_event(user_id, event_name, event_time=None, event_data=None):
    url = f"{WBHOST}/v1/accounts/{WBLICENSE_CODE}/events"
    payload = {"userId": user_id, "eventName": event_name}
    if event_time: payload["eventTime"] = event_time
    if event_data: payload["eventData"] = event_data
    print('-------------- 01')
    return _post_request(url, payload)

# -------------------- User Upsert --------------------
def upsert_user(user_id, first_name=None, last_name=None, birth_date=None,
                gender=None, email=None, phone=None, company=None, attributes=None, location=None):
    """
    Create or update a user in WebEngage
    """
    url = f"{WBHOST}/v1/accounts/{WBLICENSE_CODE}/users"

    payload = {"userId": user_id}
    if first_name:
        payload["firstName"] = first_name
    if last_name:
        payload["lastName"] = last_name
    if birth_date:
        payload["birthDate"] = _to_iso(birth_date)  # ensures ISO format
    if gender:
        payload["gender"] = gender
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if company:
        payload["company"] = company
    if attributes:
        payload["attributes"] = attributes
    # if attributes.get('Country', ''):
    #     payload["country"] = attributes.get('Country', '')
    if location:
        payload.update(location)
        
    

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "response": getattr(e.response, "text", None),
        }


# -------------------- Registration Events --------------------
def registration_completed(user_id, source, timestamp):
    return track_event(user_id, "registration_completed", timestamp,
                       {"userId": user_id, "source": source, "eventTime": timestamp})

def registration_failed(user_id, failure_reason, timestamp):
    return track_event(user_id, "registration_failed", timestamp,
                       {"failure_reason": failure_reason, "eventTime": timestamp})

# -------------------- KYC Events --------------------
def kyc_started(user_id, source, timestamp):
    return track_event(user_id, "kyc_started", timestamp,
                       {"source": source, "eventTime": timestamp})

def kyc_approved(user_id, approved_at, timestamp):
    return track_event(user_id, "kyc_approved", timestamp,
                       {"approved_at": approved_at, "eventTime": timestamp})

def kyc_rejected(user_id, rejection_reason, timestamp):
    return track_event(user_id, "kyc_rejected", timestamp,
                       {"rejection_reason": rejection_reason, "eventTime": timestamp})

# -------------------- Deposit Events --------------------
def first_deposit(user_id, amount, currency, method, timestamp):
    return track_event(user_id, "first_deposit", timestamp,
                       {"amount": amount, "currency": currency, "method": method, "eventTime": timestamp})

def deposit_failed(user_id, amount, currency, method, failure_reason, timestamp):
    return track_event(user_id, "deposit_failed", timestamp,
                       {"amount": amount, "currency": currency, "method": method, "failure_reason": failure_reason, "eventTime": timestamp})

def redeposit(user_id, amount, currency, method, timestamp):
    return track_event(user_id, "redeposit", timestamp,
                       {"amount": amount, "currency": currency, "method": method, "eventTime": timestamp})

# -------------------- Transfer Events --------------------
def funds_transfer(user_id, from_account, to_account, amount, timestamp):
    return track_event(user_id, "funds_transfer", timestamp,
                       {"from_account": from_account, "to_account": to_account, "amount": amount, "eventTime": timestamp})

# -------------------- Risk Events --------------------
def low_margin(user_id, account_balance, equity, margin_level, timestamp):
    return track_event(user_id, "low_margin", timestamp,
                       {"account_balance": account_balance, "equity": equity, "marginLevel": margin_level, "eventTime": timestamp})

# -------------------- Withdrawal Events --------------------
def withdrawal_request(user_id, amount, currency, method, timestamp):
    return track_event(user_id, "withdrawal_request", timestamp,
                       {"amount": amount, "currency": currency, "method": method, "eventTime": timestamp})

def withdrawal_approved(user_id, amount, currency, method, approved_at, timestamp):
    return track_event(user_id, "withdrawal_approved", timestamp,
                       {"amount": amount, "currency": currency, "method": method, "approved_at": approved_at, "eventTime": timestamp})

def withdrawal_failed(user_id, amount, method, failure_reason, timestamp):
    return track_event(user_id, "withdrawal_failed", timestamp,
                       {"amount": amount, "method": method, "failure_reason": failure_reason, "eventTime": timestamp})

# -------------------- Trading Events --------------------
def last_trade(user_id, instrument, volume, pnl, timestamp):
    return track_event(user_id, "last_trade", timestamp,
                       {"instrument": instrument, "volume": volume, "pnl": pnl, "eventTime": timestamp})

# -------------------- Login Events --------------------
def last_login(user_id, login_device, ip_address, timestamp):
    return track_event(user_id, "last_login", timestamp,
                       {"login_device": login_device, "ip_address": ip_address, "eventTime": timestamp})
