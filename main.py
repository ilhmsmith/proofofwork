from flask import Flask, request, jsonify
import hashlib
import requests
import re
import uuid
import random
import string
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

@app.route("/pow")
def proof_of_work():
    # Ambil parameter URL jika disediakan
    url = request.args.get("url")

    if url:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        application_id = query_params.get("applicationId", [None])[0]
        hostname = query_params.get("hostname", [None])[0]
        location_id = query_params.get("locationId", [None])[0]
    else:
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

    # Tambahkan padding pada session_id jika perlu
    if session_id and len(session_id) % 4 != 0:
        session_id += "=" * (4 - len(session_id) % 4)

    if not instance_id or not session_id:
        return jsonify({"error": "Incomplete data from hydrate response"}), 500

    # Generate GUID dan 4 fingerprint
    guid = str(uuid.uuid4())
    fingerprints = [
        ''.join(random.choices(string.hexdigits.lower(), k=32)) for _ in range(4)
    ]

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
        "hostname": hostname,
        "instance_id": instance_id,
        "location_id": location_id,
        "pow_counter": nonce,
        "session_id": session_id,
        "guid": guid,
        "fingerprints": fingerprints
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
