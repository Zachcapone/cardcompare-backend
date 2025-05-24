
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
import plaid
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
CORS(app)

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': os.getenv("PLAID_CLIENT_ID"),
        'secret': os.getenv("PLAID_SECRET"),
    }
)
client = plaid_api.PlaidApi(plaid.ApiClient(configuration))

@app.route("/create_link_token", methods=["POST"])
def create_link_token():
    request_data = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="CardCompare",
        country_codes=[CountryCode("US")],
        language="en",
        user={"client_user_id": "user-id"}
    )
    response = client.link_token_create(request_data)
    return jsonify(response.to_dict())

@app.route("/exchange_token", methods=["POST"])
def exchange_token():
    data = request.get_json()
    exchange_request = ItemPublicTokenExchangeRequest(public_token=data["public_token"])
    exchange_response = client.item_public_token_exchange(exchange_request)
    return jsonify(exchange_response.to_dict())

@app.route("/transactions", methods=["POST"])
def get_transactions():
    data = request.get_json()
    access_token = data["access_token"]
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    request_data = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=250)
    )
    response = client.transactions_get(request_data)
    return jsonify(response.to_dict())

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

