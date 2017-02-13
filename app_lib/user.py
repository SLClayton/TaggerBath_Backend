import os

from db_manager import getCloudSQL

CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
USER_TABLE = os.environ.get("USER_TABLE")



class User:

    def __init__(self, _id, name, team, email, fb_id):
        self._id = _id
        self.name = name
        self.team = team
        self.email = email
        self.fb_id = fb_id

    def __str__(self):
        return "USER: {0}, n:{1}, t:{2}, em:{3}, fb_id:{4}".format( self._id,
                                                                    self.name,
                                                                    self.team,
                                                                    self.email,
                                                                    self.fb_id)

    def update(self):
        #----------------------------------------------------------------
        # Updates the values of the team and level depending on the
        # objects current variables
        #----------------------------------------------------------------
        db = getCloudSQL()
        cursor = db.cursor()

        cursor.execute ("""UPDATE {0}.{1} 
                           SET team = %s, 
                               email = %s,
                               name = %s
                           WHERE _id = %s""".format(CLOUDSQL_DB, USER_TABLE), 
                                            (self.team, 
                                             self.email,
                                             self.name, 
                                             self._id))

        db.commit()
        db.close()


def getUser(id_type, value):
    #----------------------------------------------------------------
    # If lookup type is string, lookup via name. If not, then lookup
    # via id
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT _id, name, team, email, fb_id 
                      FROM {0}.{1} 
                      WHERE {2} = %s ;""".format(CLOUDSQL_DB,
                                                  USER_TABLE,
                                                  id_type),
                                                  (value,))

    row = cursor.fetchone()

    db.close()

    #----------------------------------------------------------------
    # Return None if user doesn't exist
    #----------------------------------------------------------------
    if (row is None):
      return None

    #----------------------------------------------------------------
    # Turn db data into user object and return
    #----------------------------------------------------------------
    return User(*row)


def createUser(name, team, email, fb_id):
    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute ("""INSERT INTO {0}.{1} (name, team, email, fb_id)
                       VALUES (%s, %s, %s, %s);""".format(CLOUDSQL_DB, USER_TABLE), 
                                                          (name, 
                                                           team,
                                                           email, 
                                                           fb_id))

    db.commit()
    db.close()


def is_username_taken(name):

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute ("""SELECT name FROM {0}.{1}
                       WHERE name = %s ;""".format(CLOUDSQL_DB, USER_TABLE), (name,))

    count = cursor.rowcount

    db.close()

    if count > 0:
      return True

    return False


