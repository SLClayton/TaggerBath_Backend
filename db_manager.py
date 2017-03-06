import os
import MySQLdb
import logging

from threaddata import thread_data



CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_IP = os.environ.get('CLOUDSQL_IP')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)



def getCloudSQL():

    thread_data.DB_access += 1

    if thread_data.DB is None:
        logging.info("DB is None, Creating one")
        thread_data.DB = _getCloudSQL()
    else:
        logging.info("DB not None, re-using")

    return thread_data.DB



def _getCloudSQL():
    #----------------------------------------------------------------
    # returns database connection from env variables
    #----------------------------------------------------------------
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)

        db = MySQLdb.connect(unix_socket=cloudsql_unix_socket,
                             user=CLOUDSQL_USER,
                             passwd=CLOUDSQL_PASSWORD)

    else:
        db = MySQLdb.connect(host=CLOUDSQL_IP,
                             user=CLOUDSQL_USER,
                             passwd=CLOUDSQL_PASSWORD)


    return db

__all__ = ['getCloudSQL']
