from flask import Flask, request, jsonify
import requests
import hashlib
from urllib.parse import urlparse, parse_qs
import os

app = Flask(__name__)

@app.route("/pow", methods=["GET"])
def proof_of_work():
    url = request.args.get("url")

    if url:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        application_id = query.get("applicationId", [None])[0]
        hostname = query.get("hostname", [None])[0]
        location_id = query.get("locationId", [None])[0]
    else:
        application_id = request.args.get("applicationId")
        hostname = request.args.get("hostname")
        location_id = request.args.get("locationId")

    # Validasi parameter
    if not all([application_id, hostname, location_id]):
        return jsonify({"error": "Incomplete query parameters"}), 400

    hydrate_url = (
        f"https://pci-connect.squareup.com/payments/hydrate"
        f"?applicationId={application_id}"
        f"&hostname={hostname}"
        f"&locationId={location_id}"
        f"&version=1.71.1"
    )

    try:
        response = requests.get(hydrate_url, timeout=10)
        data = response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    instance_id = data.get("instanceId")
    session_id = data.get("sessionId")

    # Tambahkan padding ke session_id jika perlu
    if session_id and len(session_id) % 4 != 0:
        session_id += "=" * (4 - len(session_id) % 4)

    if not instance_id or not session_id:
        return jsonify({"error": "Incomplete data from hydrate response"}), 500

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
        "hostname": hostname,
        "location_id": location_id,
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
