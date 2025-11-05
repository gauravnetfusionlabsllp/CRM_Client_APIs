import urllib.parse

def create_whatsapp_link(phone_number: str, message: str) -> str:
    """
    Create a WhatsApp link with a pre-written message.

    :param phone_number: The phone number in international format (e.g., '919876543210').
                         Leave empty ('') if you want the user to choose the contact.
    :param message: The pre-written message you want to include.
    :return: A complete WhatsApp URL.
    """
    encoded_message = urllib.parse.quote(message)

    if phone_number:
        # Link for a specific contact
        url = f"https://wa.me/{phone_number}?text={encoded_message}"
    else:
        # Link that opens WhatsApp contact list with pre-written message
        url = f"https://wa.me/?text={encoded_message}"

    return url


# Example 1: Specific phone number
link_with_number = create_whatsapp_link("919579834493", "I'm interested in your car for sale")
print("Link with number:", link_with_number)

# Example 2: No number (user chooses contact)
link_without_number = create_whatsapp_link("", "I'm inquiring about the apartment listing")
print("Link without number:", link_without_number)
