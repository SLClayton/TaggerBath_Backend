from flask import Flask, jsonify, request
import logging

import app_lib.api_handler

app = Flask(__name__)
app.config["DEBUG"] = True




@app.route('/')
@app.route('/index')
def index():
    return "You've arrived at the index"

@app.route('/test')
def test():
    return "Success! This message has been sent from the server!"



@app.route('/api', methods=["GET", "POST"])
def api_router():
    if not request.get_json():
        response = {"request_id": "NA",
                    "outcome": "fail",
                    "message": "Json missing from request"}

        return jsonify(response)

    return jsonify(api_handler.api(request.get_json()))




@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    logging.exception('An error occurred during a request.')
    return 'Sorry, nothing at this URL.', 404

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500