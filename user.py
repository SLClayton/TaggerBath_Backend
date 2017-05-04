import os
import logging
import time
from operator import itemgetter

from db_manager import getCloudSQL
from facebook import *


CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
USER_TABLE = os.environ.get("USER_TABLE")
USER_ITEMS_TABLE = os.environ.get("USER_ITEMS_TABLE")
TEAMS = os.environ.get("TEAMS").split(",")
GRID_TABLE = os.environ.get("GRID_TABLE")
SCORE_TABLE = os.environ.get("SCORE_TABLE")
ACCESS_TOKEN_TABLE = os.environ.get("ACCESS_TOKEN_TABLE")


#----------------------------------------------------------------
# Class to hold user data
#----------------------------------------------------------------
class User:

    def __init__(self, _id, fb_id, name, team, spm=None, email=None):
        self._id = _id
        self.name = name
        self.team = team
        self.email = email
        self.fb_id = fb_id
        self.spm = spm
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

            if len(self.items) > 0:

                values = ""
                for item in self.items.keys():
                    values += "({0}, '{1}', {2}),".format(self._id, item, self.items[item])

                values = values[:-1]


                cursor.execute ("""REPLACE INTO {0}.{1} (user_id, item, quantity)
                               VALUES {2}
                               """.format(CLOUDSQL_DB, USER_ITEMS_TABLE, values))


            else:
                cursor.execute ("""DELETE FROM {0}.{1} 
                                   WHERE {1}.user_id = {2}
                               """.format(CLOUDSQL_DB, USER_ITEMS_TABLE, self._id))


        cursor.close()
        db.commit()


    #----------------------------------------------------------------
    # Get user items from db
    #----------------------------------------------------------------
    def retreive_items_from_db(self, force=False):
        if self.items == None or force:
            self.items = get_user_items(self._id)


    def get_items(self):
        self.retreive_items_from_db()
        
        return self.items


    #----------------------------------------------------------------
    # Add an item to the users collection
    #----------------------------------------------------------------
    def add_item(self, item):
        self.retreive_items_from_db()

        if item in self.items:
            self.items[item] += 1
        else:
            self.items[item] = 1


    #----------------------------------------------------------------
    # Remove an item from the users collection
    #----------------------------------------------------------------
    def remove_item(self, item):
        self.retreive_items_from_db()

        if item in self.items:
            self.items[item] -= 1

            if self.items[item] < 0:
                self.items[item] = 0
        

    #----------------------------------------------------------------
    # Return number of squares user has
    #----------------------------------------------------------------
    def current_captures(self):
        return get_current_captures(self._id, self.team)



