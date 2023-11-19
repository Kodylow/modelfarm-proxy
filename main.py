from flask import Flask, request, Response, stream_with_context
import requests
from replit_identity_token_manager import ReplitIdentityTokenManager
from waitress import serve
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
token_manager = ReplitIdentityTokenManager()

# Set up basic logging
logging.basicConfig(level=logging.INFO)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["POST"])
def proxy(path):
    logging.info(f"Received {request.method} request for {path}")

    token = token_manager.get_token()

    # Prepare headers, excluding "hop-by-hop" headers
    excluded_headers = [
        "Connection",
        "Keep-Alive",
        "Transfer-Encoding",
        "TE",
        "Trailer",
        "Upgrade",
        "Proxy-Authorization",
        "Host",
    ]
    headers = {
        key: value for key, value in request.headers if key not in excluded_headers
    }
    headers["Authorization"] = f"Bearer {token}"

    url = f"https://production-modelfarm.replit.com/{path}"

    try:
        if "stream" in path:
            # Handle streaming
            req = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                params=request.args,
                allow_redirects=False,
                stream=True,
            )

            def generate():
                for chunk in req.iter_content(chunk_size=4096):
                    if chunk:  # filter out keep-alive new chunks
                        yield chunk

            return Response(
                stream_with_context(generate()),
                content_type=req.headers["Content-Type"],
            )
        else:
            # Handle non-streaming
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                params=request.args,
                allow_redirects=False,
            )

    except Exception as e:
        logging.error(f"Error during forwarding the request: {e}")
        return Response("An error occurred", status=500)

    logging.info(f"Response status: {resp.status_code}")

    # Filter out "hop-by-hop" headers from the response
    headers_to_forward = {
        name: value
        for name, value in resp.headers.items()
        if name not in excluded_headers
    }

    return Response(resp.content, status=resp.status_code, headers=headers_to_forward)


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=80)
