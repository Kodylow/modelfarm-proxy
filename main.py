from flask import Flask, request
import requests
from replit_identity_token_manager import ReplitIdentityTokenManager
from waitress import serve

app = Flask(__name__)
token_manager = ReplitIdentityTokenManager()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    # Get the token
    token = token_manager.get_token()

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
    }

    # Forward the request to the production server
    if request.method == "GET":
        resp = requests.get(
            f"https://production-modelfarm.replit.com/{path}",
            headers=headers,
            params=request.args,
        )
    elif request.method == "POST":
        resp = requests.post(
            f"https://production-modelfarm.replit.com/{path}",
            headers=headers,
            json=request.json,
        )
    elif request.method == "PUT":
        resp = requests.put(
            f"https://production-modelfarm.replit.com/{path}",
            headers=headers,
            json=request.json,
        )
    elif request.method == "DELETE":
        resp = requests.delete(
            f"https://production-modelfarm.replit.com/{path}", headers=headers
        )

    # Return the response
    return (resp.content, resp.status_code, resp.headers.items())


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
