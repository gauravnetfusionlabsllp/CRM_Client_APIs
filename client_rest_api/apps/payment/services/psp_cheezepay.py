import requests

class CheezePayPSP:
    BASE_URL = "url"

    def payout(self, approval):
        print("CheezePayPSP: called")
        # payload = {
        #     "amount": approval.amount,
        #     "currency": approval.currency,
        #     "walletAddress": approval.walletAddress,
        #     "referenceId": approval.id,
        # }

        # headers = {
        #     "Authorization": "Bearer BINANCE_API_KEY"
        # }

        # r = requests.post(self.BASE_URL, json=payload, headers=headers)
        # return r.json()
