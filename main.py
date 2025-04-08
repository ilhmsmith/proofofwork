import hashlib
import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)

def compute_hash(input_str):
    return hashlib.sha256(input_str.encode()).hexdigest()

def proof_of_work(client_id, target_prefix, params):
    n = 0
    while True:
        combined = f"{client_id}:{n}:{','.join(params)}"
        hash_result = compute_hash(combined)
        if hash_result.startswith(target_prefix):
            return n, combined, hash_result
        n += 1

@app.route("/pow")
def pow_endpoint():
    url = request.args.get("url")
    target_prefix = request.args.get("prefix", "000")

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    # Decode and parse URL
    decoded_url = unquote(url)
    parsed_url = urlparse(decoded_url)
    query_params = parse_qs(parsed_url.query)

    application_id = query_params.get("applicationId", [None])[0]
    hostname = query_params.get("hostname", [None])[0]
    location_id = query_params.get("locationId", [None])[0]

    if not all([application_id, hostname, location_id]):
        return jsonify({"error": "Incomplete data"}), 400

    try:
        response = requests.get(decoded_url)
        hydrate_data = response.json()

        instance_id = hydrate_data.get("instanceId")
        session_id = hydrate_data.get("sessionId")

        if not instance_id or not session_id:
            return jsonify({"error": "Missing instanceId or sessionId"}), 400

        params = [application_id, location_id, hostname, instance_id, session_id]
        nonce, combined, hash_result = proof_of_work(application_id, target_prefix, params)

        return jsonify({
            "client_id": application_id,
            "hostname": hostname,
            "location_id": location_id,
            "instance_id": instance_id,
            "session_id": session_id,
            "params": params,
            "result": {
                "combined": combined,
                "hash": hash_result,
                "nonce": nonce
            },
            "target_prefix": target_prefix
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
