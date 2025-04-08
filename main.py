from flask import Flask, request, jsonify
import hashlib
import requests
from urllib.parse import urlparse, parse_qs
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

def extract_data_from_url(target_url):
    parsed_url = urlparse(target_url)
    query = parse_qs(parsed_url.query)

    application_id = query.get("applicationId", [""])[0]
    hostname = query.get("hostname", [""])[0]
    location_id = query.get("locationId", [""])[0]

    if not application_id or not hostname or not location_id:
        raise ValueError("applicationId, hostname, or locationId not found in URL")

    response = requests.get(target_url)
    if response.status_code != 200:
        raise ValueError("Failed to GET data from target URL")

    json_data = response.json()
    session_id = json_data.get("sessionId", "")
    instance_id = json_data.get("instanceId", "")

    if not session_id or not instance_id:
        raise ValueError("sessionId or instanceId not found in response")

    return {
        "applicationId": application_id,
        "hostname": hostname,
        "locationId": location_id,
        "instanceId": instance_id,
        "sessionId": session_id
    }

@app.route('/proof', methods=['GET'])
def get_proof():
    full_url = request.args.get('url')

    if not full_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        extracted = extract_data_from_url(full_url)

        client_id = extracted["sessionId"]
        params = [extracted["applicationId"], extracted["locationId"], extracted["instanceId"]]

        result = proof_of_work(client_id, "000", params)

        return jsonify({
            "client_id": client_id,
            "params": params,
            "url": full_url,
            "proof_of_work": result,
            "extracted": extracted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
