from rest_framework import serializers


class PostDataSerializer(serializers.Serializer):
    data = serializers.JSONField(required=True)
    event = serializers.CharField(required=True, allow_blank=False)

class AddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)
    zipCode = serializers.CharField(max_length=20)
    state = serializers.CharField(max_length=100)


class ContactInformationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phoneNumber = serializers.IntegerField()


class CustomerSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    address = AddressSerializer()
    contactInformation = ContactInformationSerializer()
    locale = serializers.CharField(max_length=10)
    dateOfBirth = serializers.CharField(max_length=50)  # change to DateField if it's a real date
    tradingAccountLogin = serializers.CharField(max_length=100)
    tradingAccountUuid = serializers.CharField(max_length=100)


class PaymentRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    customer = CustomerSerializer()
