
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
    cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)


    if os.environ.get('SERVER_SOFTWARE','').startswith('Development'):
        db = MySQLdb.connect(host="146.148.27.235",
                             user=CLOUDSQL_USER,
                             passwd=CLOUDSQL_PASSWORD)

    else:
        db = MySQLdb.connect(unix_socket=cloudsql_unix_socket, 
                             user=CLOUDSQL_USER, 
                             passwd=CLOUDSQL_PASSWORD)


    return db

