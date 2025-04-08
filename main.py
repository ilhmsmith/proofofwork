from flask import Flask, request, jsonify
import hashlib
import urllib.parse

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

@app.route('/pow')
def pow_endpoint():
    url = request.args.get('url')
    prefix = request.args.get('prefix', '000')  # default prefix

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # Parse URL hydrate
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)

    application_id = query_params.get("applicationId", [None])[0]
    location_id = query_params.get("locationId", [None])[0]
    hostname = query_params.get("hostname", [None])[0]

    if not all([application_id, location_id, hostname]):
        return jsonify({"error": "Incomplete data"}), 400

    # Use applicationId as client_id
    client_id = application_id
    params = [application_id, location_id, hostname]

    result = proof_of_work(client_id, prefix, params)

    return jsonify({
        "client_id": client_id,
        "params": params,
        "target_prefix": prefix,
        "result": result
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
