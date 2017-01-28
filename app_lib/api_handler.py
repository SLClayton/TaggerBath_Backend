import logging
import os
import sys

from flask import Flask, jsonify, request
from json_checker import find_error_fields
from db_manager import getCloudSQL
import MySQLdb

import grid
from user import User, getUser


LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LONG_SCALE = float(os.environ.get("LONG_SCALE"))


def api_request(request):

	#----------------------------------------------------------------
	# Check request JSON has all needed fields
	#----------------------------------------------------------------
	error_fields = find_error_fields(request, "request")
	if error_fields != []:
		return incomplete_json_request(request, error_fields)


	#----------------------------------------------------------------
	# Check arguments JSON for specific request type has all
	# needed fields
	#----------------------------------------------------------------
	error_arguments = find_error_fields(request["arguments"], request["request_type"])
	if error_arguments != []:
		return incomplete_json_arguments(request, error_arguments)



	#----------------------------------------------------------------
	# Route request to correct function
	#----------------------------------------------------------------
	if request["request_type"] == "new_position":
		return new_position(request)

	elif request["request_type"] == "get_grid":
		return get_grid(request)

	else:
		return invalid_request(request)




def new_position(request):
	#----------------------------------------------------------------
	# Unpacks some useful arguments
	#----------------------------------------------------------------
	username = request["user"]
	nw_lat = request["arguments"]["nw_lat"]
	nw_long = request["arguments"]["nw_long"]


	#----------------------------------------------------------------
	# Checking user is in area and gets specific square
	#----------------------------------------------------------------
	try:
		square = grid.getGridSquare(nw_lat, nw_long)

	except AssertionError:
		response = {"request_id": request["request_id"],
					"outcome": "fail",
					"message": "Could not find square for ({0}, {1}), may be outside bounds"}
		return response


	#----------------------------------------------------------------
	# Checking user exists and gets User object
	#----------------------------------------------------------------
	try:
		user = getUser(username)

	except AssertionError:
		response = {"request_id": request["request_id"],
					"outcome": "fail",
					"message": "Invalid user '{0}'".format(username)}
		return response
	

	#----------------------------------------------------------------
	# Updates team for that square
	#----------------------------------------------------------------
	oldteam = square.team
	square.team = user.team
	square.update()
		


	response = {"request_id": request["request_id"],
				"outcome": "success",
				"message": "Updated square id({0}) from team {1} to {2} with user {3}".format(square._id,
																			    			  oldteam,
																	                          square.team,
																	                          user.name)}


	return response

def get_grid(request):
	nw_lat = request["arguments"]["nw_lat"]
	nw_long = request["arguments"]["nw_long"]
	se_lat = request["arguments"]["se_lat"]
	se_long =request["arguments"]["se_long"]

	try:
		g = grid.getGrid(nw_lat, nw_long, se_lat, se_long)

		response = {"request_id": request["request_id"],
					"outcome": "success",
					"grid":	g,
					"length": len(g),
					"message": "Grid successfully gotten."}

	except Exception as e:
		response = {"request_id": request["request_id"],
					"outcome": "fail",
					"message": "Failed to get grid. " + str(e)}

	return response





def invalid_request(request):
	response = {"request_id": request["request_id"],
				"outcome": "fail",
				"message": "Invalid request '{0}'".format(request["request_type"])}

	return response

def incomplete_json_request(request, missing_fields):
	if "request_id" in missing_fields:
		rid = "Not given"
	else:
		rid = request["request_id"]

	response = {"request_id": rid,
				"outcome": "fail",
				"message": "Incomplete json request, missing/wrong datatype field/s " + str(missing_fields)}

	return response

def incomplete_json_arguments(request, missing_arguments):
	response = {"request_id": request["request_id"],
				"outcome": "fail",
				"message": "Incomplete json arguments for '{0}', missing/wrong datatype field/s ".format(request["request_type"]) + str(missing_arguments)}

	return response