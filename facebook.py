import urllib, urllib2
import json
import os
import logging
from db_manager import getCloudSQL

CLOUDSQL_DB = os.environ.get("CLOUDSQL_DB")
ACCESS_TOKEN_TABLE = os.environ.get("ACCESS_TOKEN_TABLE")





def verify_token_with_facebook(fb_id, userAccessToken):

    #----------------------------------------------------------------
    # Chwecks with the Facebook API whether or not the given
    # accessToken matches with the facebook ID given
    #----------------------------------------------------------------

    APP_ID = str(os.environ.get("FACEBOOK_APP_ID"))
    APP_SECRET = str(os.environ.get("FACEBOOK_APP_SECRET"))


    #----------------------------------------------------------------
    # Create url request
    #----------------------------------------------------------------
    url = "https://graph.facebook.com/debug_token?"

    url += "input_token=%s&access_token=%s|%s" % (urllib.quote(str(userAccessToken)),
                                                  urllib.quote(APP_ID),
                                                  urllib.quote(APP_SECRET))
                    
    try:                
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

    except Exception as e:
        logging.info("Error verifying fb_id with Facebook")
        return False


    r = json.load(response)

    logging.info(str(r))

    
    #----------------------------------------------------------------
    # Check response for not only if token was correct, but if it
    # is for the correct app
    #----------------------------------------------------------------
    if (r["data"]["is_valid"] == True   and 
        r["data"]["app_id"]   == APP_ID and 
        r["data"]["user_id"]  == fb_id):

        return True




    return False
    


def get_local_token(fb_id):

    #----------------------------------------------------------------
    # Check local Database to see if an accesstoken has been 
    # kept for this Facebook ID
    #----------------------------------------------------------------

    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""SELECT accessToken
                      FROM {0}.{1}
                      WHERE fb_id = %s
                      ;""".format(CLOUDSQL_DB, ACCESS_TOKEN_TABLE),
                      (fb_id,))


    row = cursor.fetchone()
    cursor.close()

    if row == None:
        return None
    else:
        return row[0]
    

def update_local_token(fb_id, userAccessToken):
    #----------------------------------------------------------------
    # Uodate local DB for access token for this facebook ID
    #----------------------------------------------------------------


    db = getCloudSQL()
    cursor = db.cursor()

    cursor.execute("""REPLACE INTO {0}.{1} (fb_id, accessToken)
                      VALUES (%s, %s);""".format(CLOUDSQL_DB, ACCESS_TOKEN_TABLE),
                      (fb_id, userAccessToken))

    cursor.close()
    db.commit()