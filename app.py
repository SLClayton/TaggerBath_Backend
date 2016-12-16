import os
import sys
import traceback

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
    try:
        if request.get_json():

            json = uni_to_utf8(request.get_json())
            response = api_request(json)

        else:
            response = {"request_id": "NA",
                        "outcome": "fail",
                        "message": "Json missing from request"}


    except Exception as e:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        filename = exc_traceback.tb_frame.f_code.co_filename
        lineno = exc_traceback.tb_lineno
        name = exc_traceback.tb_frame.f_code.co_name
        typ = exc_type.__name__
        message2 = exc_value.message
        

        if request.get_json()["request_id"]:
            rid = request.get_json()["request_id"]
        else:
            rid = "Not given"

        response = {"request_id": rid,
                    "outcome": "fail",
                    "message": "{3} in {2} in file {0} at line {1}. {4}. {5}".format(filename,
                                                                                     lineno,
                                                                                     name,
                                                                                     typ,
                                                                                     str(e),
                                                                                     message2),
                    "tb": traceback.extract_stack()}

        


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
    # it in.
    #----------------------------------------------------------------

    for field in json.keys():

        if type(json[field]) == dict:
            json[field] = uni_to_utf8(json[field])

        elif type(json[field]) == unicode:
            json[field] = json[field].encode("utf-8")

    return json