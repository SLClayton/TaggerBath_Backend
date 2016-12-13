from flask import Flask, jsonify, request
import logging
import os

from json_checker import find_error_fields
from db_manager import getCloudSQL

import MySQLdb

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

	else:
		return invalid_request(request)




def new_position(request):
	


#	try:
	nw_lat = request["arguments"]["nw_lat"]
	nw_long = request["arguments"]["nw_long"]



	db = getCloudSQL()
	cursor = db.cursor()

	cursor.execute("""SELECT * FROM grid_squares 
					  WHERE nw_lat >= %s 
					  AND   nw_lat <  %s 
					  AND   nw_long <= %s 
					  AND	nw_long > %s ;""", (nw_lat,
											    nw_lat + LAT_SCALE,
											    nw_long,
											    nw_long - LONG_SCALE))
	rows = cursor.fetchall()



#	except MySQLdb.Error, e:
#		response = {"request_id": request["request_id"],
#					"outcome": "fail",
#					"message": "MySQL Error: {0}".format(str(e))}
#
#		return response

	






	response = {"request_id": request["request_id"],
				"outcome": "success",
				"message": "first row: " + str(rows[0])}

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
				"message": "Incomplete json request, missing/wrong datatype field/s " + str(missing_fields) + str(type(request["user"]))}

	return response

def incomplete_json_arguments(request, missing_arguments):
	response = {"request_id": request["request_id"],
				"outcome": "fail",
				"message": "Incomplete json arguments for '{0}', missing/wrong datatype field/s ".format(request["request_type"]) + str(missing_arguments)}

	return response