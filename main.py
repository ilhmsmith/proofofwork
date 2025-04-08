from flask import Flask, request, jsonify
import requests
import hashlib

app = Flask(__name__)

@app.route("/pow", methods=["GET"])
def proof_of_work():
    application_id = request.args.get("applicationId")
    hostname = request.args.get("hostname")
    location_id = request.args.get("locationId")

    if not all([application_id, hostname, location_id]):
        return jsonify({"error": "Incomplete query parameters"}), 400

    hydrate_url = f"https://pci-connect.squareup.com/payments/hydrate?applicationId={application_id}&hostname={hostname}&locationId={location_id}&version=1.71.1"

    try:
        response = requests.get(hydrate_url, timeout=10)
        data = response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    instance_id = data.get("instanceId")
    session_id = data.get("sessionId")

    combined = f"{application_id},{location_id},{hostname}"
    nonce = 0
    target_prefix = "000"
    while True:
        test = f"{application_id}:{nonce}:{combined}"
        hash_hex = hashlib.sha256(test.encode()).hexdigest()
        if hash_hex.startswith(target_prefix):
            break
        nonce += 1

    return jsonify({
        "client_id": application_id,
        "params": [application_id, location_id, hostname],
        "instance_id": instance_id,
        "session_id": session_id,
        "result": {
            "combined": test,
            "hash": hash_hex,
            "nonce": nonce
        },
        "target_prefix": target_prefix
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
