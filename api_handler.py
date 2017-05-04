import logging
import os
import sys
import copy
import time

from operator import itemgetter

import grid
from facebook import *
from user import *
from json_checker import find_error_fields, need_verification, templates
from db_manager import getCloudSQL

LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LNG_SCALE = float(os.environ.get("LNG_SCALE"))
MAX_STACK = int(os.environ.get("MAX_STACK"))
TEAMS = os.environ.get("TEAMS").split(",")
CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
USER_TABLE = os.environ.get("USER_TABLE")
GRID_TABLE = os.environ.get("GRID_TABLE")




def api_request(request):



    #----------------------------------------------------------------
    # Check request JSON has no missing fields, correct types etc
    #----------------------------------------------------------------
    errors = find_error_fields(request, "request")
    if errors != []:
        return incomplete_json_request(request, errors)


    if request["request_type"] not in templates:
        return invalid_request(request)


    #----------------------------------------------------------------
    # create_user needs fb login, but not an active account. Special
    # case
    #----------------------------------------------------------------
    if request["request_type"] == "create_user":

        if verify_token_with_facebook(request["fb_id"], request["userAccessToken"]):
            return create_user(request)

        else:
            return invalidAccessToken(request)

    #----------------------------------------------------------------
    # If request doesn't need a user, go straight there
    #----------------------------------------------------------------
    elif request["request_type"] == "get_grid":
        return get_grid(request)

    elif request["request_type"] == "get_grid_square":
        return get_grid_square(request)

    elif request["request_type"] == "get_leaderboard_spm":
        return get_leaderboard_spm(request)

    elif request["request_type"] == "get_leaderboard_score":
        return get_leaderboard_score(request)

    elif request["request_type"] == "get_leaderboard_team_spm":
        return get_leaderboard_team_spm(request)

    elif request["request_type"] == "get_leaderboard_team_score":
        return get_leaderboard_team_score(request)

    elif request["request_type"] == "get_scale":
        return get_scale()



    #----------------------------------------------------------------
    # Get user and check access token is correct
    #----------------------------------------------------------------
    [verified_token, user] = verify_and_get_user(request["fb_id"], request["userAccessToken"])

    if not verified_token:
        return invalidAccessToken(request)
    elif user == None:
        return invalid_user()


    #----------------------------------------------------------------
    # Route remaining requests and user to functions
    #----------------------------------------------------------------
    if request["request_type"] == "new_position":
        return new_position(request, user)

    elif request["request_type"] == "get_user_info":
        return get_user_info(request, user)

    
    return invalid_request(request)



def get_scale():
    #----------------------------------------------------------------
    # Return scale of squares within the grid
    #----------------------------------------------------------------
    response = {"outcome": "success",
                "message": "Scale gotten",
                "lat_scale": LAT_SCALE,
                "lng_scale": LNG_SCALE}

    return response


def new_position(request, user):



    #----------------------------------------------------------------
    # Unpacks some useful arguments
    #----------------------------------------------------------------
    nw_lat = request["nw_lat"]
    nw_lng = request["nw_lng"]


    #----------------------------------------------------------------
    # Checking user is in area and gets specific square
    #----------------------------------------------------------------
    square = grid.getGridSquare(nw_lat, nw_lng)

    

    if square == None:
        response = {"outcome": "fail",
                    "message": "Could not find square for ({0}, {1}), may be outside bounds".format(str(nw_lat), str(nw_lng))}
        return response
    

    old_stack = square.get_stack_string()
    old_team = square.team
    old_level = square.level


    if square.item is not None:
        user.add_item(square.item)

        user.update()

    #----------------------------------------------------------------
    # Add user to end of list and update in db
    #----------------------------------------------------------------
    square.add_user(user)

    square.update()

        
    response = {"outcome": "success",
                "message": "Updated square id({0}) from team {1}|{2} to {3}|{4} with user {5}.".format(square._id,
                                                                                                      old_team,
                                                                                                      old_level,
                                                                                                      square.team,
                                                                                                      square.level,
                                                                                                      user.name,
                                                                                                      square.stack),
                "nw_lat": square.nw_lat,
                "nw_lng": square.nw_lng,
                "team": square.team,
                "level": square.level,
                "stack_old": old_stack,
                "stack_new": square.get_stack_string()
                }


    return response


def get_grid(request):
    #----------------------------------------------------------------
    # Extract bounds and return list of squares from grid
    #----------------------------------------------------------------

    nw_lat = request["nw_lat"]
    nw_lng = request["nw_lng"]
    se_lat = request["se_lat"]
    se_lng = request["se_lng"]

    try:
        g = grid.getGrid(nw_lat, nw_lng, se_lat, se_lng)

        response = {"outcome": "success",
                    "grid": g,
                    "length": len(g),
                    "message": "Grid successfully gotten."}

    except Exception as e:
        response = {"outcome": "fail",
                    "message": "Failed to get grid. " + str(e)}

    return response


