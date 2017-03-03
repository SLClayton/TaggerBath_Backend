import sys
import logging

templates = {
            "request": {"request_type": str},

            "credentials":{"fb_id": str,
                           "userAccessToken": str},

            "new_position": {"nw_lat": float,
                             "nw_lng": float
                             },

            "get_grid": {"nw_lat": float,
                        "nw_lng": float,
                        "se_lat": float,
                        "se_lng": float
                        },

            "create_user": {"name": str,
                            "email": str,
                            },

            "check_name_exists":{"name": str
                                },

            "get_grid_square":{"nw_lat": float,
                               "nw_lng": float
                               },

            "get_leaderboard_current_captures": {},

            "get_scale": {}

            }

need_verification = ["create_user", 
                     "new_position",
                     "get_user_info"
                     ]


def find_error_fields(arguments, request_type):

    errors = []

    if request_type not in templates:
        return errors

    template = templates[request_type]

    for field in template.keys():

        #----------------------------------------------------------------
        # Check if field is present
        #----------------------------------------------------------------
        if field not in arguments:
            errors.append("'" + field + "' argument missing")

        else:

            correct_type = template[field]
            this_type = type(arguments[field])

            #----------------------------------------------------------------
            # Check field is of right type, (allow ints for floats)
            #----------------------------------------------------------------
            if (correct_type is not this_type) and (this_type is not int or correct_type is not float):

                errors.append("'" + field + "' should be of type " + str(correct_type) + " not " + str(this_type))


            
    if request_type is "request":

        req = arguments["request_type"]

        if req in need_verification:
            errors += find_error_fields(arguments, "credentials")

        if req in templates:
            errors += find_error_fields(arguments, req)




    return errors
