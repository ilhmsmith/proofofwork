from flask import Flask, request, jsonify
import hashlib
import requests
from urllib.parse import urlparse, parse_qsl

app = Flask(__name__)

def compute_hash(input_str):
    return hashlib.sha256(input_str.encode()).hexdigest()

def proof_of_work(client_id, target_prefix, params):
    n = 0
    while True:
        combined = f"{client_id}:{n}:{','.join(params)}"
        hash_result = compute_hash(combined)
        if hash_result.startswith(target_prefix):
            return {
                "nonce": n,
                "hash": hash_result,
                "combined": combined
            }
        n += 1

@app.route("/pow")
def pow():
    hydrate_url = request.args.get("url")
    target_prefix = request.args.get("prefix", "000")

    if not hydrate_url:
        return jsonify({"error": "Missing hydrate url"}), 400

    try:
        # Ambil parameter dari URL
        parsed = urlparse(hydrate_url)
        query_params = dict(parse_qsl(parsed.query))

        client_id = query_params.get("applicationId")
        location_id = query_params.get("locationId")
        hostname = query_params.get("hostname")

        # Fetch dari hydrate URL
        response = requests.get(hydrate_url)
        data = response.json()

        sessionId = data.get("sessionId")
        instanceId = data.get("instanceId")

        if not all([sessionId, instanceId, client_id, location_id, hostname]):
            return jsonify({"error": "Incomplete data"}), 400

        params = [client_id, location_id, instanceId]
        result = proof_of_work(sessionId, target_prefix, params)

        return jsonify({
            "sessionId": sessionId,
            "instanceId": instanceId,
            "client_id": client_id,
            "location_id": location_id,
            "hostname": hostname,
            "target_prefix": target_prefix,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
