

templates = {
            "request": {"request_id": int,
                        "request_type": str,
                        "arguments": dict,
                        "user": str
                        },

            "new_position": {"nw_lat": float,
                             "nw_long": float
                             }
            }


def find_error_fields(arguments, request_type):

    errors = []

    #----------------------------------------------------------------
    # If an incorrect request type is entered, it will be found
    # once this is returned in the next bit of code, so checking
    # here is pointless.
    #----------------------------------------------------------------
    if request_type not in templates.keys():
        return errors


    #----------------------------------------------------------------
    # Finds all errors in fields in a list for that particular 
    # request type, if list is empty at the end then all fields
    # are present and correct
    #----------------------------------------------------------------
    for field in templates[request_type].keys():

        if (field not in arguments or 
            type(arguments[field]) != templates[request_type][field]):

            errors.append(field)

    return errors
