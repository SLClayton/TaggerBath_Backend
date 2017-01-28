import os

from db_manager import getCloudSQL

CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
USER_TABLE = os.environ.get("USER_TABLE")



class User:

    def __init__(self, _id, name, team, email):
        self._id = _id
        self.name = name
        self.team = team
        self.email = email

    def __str__(self):
        return "USER: {0}, n:{1}, t:{2}, em:{3}".format(self._id,
                                                        self.name,
                                                        self.team,
                                                        self.email)

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


def getUser(lookup):
    #----------------------------------------------------------------
    # If lookup type is string, lookup via name. If not, then lookup
    # via id
    #----------------------------------------------------------------
    if type(lookup) == str:
      field = "name"
    else:
      field = "_id"

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT * FROM {0}.{1} 
                      WHERE {2} = %s ;""".format(CLOUDSQL_DB,
                                                  USER_TABLE,
                                                  field),
                                                  (lookup,))

    row = cursor.fetchone()

    #----------------------------------------------------------------
    # This makes sure user exists
    #----------------------------------------------------------------
    assert row is not None

    #----------------------------------------------------------------
    # Turn db data into user object and return
    #----------------------------------------------------------------
    return User(*row)