#/usr/bin/env python2

def getClientData(data):
    try:
        event = parseClientData(data)
        return event
    except ParseError:
        print "getClientData: Invalid data from client"
        return None

def parseClientData(data):
    # TODO: pass binary data here and actually parse it
    return data


