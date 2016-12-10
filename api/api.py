from flask import Flask, jsonify, request
import logging


def api(request):
	if request["request_type"] == "new_position":
		return new_position(request)

	else:
		response = {"request_id": request["request_id"],
					"outcome": "fail",
					"message": "Invalid request type"}

		return jsonify(response)


def new_position(request):

	response = {"request_id": request["request_id"],
				"outcome": "success",
				"message": "Its working so far"}

	return jsonify(response)