import os
import MySQLdb
import logging
import time

from threaddata import thread_data



CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_IP = os.environ.get('CLOUDSQL_IP')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)



def getCloudSQL1():
    #----------------------------------------------------------------
    # Un-used function from a previous iteration
    #----------------------------------------------------------------

    t0 = time.time()
    thread_data.DB_access += 1

    if 'gDB' not in globals():
        global gDB
        gDB = None

    global gDB

    if gDB is None:
        logging.info("DB is None, Creating one")
        gDB = _getCloudSQL()

    else:
        logging.info("DB not None, re-using")
        try:
            c = gDB.cursor()
            c.execute("SELECT version()")

        except MySQLdb.Error:
            logging.info("DB disconnected on test, creating new connection")
            gDB = _getCloudSQL()



    thread_data.DB_access_times.append(str(time.time() - t0)[0:7])

    return gDB



def getCloudSQL():

    #----------------------------------------------------------------
    # Checks if a DB instance is created, returns it if it is,
    # and creates one if it isn't
    #----------------------------------------------------------------

    t0 = time.time()

    thread_data.DB_access += 1

    if thread_data.DB is None:
        logging.info("DB is None, Creating one")
        thread_data.DB = _getCloudSQL()
    else:
        logging.info("DB not None, re-using")


    thread_data.DB_access_times.append(str(time.time() - t0)[0:7])

    return thread_data.DB


def _getCloudSQL():
    #----------------------------------------------------------------
    # returns database connection from env variables
    #----------------------------------------------------------------
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):

        logging.info("Logging into DB via socket")

        thread_data.DB_access_type = "socket"

        cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)

        db = MySQLdb.connect(unix_socket=cloudsql_unix_socket,
                             user=CLOUDSQL_USER,
                             passwd=CLOUDSQL_PASSWORD)



    else:

        logging.info("Logging into DB via public IP")

        thread_data.DB_access_type = "IP"

        db = MySQLdb.connect(host=CLOUDSQL_IP,
                             user=CLOUDSQL_USER,
                             passwd=CLOUDSQL_PASSWORD)


    return db

__all__ = ['getCloudSQL']
