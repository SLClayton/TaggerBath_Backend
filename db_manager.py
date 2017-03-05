import os
import MySQLdb

from thread import thread_data



























CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_IP = os.environ.get('CLOUDSQL_IP')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)



def getCloudSQL():

    DB = getattr(thread_data, 'DB', None)

    if DB is None:
        thread_data.DB = _getCloudSQL()

    return DB



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
