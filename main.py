from flask import Flask, request, jsonify
import hashlib
import requests
import re

app = Flask(__name__)

@app.route("/pow")
def proof_of_work():
    # Ambil parameter dari query string
    application_id = request.args.get("applicationId")
    hostname = request.args.get("hostname")
    location_id = request.args.get("locationId")

    # Validasi parameter
    if not application_id or not hostname or not location_id:
        return jsonify({"error": "Incomplete query parameters"}), 400

    # Ambil data dari URL hydrate
    hydrate_url = f"https://pci-connect.squareup.com/payments/hydrate?applicationId={application_id}&hostname={hostname}&locationId={location_id}&version=1.71.1"
    try:
        response = requests.get(hydrate_url)
        data = response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Ambil instanceId dan sessionId
    instance_id = data.get("instanceId")
    session_id = data.get("sessionId")
    payment_method_tracking_id = data.get("paymentMethodTrackingId")

    if not instance_id or not session_id:
        return jsonify({"error": "Incomplete data from hydrate response"}), 500

    # Lakukan proof of work
    prefix = "000"
    nonce = 0
    while True:
        combined = f"{application_id}:{nonce}:{application_id},{location_id},{hostname}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        if hashed.startswith(prefix):
            break
        nonce += 1

    # Kembalikan data yang dirapikan
    return jsonify({
        "client_id": application_id,
        "instance_id": instance_id,
        "location_id": location_id,
        "payment_method_tracking_id": payment_method_tracking_id,
        "pow_counter": nonce,
        "session_id": session_id
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
