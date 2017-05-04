import os
import sys
import traceback
import time
import collections

from flask import Flask, jsonify, request
import logging

from api_handler import api_request
from threaddata import thread_data


app = Flask(__name__)

#----------------------------------------------------------------
# Change setting depending on where deployed
#----------------------------------------------------------------
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
    app.config["DEBUG"] = False
else:
    app.config["DEBUG"] = True




#----------------------------------------------------------------
# The following http routes are taken depending on the url entered
# This is the 'entry' point to all requests from clients
#----------------------------------------------------------------

@app.route('/')
@app.route('/index')
def index():
    #----------------------------------------------------------------
    # Used as default, testing
    #----------------------------------------------------------------
    return "You've arrived at the index"

@app.route('/test')
def test():
    #----------------------------------------------------------------
    # Used for testing connection
    #----------------------------------------------------------------
    return "Success! This message has been sent from the server!"



#----------------------------------------------------------------
# All API traffic through here
#----------------------------------------------------------------
@app.route('/api', methods=["GET", "POST"])
def api_router():


    t0 = time.time()

    thread_data.DB = None
    thread_data.DB_access = 0
    thread_data.DB_access_times = []
    thread_data.DB_access_type = None



    #----------------------------------------------------------------
    # Check JSON is present in request
    #----------------------------------------------------------------
    if request.get_json():

        json = convert(request.get_json())

        #----------------------------------------------------------------
        # Send JSON off to be sorted and retrieve the response whatever
        # it may be
        #----------------------------------------------------------------
        response = api_request(json)

        #----------------------------------------------------------------
        # If send back argument given, put the request back into the
        # response. (for testing obviously)
        #----------------------------------------------------------------
        if "sendback" in json:
            response["a_request"] = json


    else:
        response = {"outcome": "fail",
                    "message": "Json missing from request"}


    


    if request.get_json() and request.get_json()["request_id"]:
        rid = request.get_json()["request_id"]
    else:
        rid = "Not given"


    response["request_id"] = rid
    response["DB_access"] = thread_data.DB_access    
    response["DB_access_times"] =  thread_data.DB_access_times  
    response["DB_access_type"] = thread_data.DB_access_type   
    
    if thread_data.DB is not None:
        if thread_data.DB.open:
            thread_data.DB.close()
        thread_data.DB = None

    response["a_time"] = str(time.time() - t0)[0:7]


    return jsonify(response)



@app.errorhandler(404)
def page_not_found(e):
    logging.exception('An error occurred during a request.')
    return 'Sorry, nothing at this URL.', 404

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500


def uni_to_utf8(json):
    #----------------------------------------------------------------
    # I thought changing all the nested unicode strings to utf-8
    # would solve a bug, it may or may not have but I'm leaving
    # it in just in case it did. It works as is and doesn't slow
    # anything down
    #----------------------------------------------------------------

    for field in json.keys():

        if type(json[field]) == dict:
            json[field] = uni_to_utf8(json[field])

        elif type(json[field]) == unicode:
            json[field] = json[field].encode("utf-8")

    return json



def convert(data):
    #----------------------------------------------------------------
    # Converts nested basestrings to strings
    #----------------------------------------------------------------
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data