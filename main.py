from flask import Flask, request, jsonify
import hashlib
import requests
import os

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

@app.route("/pow", methods=["GET"])
def auto_pow():
    hydrate_url = request.args.get('url')
    if not hydrate_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        response = requests.get(hydrate_url)
        data = response.json()

        sessionId = data.get("sessionId")
        instanceId = data.get("instanceId")
        
        # Extract query params
        parsed = requests.utils.urlparse(hydrate_url)
        query_params = dict(requests.utils.parse_qsl(parsed.query))
        client_id = query_params.get("applicationId")
        location_id = query_params.get("locationId")

        if not all([sessionId, instanceId, client_id, location_id]):
            return jsonify({"error": "Incomplete data"}), 400

        target_prefix = "000"
        params = [client_id, location_id, instanceId]
        result = proof_of_work(sessionId, target_prefix, params)

        return jsonify({
            "sessionId": sessionId,
            "instanceId": instanceId,
            "client_id": client_id,
            "location_id": location_id,
            "target_prefix": target_prefix,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
