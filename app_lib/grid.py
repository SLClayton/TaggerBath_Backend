import os

from db_manager import getCloudSQL

LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LONG_SCALE = float(os.environ.get("LONG_SCALE"))
GRID_TABLE = os.environ.get("GRID_TABLE")



class GridSquare:

    def __init__(self, _id, nw_lat, nw_long, team, level):
        self._id = _id
        self.nw_lat = nw_lat
        self.nw_long = nw_long
        self.team = team
        self.level = level

    def __str__(self):
        return "_id: {0} at ({1}, {2}) {3} team level {4}.".format(self._id,
                                                                 self.nw_lat,
                                                                 self.nw_long,
                                                                 self.team,
                                                                 self.level)

    def update(self):
        #----------------------------------------------------------------
        # Updates the values of the team and level depending on the
        # objects current variables
        #----------------------------------------------------------------
        db = getCloudSQL()
        cursor = db.cursor()

        cursor.execute ("""UPDATE {0} 
                           SET team = %s, 
                               level = %s
                           WHERE _id = %s""".format(GRID_TABLE), 
                                            (self.team, 
                                             self.level, 
                                             self._id))

        db.commit()
        db.close()




def getGridSquare(lat, lon):
    #----------------------------------------------------------------
    # returns a gridsquare object that the coordinates are inside
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT * FROM {0} 
                      WHERE nw_lat >= %s 
                      and nw_lat < %s 
                      and nw_long <= %s
                      and nw_long > %s ;""".format(GRID_TABLE),
                                            (lat, 
                                             lat + LAT_SCALE,
                                             lon,
                                             lon - LONG_SCALE))

    rows = cursor.fetchall()


    #----------------------------------------------------------------
    # This makes sure the co-ordinates are within the entire area
    #----------------------------------------------------------------
    assert len(rows) != 0

    return GridSquare(*rows[0])