#----------------------------------------------------------------
# Verify user credentials, and then return a User object of that
# user
#----------------------------------------------------------------
def verify_and_get_user(fb_id, userAccessToken):



    #----------------------------------------------
    # For testing purposes, not used in prod
    #----------------------------------------------
    #if userAccessToken == "sam":
    #    return [True, getUser("fb_id", fb_id)]



    #----------------------------------------------
    # Check local accesstoken for match
    #----------------------------------------------
    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT u._id, u.fb_id, u.name, u.team, u.email,
                             CAST( SUM( IF(g._id IS NULL, 
                                           0, 
                                           IF(g.item IS NULL, 1, 20)))
                                  AS UNSIGNED) AS spm,
                       u.accessToken

                      FROM 

                     (SELECT iu._id, iu.fb_id, iu.name, iu.team, iu.email, at.accessToken
                      FROM      {0}.{1} AS iu
                      LEFT JOIN {0}.{2} AS at
                      ON iu.fb_id = at.fb_id
                      WHERE iu.fb_id = %s ) AS u

                      LEFT JOIN 
                      {0}.{3} AS g

                      ON (u._id in (g.stack1, 
                                    g.stack2, 
                                    g.stack3, 
                                    g.stack4))

                      AND g.team = u.team
                      AND g.level > 0

                      GROUP BY u._id
                      ;""".format(CLOUDSQL_DB,
                                  USER_TABLE,
                                  ACCESS_TOKEN_TABLE,
                                  GRID_TABLE),

                                  (fb_id,))

    row = cursor.fetchone()
    cursor.close()

    if row == None:
        return [verify_token_with_facebook(fb_id, userAccessToken), None]

    _id = row[0]
    fb_id = row[1]
    name = row[2]
    team = row[3]
    email = row[4]
    spm = row[5]
    accessToken = row[6]


    user = User(_id, fb_id, name, team, spm, email)

    #----------------------------------------------
    # Check local acccess token
    #----------------------------------------------
    if userAccessToken == accessToken:
        return [True, user]


    #----------------------------------------------
    # If no match check with facebook if valid
    #----------------------------------------------
    if verify_token_with_facebook(fb_id, userAccessToken):

        #----------------------------------------------
        # Update local value
        #----------------------------------------------
        update_local_token(fb_id, userAccessToken)

        return [True, user]
    


    return [False, user]


def getUser(id_type, value):
    #----------------------------------------------------------------
    # If lookup type is string, lookup via name. If not, then lookup
    # via id
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT u._id, u.fb_id, u.name, u.team,
                      CAST( SUM( IF(g._id IS NULL, 0, IF(g.item IS NULL, 1, 20)))
                            AS UNSIGNED) AS spm,
                            u.email

                      FROM 
                      {0}.{1} AS u
                      LEFT JOIN 
                      {0}.{2} AS g

                      ON (u._id in (g.stack1, 
                                    g.stack2, 
                                    g.stack3, 
                                    g.stack4))

                      AND g.team=u.team
                      AND g.level > 0
            
                      WHERE {3} = %s

                      GROUP BY u._id
                      ;""".format(CLOUDSQL_DB,
                                  USER_TABLE,
                                  GRID_TABLE,
                                  id_type),
                                  (str(value),))

    row = cursor.fetchone()
    cursor.close()

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
    cursor.close()


def is_username_taken(name):

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute ("""SELECT name FROM {0}.{1} ;""".format(CLOUDSQL_DB, USER_TABLE))

    for row in cursor.fetchall():
        if name.lower() == row[0].lower():
            cursor.close()
            return True

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
    #----------------------------------------------------------------
    # Get user items from items table
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()


    cursor.execute("""SELECT item, quantity FROM {0}.{1}
                      WHERE user_id = %s
                      ;""".format(CLOUDSQL_DB, USER_ITEMS_TABLE), (user_id, ))


    items = {}
    for row in cursor.fetchall():
        items[row[0]] = row[1]


    cursor.close()
    return items


