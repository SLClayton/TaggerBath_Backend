import os

from db_manager import getCloudSQL

LAT_SCALE = float(os.environ.get("LAT_SCALE"))
LONG_SCALE = float(os.environ.get("LONG_SCALE"))



class GridSquare:

	def __init__(self, _id, nw_lat, nw_long, team, level)
	self._id = _id
	self.nw_lat = nw_lat
	self.nw_long = nw_long
	self.team = team
	self.level = level



def getGridSquare(lat, long):

	db = getCloudSQL()
	cursor = db.cursor()

	cursor.execute("""SELECT * FROM landgrab_db.grid_squares 
					  WHERE _id = 34000 ;""")

	rows = cursor.fetchall()

	return
