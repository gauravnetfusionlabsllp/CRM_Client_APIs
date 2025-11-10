import requests
import json
from generate_sign import generate_signature  # same as used for deposit

# Your API secret (keep this safe)
api_secret = "Bg6AcUwDopx2-9tsKeri99CtupYQs8CQFnQea4oceOdQlFYEkpyIq209"

# Withdrawal request body
request_body = {
    "amount": 10,
    "apiToken": "Jsac1nwWT9Tnze4TIpXozFukqWwAm68XBcAQN0jbY7SAwah96OYCSW3f",
    "callbackUrl": "http://test/withdrawal/callback",
    "cryptoAddress": "TXYZ1234567890ABCDEFG",  # 🔹 Replace with actual USDT TRC20 wallet address
    "currency": "USD",
    "customer": {
        "firstName": "John",
        "lastName": "Doe",
        "address": {
            "address": "123 Test Street",
            "city": "Testville",
            "country": "US",
            "zipCode": "12345",
            "state": "CA"
        },
        "contactInformation": {
            "email": "john.doe@example.com",
            "phoneNumber": "+15551234567"
        },
        "locale": "en_US",
        "dateOfBirth": "1990-01-01",
        "tradingAccountLogin": "clientId_12345",
        "tradingAccountUuid": "clientUid_67890"
    },
    "failureUrl": "http://test/withdrawal/failed",
    "paymentCurrency": "USX",
    "paymentGatewayName": "USDT TRC20",
    "paymentMethod": "CRYPTO_AGENT",
    "successUrl": "http://test/withdrawal/success",
    "timestamp": "1764149779000"  # should be a current or future timestamp
}

# ✅ Generate signature using your helper function
request_body["signature"] = generate_signature(request_body, api_secret)

# Prepare headers
headers = {
    "Content-Type": "application/json"
}

# ✅ Send POST request
response = requests.post(
    "https://wallet-staging.match2pay.com/api/v2/payment/withdrawal",
    headers=headers,
    data=json.dumps(request_body)
)

# ✅ Print response
print(response.status_code)
print(response.text)
