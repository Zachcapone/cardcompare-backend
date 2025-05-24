@app.route("/spend_summary", methods=["GET"])
def spend_summary():
    access_token = user_access_tokens.get("user-id")
    if not access_token:
        return jsonify({"error": "No access token available"}), 400

    try:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        request_data = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(count=250)
        )
        response = client.transactions_get(request_data)
        transactions = response.to_dict()["transactions"]  # ✅ Fixed here

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

    except Exception as e:
        print(f"🔥 spend_summary error: {str(e)}")
        return jsonify({"error": "Internal error", "details": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
