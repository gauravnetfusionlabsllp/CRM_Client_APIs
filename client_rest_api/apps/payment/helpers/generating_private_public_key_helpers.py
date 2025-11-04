import textwrap


def to_pem(base64_str, key_type):
    try:
        
        wrapped = "\n".join(textwrap.wrap(base64_str, 64))
        return f"-----BEGIN {key_type}-----\n{wrapped}\n-----END {key_type}-----"

    except Exception as e:
        print(f"Error in the getting to pem: {str(e)}")
        return None
    