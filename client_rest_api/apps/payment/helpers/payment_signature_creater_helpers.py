
import hashlib
import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature


def jena_pay_generate_signature(order, password):
    try:
        raw_string = f"{order['number']}{order['amount']}{order['currency']}{order['description']}{password}"
        
        to_md5_upper = raw_string.upper()

        md5_hash = hashlib.md5(to_md5_upper.encode("utf-8")).hexdigest()
   
        sha1_hash = hashlib.sha1(md5_hash.encode("utf-8")).hexdigest()

        return sha1_hash
    
    except Exception as e:
        print(f"Error in the generate_signature:{str(e)}")
        return None
    

def get_content(params):
    try:
        
        param_name_list = sorted(params.keys())
        result_parts = []

        for name in param_name_list:
            value = params[name]

            if value is not None:
                if name.lower() == 'data':
                    json_string = json.dumps(value, separators=(',', ':'))
                    result_parts.append(f"{name}={json_string}")
                
                else:
                    result_parts.append(f"{name}={value}")

        return "&".join(result_parts)

    except Exception as e:
        print(f"Error in creation the Content: {str(e)}")
        return None
    

def get_sign(params, private_key_pem):
    try:
        message = get_content(params)

        private_key = load_pem_private_key(
            private_key_pem.encode(),
            password = None,
        )

        signature = private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()

    except Exception as e:
        print(f"Signature failed:: {str(e)}")
        return None
    

def verify_sign(response_body, public_key_pem):
   
    try:
        signature = response_body.pop('sign', None)
        
        if not signature:
            raise ValueError("No 'sign' field in response_body")

        signature_bytes = base64.b64decode(signature)

        data_to_verify = get_content(response_body)

        public_key = load_pem_public_key(public_key_pem.encode())

        public_key.verify(
            signature_bytes,
            data_to_verify.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    
    except InvalidSignature:
        return False
    
    except Exception as e:
        print(f"Signature failed: {e}")
        return 
    
