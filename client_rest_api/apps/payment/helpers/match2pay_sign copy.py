import json
import hashlib

def format_nested_dict(d, ordered_keys):
    """Formats a nested dictionary into a structured string"""
    formatted_items = []
    for key in ordered_keys:
        if key in d:
            formatted_items.append(
                f"{key}={format_nested_dict(d[key], ordered_keys) if isinstance(d[key], dict) else d[key]}"
            )
    return "{" + ", ".join(formatted_items) + "}"

def format_customer(d):
    """Formats the customer dictionary"""
    ordered_keys = [
        "firstName",
        "lastName",
        "address",
        "contactInformation",
        "locale",
        "dateOfBirth",
        "tradingAccountLogin",
        "tradingAccountUuid",
    ]
    address_keys = ["address", "city", "country", "zipCode", "state"]
    contact_keys = ["email", "phoneNumber"]
    return (
        "{"
        + ", ".join(
            [
                f"firstName={d['firstName']}",
                f"lastName={d['lastName']}",
                f"address={format_nested_dict(d['address'], address_keys)}",
                f"contactInformation={format_nested_dict(d['contactInformation'], contact_keys)}",
                f"locale={d['locale']}",
                f"dateOfBirth={d['dateOfBirth']}",
                f"tradingAccountLogin={d['tradingAccountLogin']}",
                f"tradingAccountUuid={d['tradingAccountUuid']}",
            ]
        )
        + "}"
    )

def concatenate_values(d):
    """Concatenates values from the dictionary."""
    ordered_keys = [
        "amount",
        "apiToken",
        "callbackUrl",
        "currency",
        "customer",
        "failureUrl",
        "paymentCurrency",
        "paymentGatewayName",
        "paymentMethod",
        "successUrl",
        "timestamp",
    ]
    concatenated_string = "".join(
        format_customer(d[k])
        if k == "customer"
        else f"{d[k]:f}".rstrip('0').rstrip('.') if k == "amount"
        else str(d[k])
        for k in ordered_keys
    )
    return concatenated_string

def generate_signature(request_body, api_secret):
    """Generates SHA-384 signature based on sorted keys and formatted concatenated values."""
    formatted_string = concatenate_values(request_body)
    formatted_string += api_secret
    print(formatted_string)
    signature = hashlib.sha384(formatted_string.encode("utf-8")).hexdigest()
    return signature

request_body = {
    "amount": 10,
    "apiToken": "Bg6AcUwDopx2-9tsKeri99CtupYQs8CQFnQea4oceOdQlFYEkpyIq209",
    "callbackUrl": "http://test/deposit/callback",
    "currency": "USD",
    "customer": {
        "firstName": "firstName_4da0af01617c",
        "lastName": "lastName_801eb285edd1",
        "address": {
            "address": "address_52c10ed842fb",
            "city": "city_62da6faaeb17",
            "country": "country_a6be7ed127cc",
            "zipCode": "zipCode_3e168862ef49",
            "state": "state_b8d531055c90",
        },
        "contactInformation": {
            "email": "email_e4ac63093536",
            "phoneNumber": "phoneNumber_8fcb0237f7ee",
        },
        "locale": "en_US",
        "dateOfBirth": "dateOfBirth_338c08d95dd6",
        "tradingAccountLogin": "clientId_d6811bff2963",
        "tradingAccountUuid": "clientUid_56b798ba2ae2",
    },
    "failureUrl": "http://test/failed-payment",
    "paymentCurrency": "USX",
    "paymentGatewayName": "USDT TRC20",
    "paymentMethod": "CRYPTO_AGENT",
    "successUrl": "http://test/thanku",
    "timestamp": "1764149779000"
}

api_secret = "ApiSecretProvidedBySupport"

signature = generate_signature(request_body, api_secret)
print("Generated Signature:", signature)
