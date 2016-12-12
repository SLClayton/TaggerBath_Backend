
import os

import MySQLdb
import webapp2


def getCloudSQL():
	#----------------------------------------------------------------
	# returns database connection from env variables
	#----------------------------------------------------------------

    CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
    CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
    CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')

    db = MySQLdb.connect(unix_socket=cloudsql_unix_socket, 
                         user=CLOUDSQL_USER, 
                         passwd=CLOUDSQL_PASSWORD)

    return db

