import urllib, urllib2
import json
import os
import logging


def verify_token(fb_id, userAccessToken):

    APP_ID = str(os.environ.get("FACEBOOK_APP_ID"))
    APP_SECRET = str(os.environ.get("FACEBOOK_APP_SECRET"))


    url = "https://graph.facebook.com/debug_token?"

    url += "input_token=%s&access_token=%s|%s" % (urllib.quote(str(userAccessToken)),
                                                  urllib.quote(APP_ID),
                                                  urllib.quote(APP_SECRET))
                    
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)


    r = json.load(response)

    logging.info(str(r))

    

    if (r["data"]["is_valid"] == True   and 
        r["data"]["app_id"]   == APP_ID and 
        r["data"]["user_id"]  == fb_id):

        return True


    return False

    
