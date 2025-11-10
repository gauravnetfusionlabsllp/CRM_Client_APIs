from .psp_match2pay import Match2PayPSP
from .psp_cheezepay import CheezePayPSP

class PSPRouter:
    @staticmethod
    def get_psp(psp_name):
        psp_name = psp_name.lower()

        if psp_name == "match2pay":
            return Match2PayPSP()
        if psp_name == "cheezepay":
            return CheezePayPSP()

        raise Exception(f"Unsupported PSP: {psp_name}")
