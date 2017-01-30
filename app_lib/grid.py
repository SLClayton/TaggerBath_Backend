import os

from db_manager import getCloudSQL

LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LNG_SCALE = float(os.environ.get("LNG_SCALE"))
CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
GRID_TABLE = os.environ.get("GRID_TABLE")



class GridSquare:

    def __init__(self, _id, nw_lat, nw_lng, team, level):
        self._id = _id
        self.nw_lat = nw_lat
        self.nw_lng = nw_lng
        self.team = team
        self.level = level

    def __str__(self):
        return "_id: {0} at ({1}, {2}) {3} team level {4}.".format(self._id,
                                                                   self.nw_lat,
                                                                   self.nw_lng,
                                                                   self.team,
                                                                   self.level)

    def update(self):
        #----------------------------------------------------------------
        # Updates the values of the team and level depending on the
        # objects current variables
        #----------------------------------------------------------------
        db = getCloudSQL()
        cursor = db.cursor()

        cursor.execute ("""UPDATE {0}.{1} 
                           SET team = %s, 
                               level = %s
                           WHERE _id = %s ;""".format(CLOUDSQL_DB, GRID_TABLE), 
                                            (self.team, 
                                             self.level, 
                                             self._id))

        db.commit()
        db.close()




def getGridSquare(lat, lng):
    #----------------------------------------------------------------
    # returns a gridsquare object that the coordinates are inside
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT * FROM {0}.{1} 
                      WHERE nw_lat >= %s 
                      and nw_lat < %s 
                      and nw_lng <= %s
                      and nw_lng > %s ;""".format(CLOUDSQL_DB, GRID_TABLE),
                                            (lat, 
                                             lat + LAT_SCALE,
                                             lng,
                                             lng - LNG_SCALE))

    row = cursor.fetchone()

    #----------------------------------------------------------------
    # This makes sure the co-ordinates are within the entire area
    #----------------------------------------------------------------
    assert row is not None

    return GridSquare(*row)


def getGrid(nw_lat, nw_lng, se_lat, se_long):
    #----------------------------------------------------------------
    # returns entire map
    #----------------------------------------------------------------
    db = getCloudSQL()
    cursor = db.cursor()


    cursor.execute("""SELECT * FROM {0}.{1}
                      WHERE nw_lat >= %s 
                      and nw_lat < %s 
                      and nw_lng <= %s
                      and nw_lng > %s ;""".format(CLOUDSQL_DB, GRID_TABLE),
                                            (se_lat,
                                             nw_lat,
                                             se_long,
                                             nw_lng))


    grid = []
    for row in cursor.fetchall():
        square = []
        #square.append(row[0])
        square.append(str(row[1]))
        square.append(str(row[2]))
        square.append(row[3])
        #square.append(row[4])

        grid.append(square)



    return grid




