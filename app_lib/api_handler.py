import logging
import os
import sys

from flask import Flask, jsonify, request
from json_checker import find_error_fields, need_verification
from db_manager import getCloudSQL
import MySQLdb

import grid
import facebook
from user import User, getUser, is_username_taken, createUser


LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LNG_SCALE = float(os.environ.get("LNG_SCALE"))


def api_request(request):

	#----------------------------------------------------------------
	# Check request JSON has no missing fields, correct types etc
	#----------------------------------------------------------------
	errors = find_error_fields(request, "request")
	if errors != []:
		return incomplete_json_request(request, errors)


	#----------------------------------------------------------------
	# check user exists and access token is correct
	#----------------------------------------------------------------
	if (request["request_type"] in need_verification and 
		not facebook.verify_token(request["fb_id"], request["userAccessToken"])):

		return invalidAccessToken(request)


	#----------------------------------------------------------------
	# If request doesn't need the user, go straight there
	#----------------------------------------------------------------
	if request["request_type"] == "create_user":
		return create_user(request)


	#----------------------------------------------------------------
	# Otherwise, check user is signed up
	#----------------------------------------------------------------
	user = getUser("fb_id", request["fb_id"])
	if user is None:
		return invalid_user()


	#----------------------------------------------------------------
	# Route request to correct function
	#----------------------------------------------------------------
	if request["request_type"] == "new_position":
		return new_position(request, user)

	elif request["request_type"] == "get_grid":
		return get_grid(request)

	elif request["request_type"] == "get_user_info":
		return get_user_info(request, user)

	else:
		return invalid_request(request)


def new_position(request, user):
	#----------------------------------------------------------------
	# Unpacks some useful arguments
	#----------------------------------------------------------------
	nw_lat = request["nw_lat"]
	nw_lng = request["nw_lng"]


	#----------------------------------------------------------------
	# Checking user is in area and gets specific square
	#----------------------------------------------------------------
	try:
		square = grid.getGridSquare(nw_lat, nw_lng)

	except AssertionError:
		response = {"outcome": "fail",
					"message": "Could not find square for ({0}, {1}), may be outside bounds"}
		return response
	

	#----------------------------------------------------------------
	# Updates team for that square
	#----------------------------------------------------------------
	oldteam = square.team
	square.team = user.team
	square.update()
		

	response = {"outcome": "success",
				"message": "Updated square id({0}) from team {1} to {2} with user {3}".format(square._id,
																			    			  oldteam,
																	                          square.team,
																	                          user.name),
				"updated_square": {"nw_lat": square.nw_lat,
								   "nw_lng": square.nw_lng,
								   "team": square.team
								   }
				}


	return response


def get_grid(request):
	nw_lat = request["nw_lat"]
	nw_lng = request["nw_lng"]
	se_lat = request["se_lat"]
	se_lng =request["se_lng"]

	try:
		g = grid.getGrid(nw_lat, nw_lng, se_lat, se_lng)

		response = {"outcome": "success",
					"grid":	g,
					"length": len(g),
					"message": "Grid successfully gotten."}

	except Exception as e:
		response = {"outcome": "fail",
					"message": "Failed to get grid. " + str(e)}

	return response


def get_user_info(request, user):

	response = {"outcome": "success",
				"message": "Successfully gotten user info for '{0}'".format(username),
				"user_info": {	"name": user.name,
								"team": user.team,
								"email": user.email,
								"fb_id": user.fb_id
								}
			}
		
	return response


def create_user(request):

	name = request["name"]
	email = request["email"]
	team = "blue"
	fb_id = request["fb_id"]


	if is_username_taken(name):
		response = {"outcome": "fail",
					"error_code": 1,
					"message": "Username '{0}' taken".format(name)}

	else:

		try:
			createUser(name, team, email, fb_id)

			response = {"outcome": "success",
						"message": "Created user {0}".format(str(getUser("fb_id", fb_id)))}


		except Exception as e:
			response = {"outcome": "fail",
						"message": "Failed to create user '{0}' - {1}".format(name, str(e))}


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
				"message": "Invalid user not signed up"}

	return response

def invalidAccessToken(request):
	fb_id = request["fb_id"]

	response = {"outcome": "fail",
				"message": "Invalid/out of date fb_id / access token for fb_id '{0}'".format(fb_id)}

	return response