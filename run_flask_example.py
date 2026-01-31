# This is an illustrative Flask application showing basic backend logic.
# A real application would be more complex, with a proper database,
# authentication, error handling, and separation of concerns.

from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# --- Mock Database ---
# In a real app, this would be a PostgreSQL database with SQLAlchemy or Django ORM.
MOCK_USERS = {
    1: {"username": "seller_one", "email": "seller@example.com", "balance": 0.0},
    2: {"username": "buyer_one", "email": "buyer@example.com", "balance": 0.0},
}

MOCK_LISTINGS = {
    101: {
        "id": 101,
        "seller_id": 1,
        "platform": "Instagram",
        "handle": "@TravelVibes",
        "follower_count": 150000,
        "price": 1800.00,
        "status": "available",
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat()
    },
    102: {
        "id": 102,
        "seller_id": 1,
        "platform": "YouTube",
        "handle": "TechExplained",
        "follower_count": 55000,
        "price": 2500.00,
        "status": "available",
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat()
    }
}
# --- End Mock Database ---


@app.route("/")
def index():
    return "AccSwap Backend API is running!"

# Endpoint to get all available listings
@app.route("/api/listings", methods=['GET'])
def get_listings():
    """
    Fetches all listings with status 'available'.
    In a real app, you would add filtering by platform, price, etc.
    e.g., platform = request.args.get('platform')
    """
    available_listings = [
        listing for listing in MOCK_LISTINGS.values() if listing['status'] == 'available'
    ]
    return jsonify(available_listings)

# Endpoint to get details for a single listing
@app.route("/api/listings/<int:listing_id>", methods=['GET'])
def get_listing_detail(listing_id):
    listing = MOCK_LISTINGS.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(listing)

# Endpoint to create a new listing
# A real endpoint would require authentication to identify the seller.
@app.route("/api/listings", methods=['POST'])
def create_listing():
    """
    Creates a new listing.
    Requires a JSON body with listing details.
    """
    # For this example, we'll assume seller_id=1 is authenticated
    SELLER_ID = 1
    
    data = request.get_json()
    if not data or not all(k in data for k in ['platform', 'handle', 'price', 'follower_count']):
        return jsonify({"error": "Missing required fields"}), 400

    new_id = max(MOCK_LISTINGS.keys()) + 1
    new_listing = {
        "id": new_id,
        "seller_id": SELLER_ID,
        "platform": data['platform'],
        "handle": data['handle'],
        "follower_count": int(data['follower_count']),
        "price": float(data['price']),
        "status": "available",
        "is_verified": False, # Verification would be a separate process
        "created_at": datetime.utcnow().isoformat()
    }
    MOCK_LISTINGS[new_id] = new_listing
    
    return jsonify(new_listing), 201

# Endpoint to initiate a purchase (starts the escrow process)
@app.route("/api/transactions/initiate/<int:listing_id>", methods=['POST'])
def initiate_purchase(listing_id):
    """
    A buyer initiates the purchase.
    This would change the listing status and create a transaction record.
    """
    # Assume buyer_id=2 is authenticated
    BUYER_ID = 2

    listing = MOCK_LISTINGS.get(listing_id)
    if not listing or listing['status'] != 'available':
        return jsonify({"error": "Listing is not available for purchase"}), 400

    # 1. Update listing status
    listing['status'] = 'in_escrow'

    # 2. In a real app, create a Transaction record in the database.
    print(f"Transaction initiated for listing {listing_id} by buyer {BUYER_ID}.")
    print("Next step: Redirect user to payment gateway (e.g., Stripe).")

    return jsonify({
        "message": "Transaction initiated. Please proceed to payment.",
        "listing": listing
    })


if __name__ == '__main__':
    # Note: In production, use a proper WSGI server like Gunicorn.
    app.run(debug=True, port=5000)
