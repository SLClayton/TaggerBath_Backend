

templates = {
            "request": ["request_id",
                         "request_type",
                         "arguments",
                         "user"],

            "new_position": ["nw_lat",
                             "nw_long"]
            }


def find_missing_fields(arguments, request_type):

    #----------------------------------------------------------------
    # Finds all missing fields in a list for that particular 
    # request type, if list is empty at the end then all fields
    # are present
    #----------------------------------------------------------------

    missing = []

    for field in templates[request_type]:
        if field not in arguments:
            missing.append(field)

    return missing