def get_grid_square(request):

    #----------------------------------------------------------------
    # Return data for a particular square
    # I don't think this is ever used, just in case one day
    #----------------------------------------------------------------

    nw_lat = request["nw_lat"]
    nw_lng = request["nw_lng"]

    square = grid.getSpecificGridSquare(nw_lat, nw_lng)

    if square == None:
        response = {"outcome": "fail",
                    "message": "Unable to find gridsquare ({0}, {1})".format(nw_lat, nw_lng)}

        return response


    stack = []

    for user in square.stack:
        stack.append({"name": user.name,
                      "team": user.team})


    response = {"outcome": "success",
                "message": "Got square info successfully",

                "nw_lat": square.nw_lat,
                "nw_lng": square.nw_lng,
                "team": square.team,
                "level": square.level,
                "stack": stack
                }

    return response



def get_user_info(request, user):

    #----------------------------------------------------------------
    # Returns the info of the user requesting
    #----------------------------------------------------------------

    response = {"outcome": "success",
                "message": "Successfully gotten user info for '{0}'".format(user.name),
                "name": user.name,
                "team": user.team,
                "email": user.email,
                "fb_id": user.fb_id,
                "items": user.get_items(),
                "spm" : user.spm
                }
        
    return response


def create_user(request):


    name = request["name"]
    email = request["email"]
    team = least_populous_team()
    fb_id = request["fb_id"]

    #----------------------------------------------------------------
    # Check name is valid (char check)
    #----------------------------------------------------------------
    if not is_username_valid(name):
        response = {"outcome": "fail",
                    "error_code": 3,
                    "message": "Username '{0}' not allowed".format(name)}


    #----------------------------------------------------------------
    # Check whether or not username is taken
    #----------------------------------------------------------------
    elif is_username_taken(name):
        response = {"outcome": "fail",
                    "error_code": 1,
                    "message": "Username '{0}' taken".format(name)}

    else:

        try:
            #----------------------------------------------------------------
            # Checks are done, try and create user
            #----------------------------------------------------------------
            createUser(name, team, email, fb_id)

            user = getUser("fb_id", fb_id)

            response = {"outcome": "success",
                        "message": "Created user {0}".format(user.name),
                        "team": user.team}


        except Exception as e:
            #----------------------------------------------------------------
            # Something went wrong, can't create user, send fail response
            #----------------------------------------------------------------
            response = {"outcome": "fail",
                        "message": "Failed to create user '{0}' - {1}".format(name, str(e))}


    return response 


def get_leaderboard_spm(request):

    #----------------------------------------------------------------
    # Get Score Per Minute leaderboard and return it to requester
    #----------------------------------------------------------------

    whitelist = None
    if "whitelist" in request:
        whitelist = request["whitelist"]

    leaderboard = leaderboard_spm(whitelist)

    response = {"outcome": "success",
                "message": "Got personal spm leaderboard",
                "leaderboard": leaderboard}

    return response


def get_leaderboard_score(request):

    #----------------------------------------------------------------
    # Optional arguments, check and use if exist
    #----------------------------------------------------------------
    whitelist = None
    if "whitelist" in request:
        whitelist = request["whitelist"]

    timescale = None
    if "timescale" in request:
        timescale = request["timescale"]



    #----------------------------------------------------------------
    # Get total Score leaderboard and return it to requester
    #----------------------------------------------------------------
    leaderboard = leaderboard_score(timescale, whitelist)

    response = {"outcome": "success",
                "message": "Got personal score leaderboard",
                "leaderboard": leaderboard}

    return response



def get_leaderboard_team_spm(request):

    #----------------------------------------------------------------
    # Get Team Score Per Minute leaderboard and return it to requester
    #----------------------------------------------------------------

    leaderboard = leaderboard_team_spm()

    response = {"outcome": "success",
                "message": "Got team spm leaderboard",
                "leaderboard": leaderboard}

    return response



def get_leaderboard_team_score(request):

    timescale = None
    if "timescale" in request:
        timescale = request["timescale"]


    #----------------------------------------------------------------
    # Get team total Score leaderboard and return it to requester
    #----------------------------------------------------------------

    leaderboard = leaderboard_team_score(timescale)

    response = {"outcome": "success",
                "message": "Got team score leaderboard",
                "leaderboard": leaderboard}

    return response











def invalid_request(request):
    response = {"outcome": "fail",
                "message": "Invalid request '{0}'".format(request["request_type"])}

    return response


def incomplete_json_request(request, missing_fields):
    response = {"outcome": "fail",
                "message": "Incomplete json request, missing/wrong datatype field/s " + str(missing_fields)}

    return response


def invalid_user():
    response = {"outcome": "fail",
                "error_code": 2,
                "message": "User not signed up"}

    return response


def invalidAccessToken(request):
    fb_id = request["fb_id"]

    response = {"outcome": "fail",
                "message": "Invalid or out of date fb_id & access token for fb_id '{0}'".format(fb_id)}

    return response