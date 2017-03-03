import os
import sys
import traceback
import time

from flask import Flask, jsonify, request
import logging


from app_lib.api_handler import api_request


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

    t0 = time.time()

    if request.get_json():

        json = uni_to_utf8(request.get_json())
        response = api_request(json)


    else:
        response = {"outcome": "fail",
                    "message": "Json missing from request"}


    
    if request.get_json() and request.get_json()["request_id"]:
        rid = request.get_json()["request_id"]
    else:
        rid = "Not given"


    response["request_id"] = rid
    response["a_time"] = str(time.time() - t0)           
    

    return jsonify(response)



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



def uni_to_utf8(json):
    #----------------------------------------------------------------
    # I thought changing all the nested unicode strings to utf-8
    # would solve a bug, it may or may not have but I'm leaving
    # it in just in case it did.
    #----------------------------------------------------------------

    for field in json.keys():

        if type(json[field]) == dict:
            json[field] = uni_to_utf8(json[field])

        elif type(json[field]) == unicode:
            json[field] = json[field].encode("utf-8")

    return json
