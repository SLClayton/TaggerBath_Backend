import os

import logging
from db_manager import getCloudSQL

from user import User, getUser

LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LNG_SCALE = float(os.environ.get("LNG_SCALE"))
CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
GRID_TABLE = os.environ.get("GRID_TABLE")
USER_TABLE = os.environ.get("USER_TABLE")
MAX_STACK = int(os.environ.get("MAX_STACK"))
TEAMS = os.environ.get("TEAMS").split(",")


#----------------------------------------------------------------
# Class that represents a square on the grid
#----------------------------------------------------------------
class GridSquare:

    def __init__(self, _id, nw_lat, nw_lng, team, level, stack, item=None):

        self._id = _id
        self.nw_lat = float(nw_lat)
        self.nw_lng = float(nw_lng)
        self.team = team
        self.level = level
        self.stack = stack
        self.item = item

        self.changed = False





    def __str__(self):
        return "_id: {0} at ({1}, {2}) {3} team level {4}. {5}".format(self._id,
                                                                       self.nw_lat,
                                                                       self.nw_lng,
                                                                       self.team,
                                                                       self.level,
                                                                       str(self.stack))


    #----------------------------------------------------------------
    # Remove a user from this squares stack
    #----------------------------------------------------------------
    def remove_from_stack(self, _id):
        for user in self.stack:

            if user._id == _id:

                self.stack.remove(user)
                return True

        return False



    #----------------------------------------------------------------
    # Return a dict with the number of users from each team that
    # are on the stack
    #----------------------------------------------------------------
    def get_team_sizes(self):
        amounts = {}
        winning_team = None

        for user in self.stack:

            if user.team not in amounts:
                amounts[user.team] = 1
            else:
                amounts[user.team] += 1

            if winning_team == None or amounts[user.team] > amounts[winning_team]:
                winning_team = user.team


        # denote team with most users on stack
        amounts["winning_team"] = winning_team

        return amounts


    #----------------------------------------------------------------
    # Remove a member from the team specified from the stack
    #----------------------------------------------------------------
    def remove_team_user(self, team):
        for user in self.stack:
            if user.team == team:
                self.stack.remove(user)
                return True

        return False



    #----------------------------------------------------------------
    # Algorithm for deciding new state of square
    #----------------------------------------------------------------  
    def add_user(self, user):

        team_sizes = self.get_team_sizes()
        prev_leader = team_sizes["winning_team"]

        #----------------------------------------------------------------
        # If user already in the square stack, remove them first
        #----------------------------------------------------------------
        if not self.remove_from_stack(user._id):
            self.changed = True

        #----------------------------------------------------------------
        # Add user to end of list
        #----------------------------------------------------------------
        self.stack.append(user)

        team_sizes = self.get_team_sizes()


        #----------------------------------------------------------------
        # If this team has reached over max size, remove 1 from both 
        # other teams and 2 from this team
        #----------------------------------------------------------------
        enemies_removed = 0
        if team_sizes[user.team] > MAX_STACK:

            for team in TEAMS:

                if team != user.team and self.remove_team_user(team):
                    enemies_removed += 1

            enemies_removed = max(enemies_removed, 1)

            for i in range(enemies_removed):
                self.remove_team_user(user.team)


        #----------------------------------------------------------------
        # If this team reaches size of previous leader, remove 1 from
        # them
        #----------------------------------------------------------------
        elif prev_leader != None:
            if (user.team != prev_leader and team_sizes[user.team] == team_sizes[prev_leader]):
                self.remove_team_user(prev_leader)


        team_sizes = self.get_team_sizes()

        self.team = team_sizes["winning_team"]
        self.level = team_sizes[self.team] - (len(self.stack) - team_sizes[self.team])


    def get_stack_string(self):
        l = []

        for user in self.stack:
            l.append(str(user.team).upper() + "|" + str(user.name))

        return str(l)



    def update(self):
        #----------------------------------------------------------------
        # Updates the db values of the team and level depending on the
        # objects current variables
        #----------------------------------------------------------------
        db = getCloudSQL()
        cursor = db.cursor()

        #----------------------------------------------------------------
        # Fill rest of list with None values for database entry
        #----------------------------------------------------------------
        s = []
        for user in self.stack:
            s.append(user._id)

        while len(s) < 4:
            s.append(None)


        update_count = ""
        if self.changed:
            update_count = ", update_count = update_count + 1 "


        cursor.execute ("""UPDATE {0}.{1} 
                           SET team = %s, 
                               level = %s,
                               stack1 = %s,
                               stack2 = %s,
                               stack3 = %s,
                               stack4 = %s,
                               updated = NOW()
                               {2}
                           WHERE _id = %s ;""".format(CLOUDSQL_DB, GRID_TABLE, update_count), 
                                                    (self.team, 
                                                     self.level,
                                                     s[0],
                                                     s[1],
                                                     s[2],
                                                     s[3],
                                                     self._id))

        cursor.close()
        db.commit()




