import os
import logging
from operator import itemgetter

from db_manager import getCloudSQL


CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
USER_TABLE = os.environ.get("USER_TABLE")
USER_ITEMS_TABLE = os.environ.get("USER_ITEMS_TABLE")
TEAMS = os.environ.get("TEAMS").split(",")
GRID_TABLE = os.environ.get("GRID_TABLE")



class User:

    def __init__(self, _id, fb_id, name, team, email=None):
        self._id = _id
        self.name = name
        self.team = team
        self.email = email
        self.fb_id = fb_id
        self.items = None

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


        #----------------------------------------------------------------
        # Update items in items table if it was ever retrieved
        #----------------------------------------------------------------
        if self.items != None:
            for item in self.items.keys():

                cursor.execute ("""REPLACE INTO {0}.{1} (user_id, item, quantity)
                               VALUES (%s, %s, %s)
                               """.format(CLOUDSQL_DB, USER_ITEMS_TABLE), 
                                                (self._id,
                                                 item,
                                                 self.items[item]))


        db.commit()
        db.close()

    def retreive_items_from_db(self, force=False):
        if self.items == None or force:
            self.items = get_user_items(self._id)

    def get_items(self):
        self.retreive_items_from_db()
        
        return self.items

    def add_item(self, item):
        self.retreive_items_from_db()

        if item in self.items:
            self.items[item] += 1
        else:
            self.items[item] = 1

    def remove_item(self, item):
        self.retreive_items_from_db()

        if item in self.items:
            self.items[item] -= 1

            if self.items[item] <= 0:
                del self.items[item]
        

    def current_captures(self):
        return get_current_captures(self._id, self.team)



def getUser(id_type, value):
    #----------------------------------------------------------------
    # If lookup type is string, lookup via name. If not, then lookup
    # via id
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT _id, fb_id, name, team, email 
                      FROM {0}.{1} 
                      WHERE {2} = %s ;""".format(CLOUDSQL_DB,
                                                  USER_TABLE,
                                                  id_type),
                                                  (str(value),))

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
                                                           team.lower(),
                                                           email.lower(), 
                                                           fb_id))

    db.commit()
    db.close()


def is_username_taken(name):

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute ("""SELECT name FROM {0}.{1} ;""".format(CLOUDSQL_DB, USER_TABLE))

    for row in cursor.fetchall():
        if name.lower() == row[0].lower():
            db.close()
            return True

    db.close()
    return False


def is_username_valid(name):

    alphabet = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"

    whitelist = alphabet.lower() + alphabet.upper() + numbers + "_-"


    for c in name:
      if c not in whitelist:
        return False

    return True


def get_user_items(user_id):
    db = getCloudSQL()
    cursor = db.cursor()


    cursor.execute("""SELECT item, quantity FROM {0}.{1}
                      WHERE user_id = %s
                      ;""".format(CLOUDSQL_DB, USER_ITEMS_TABLE), (user_id, ))


    items = {}
    for row in cursor.fetchall():
        items[row[0]] = row[1]


    return items


def least_populous_team():
    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT 
                      SUM(team = 'red') AS red,
                      SUM(team = 'green') AS green,
                      SUM(team = 'blue') AS blue
                      from {0}.{1};""".format(CLOUDSQL_DB, USER_TABLE))


    row = cursor.fetchone()
    db.close()

    return TEAMS[row.index(min(row))]


def get_current_captures(user_id, team):
        #----------------------------------------------------------------
        # Get the amount of squares the user is on that is controlled
        # by his team
        #---------------------------------------------------------------
        db = getCloudSQL()
        cursor = db.cursor()

        cursor.execute("""SELECT 
                          SUM(team = %s AND
                                (stack1 = %s or
                                 stack2 = %s or
                                 stack3 = %s or
                                 stack4 = %s)) 
                          AS c
                          from {0}.{1};""".format(CLOUDSQL_DB, GRID_TABLE),
                          (team,
                           user_id,
                           user_id,
                           user_id,
                           user_id))


        row = cursor.fetchone()
        db.close()

        if row[0] == None:
            return 0
        else:
            return int(row[0])



def leaderboard_current_captures(whitelist=None):


    #--------------------------------------------------
    # Create where clause to whitelist fb IDs if given
    #--------------------------------------------------
    fb_id_where = ""
    if whitelist != None: 

        if len(whitelist) <= 0:
            return []

        for fb_id in whitelist:
            fb_id_where += " fb_id = '{0}' OR ".format(fb_id)

        fb_id_where = "WHERE (" + fb_id_where[:-3] + ")"

                
    db = getCloudSQL()
    cursor = db.cursor()


    #--------------------------------------------------
    # Gets number of squares each user is on that has
    # points for them
    #--------------------------------------------------
    cursor.execute("""SELECT u.name, u.fb_id, u.team, 
                      IFNULL(COUNT(gs.stack1 
                                   OR gs.stack2 
                                   OR gs.stack3 
                                   OR gs.stack4), 0) 
                      AS captures
                      FROM {0}.{1} AS u
                      LEFT JOIN {0}.{2} AS gs

                      ON (gs.stack1=u._id OR
                          gs.stack2=u._id OR
                          gs.stack3=u._id OR
                          gs.stack4=u._id)
                      AND gs.team=u.team
                      AND gs.level > 0
                      {3}
                      GROUP BY name 
                      ORDER BY captures DESC;
                      """.format(CLOUDSQL_DB,
                                  USER_TABLE,
                                  GRID_TABLE,
                                  fb_id_where))

    logging.info(cursor._last_executed)

    db.close()

    return cursor.fetchall()