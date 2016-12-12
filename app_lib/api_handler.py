from flask import Flask, jsonify, request
import logging


def api(request):
	if request["request_type"] == "new_position":
		return new_position(request)

	else:
		return invalid_request(request)




def new_position(request):
	response = {"request_id": request["request_id"],
				"outcome": "success",
				"message": "Its working so far"}

	return response


def invalid_request(request):
	response = {"request_id": request["request_id"],
				"outcome": "fail",
				"message": "Invalid request '{0}'".format(request["request_type"])}

	return response