def least_populous_team():
    #----------------------------------------------------------------
    # Find the team which has least members
    # (used for new users to assign a team)
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT 
                      SUM(team = 'red') AS red,
                      SUM(team = 'green') AS green,
                      SUM(team = 'blue') AS blue
                      from {0}.{1};""".format(CLOUDSQL_DB, USER_TABLE))


    row = cursor.fetchone()
    cursor.close()

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
        cursor.close()

        if row[0] == None:
            return 0
        else:
            return int(row[0])


def leaderboard_current_captures(whitelist=None):

    fb_id_where = ""
    if whitelist is not None:
        
        for fb_id in whitelist:
            fb_id_where += "'{0}',".format(fb_id)

        fb_id_where = " WHERE u.fb_id IN (" + fb_id_where[:-1] + ")"



                
    db = getCloudSQL()
    cursor = db.cursor()


    #--------------------------------------------------
    # Gets number of squares each user is on that has
    # points for them
    #--------------------------------------------------
    cursor.execute("""SELECT u.name, u.fb_id, u.team, 
                      CAST(IFNULL(COUNT(gs.stack1 
                                   OR gs.stack2 
                                   OR gs.stack3 
                                   OR gs.stack4), 0) AS UNSIGNED)
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
                      GROUP BY u.name 
                      ORDER BY captures DESC
                      LIMIT 100
                      ;""".format(CLOUDSQL_DB,
                                  USER_TABLE,
                                  GRID_TABLE,
                                  str(fb_id_where)))

    leaderboard = cursor.fetchall()

    cursor.close()

    return leaderboard


def leaderboard_spm(whitelist=None):

    fb_id_where = ""
    if whitelist is not None:
        
        for fb_id in whitelist:
            fb_id_where += "'{0}',".format(fb_id)

        fb_id_where = " WHERE u.fb_id IN (" + fb_id_where[:-1] + ")"



                
    db = getCloudSQL()
    cursor = db.cursor()


    #--------------------------------------------------
    # Gets number of squares each user is on that has
    # points for them
    #--------------------------------------------------
    cursor.execute("""SELECT u.name, u.fb_id, u.team, 
                      CAST( SUM( IF(g._id IS NULL, 0, IF(g.item IS NULL, 1, 20)))
                            AS UNSIGNED) AS spm

                      FROM 
                      {0}.{1} AS u
                      LEFT JOIN 
                      {0}.{2} AS g

                      ON (u._id in (g.stack1, 
                                    g.stack2, 
                                    g.stack3, 
                                    g.stack4))

                      AND g.team=u.team
                      AND g.level > 0

                      {3}

                      GROUP BY u.name 
                      ORDER BY spm DESC
                      ;""".format(CLOUDSQL_DB,
                                  USER_TABLE,
                                  GRID_TABLE,
                                  str(fb_id_where)))

    leaderboard = cursor.fetchall()

    cursor.close()

    return list(leaderboard)[0:100]



def leaderboard_score(timescale, whitelist=None):

    #--------------------------------------------------
    # Get leaderboard for score
    #--------------------------------------------------



    #--------------------------------------------------
    # IF whitelist given, only query Facebook values from
    # this list
    #--------------------------------------------------
    fb_id_where = ""
    if whitelist is not None:

        values = "'010101',"
        
        for fb_id in whitelist:
            values += "'{0}',".format(fb_id)

        fb_id_where = " WHERE u.fb_id IN (" + values[:-1] + ")"



    #--------------------------------------------------
    # If timescale given, only query for score
    # within this time
    #--------------------------------------------------
    if timescale is not None and timescale.upper() in ["HOUR", "DAY", "WEEK", "MONTH"]:
        t = "DATE_SUB(NOW(), INTERVAL 1 {0})".format(timescale)

    else:
        t = "'2000-01-01 00:00:00'"



    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT u.name, u.fb_id, u.team,
                      CAST(SUM(IF(s.time > {3},
                                  IFNULL(s.points, 0), 
                                  0))
                      AS UNSIGNED) AS total

                      FROM      {0}.{1} AS u
                      LEFT JOIN {0}.{2} AS s
                      ON u._id = s.user_id
                      {4}
                      GROUP BY u.name
                      ORDER BY total DESC

        ;""".format(CLOUDSQL_DB, 
                    USER_TABLE, 
                    SCORE_TABLE, 
                    t, 
                    fb_id_where))

    leaderboard = cursor.fetchall()

    cursor.close()

    return list(leaderboard)[0:100]


def leaderboard_team_spm():
    db = getCloudSQL()
    cursor = db.cursor()


    #--------------------------------------------------
    # Gets number of squares each user is on that has
    # points for them
    #--------------------------------------------------
    cursor.execute("""SELECT g.team,
                      CAST( SUM(IF(g.item is NULL, g.level, 20 * g.level))
                            AS UNSIGNED) AS spm

                      FROM 
                      {0}.{1} AS g

                      GROUP BY g.team
                      ORDER BY spm DESC
                      ;""".format(CLOUDSQL_DB,
                                  GRID_TABLE))


    leaderboard = cursor.fetchall()

    cursor.close()

    return leaderboard



def leaderboard_team_score(timescale):


    if timescale is not None and timescale.upper() in ["HOUR", "DAY", "WEEK", "MONTH"]:
        t = "DATE_SUB(NOW(), INTERVAL 1 {0})".format(timescale)

    else:
        t = "'2000-01-01 00:00:00'"



    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT u.team,
                             CAST(SUM(IF(s.time > {0},
                                         IFNULL(s.points, 0),
                                         0)) 
                                  AS UNSIGNED)
                             AS total

                      FROM      {1}.{2} AS s
                      LEFT JOIN {1}.{3} AS u

                      ON s.user_id = u._id

                      GROUP BY u.team
                      ORDER BY total DESC
        ;""".format(t, CLOUDSQL_DB, SCORE_TABLE, USER_TABLE))


    leaderboard = cursor.fetchall()

    cursor.close()

    return leaderboard


