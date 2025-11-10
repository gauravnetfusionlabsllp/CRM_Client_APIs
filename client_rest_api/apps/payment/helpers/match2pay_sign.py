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
    """
    Concatenates values in the correct order.
    Handles both DEPOSIT and WITHDRAWAL requests automatically.
    """
    # common fields (order-sensitive)
    ordered_keys = [
        "amount",
        "apiToken",
        "callbackUrl",
    ]

    # withdrawal includes cryptoAddress
    if "cryptoAddress" in d:
        ordered_keys.append("cryptoAddress")

    # then rest of common fields
    ordered_keys += [
        "currency",
        "customer",
        "failureUrl",
        "paymentCurrency",
        "paymentGatewayName",
        "paymentMethod",
        "successUrl",
        "timestamp",
    ]

    # concatenate values in correct order
    concatenated_string = ""
    for k in ordered_keys:
        if k not in d:
            continue
        if k == "customer":
            concatenated_string += format_customer(d[k])
        elif k == "amount":
            concatenated_string += f"{float(d[k]):.6f}".rstrip("0").rstrip(".")
        else:
            concatenated_string += str(d[k])

    return concatenated_string

def generate_signature(request_body, api_secret):
    print("========================================================= 01")
    print(request_body)
    """Generates SHA-384 signature for deposit or withdrawal"""
    formatted_string = concatenate_values(request_body) + api_secret
    print(formatted_string)  # optional debug
    signature = hashlib.sha384(formatted_string.encode("utf-8")).hexdigest()
    print("Generated Signature:", signature)
    return signature
