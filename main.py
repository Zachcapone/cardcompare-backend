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

# Store access tokens in memory for this demo
user_access_tokens = {}

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
    public_token = data["public_token"]
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response.to_dict()["access_token"]
    user_access_tokens["user-id"] = access_token
    return jsonify({"access_token_stored": True})

@app.route("/spend_summary", methods=["GET"])
def spend_summary():
    access_token = user_access_tokens.get("user-id")
    if not access_token:
        return jsonify({"error": "No access token available"}), 400

    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    request_data = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=250)
    )
    response = client.transactions_get(request_data)
    transactions = response.to_dict()["transactions"]  # ✅ fixed line

    category_totals = {
        "Dining": 0,
        "Groceries": 0,
        "Flights": 0,
        "Hotels": 0
    }

    for txn in transactions:
        category = txn.get("category", [])
        amount = txn["amount"]
        name = (category[0] if category else "").lower()

        if "restaurant" in name or "dining" in name:
            category_totals["Dining"] += amount
        elif "grocery" in name:
            category_totals["Groceries"] += amount
        elif "travel" in name or "airlines" in name:
            category_totals["Flights"] += amount
        elif "hotel" in name:
            category_totals["Hotels"] += amount

    return jsonify(category_totals)

# ✅ Required for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