def getGridSquare(lat, lng):
    #----------------------------------------------------------------
    # returns a gridsquare object that the coordinates lay within
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""select gs._id, gs.nw_lat, gs.nw_lng, gs.team,   gs.level,      
                      gs.stack1,     gs.stack2, gs.stack3, gs.stack4, gs.item,
                      u._id,         u.fb_id,   u.name,    u.team

                      FROM {0}.{1} AS gs
                      LEFT JOIN {0}.{2} AS u

                      ON gs.stack1 = u._id
                      OR gs.stack2 = u._id
                      OR gs.stack3 = u._id
                      OR gs.stack4 = u._id

                      WHERE nw_lat >= %s 
                      and nw_lat < %s 
                      and nw_lng <= %s
                      and nw_lng > %s ;""".format(CLOUDSQL_DB, 
                                                  GRID_TABLE, 
                                                  USER_TABLE),
                                            (lat, 
                                             lat + LAT_SCALE,
                                             lng,
                                             lng - LNG_SCALE))


    #----------------------------------------------------------------
    # Return None if no rows found
    #----------------------------------------------------------------
    if cursor.rowcount < 1:
        return None


    stack = [None, None, None, None]

    for row in cursor.fetchall():

        [grid_id, nw_lat, nw_lng,  square_team, 
         level,   stack1, stack2,  stack3, 
         stack4,  item,   user_id, fb_id, 
         name,    user_team] = row


        #----------------------------------------------------------------
        # Build stack from db values
        #----------------------------------------------------------------
        if user_id is not None:
            
            if user_id == stack1:
                index = 0
            elif user_id == stack2:
                index = 1
            elif user_id == stack3:
                index = 2
            elif user_id == stack4:
                index = 3

            stack[index] = User(user_id, fb_id, name, user_team)

    cursor.close()

    while None in stack:
        stack.remove(None)

    return GridSquare(grid_id, nw_lat, nw_lng, square_team, level, stack, item)



def getGrid(nw_lat, nw_lng, se_lat, se_lng):
    #----------------------------------------------------------------
    # returns entire map within given bounds
    #----------------------------------------------------------------
    db = getCloudSQL()
    cursor = db.cursor()


    cursor.execute("""SELECT nw_lat, nw_lng, team, level, item FROM {0}.{1}
                      WHERE nw_lat >= %s 
                      and nw_lat < %s 
                      and nw_lng <= %s
                      and nw_lng > %s ;""".format(CLOUDSQL_DB, GRID_TABLE),
                                            (se_lat,
                                             nw_lat + LAT_SCALE,
                                             se_lng,
                                             nw_lng - LNG_SCALE))


    grid = []
    for row in cursor.fetchall():
        square = []
        square.append(str(row[0]))
        square.append(str(row[1]))
        square.append(row[2])
        
        if row[3] == None:
            square.append(0)
        else:
            square.append(row[3])

        if row[4] is not None:
            square.append(row[4])

        grid.append(square)

    cursor.close()

    return grid





