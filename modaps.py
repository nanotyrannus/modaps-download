import argparse
import xmltodict as xml
import urllib.request as request
import json
import re
import time
from datetime import date


def getResponseDict(url):
    response = request.urlopen(url)
    response_text = response.read().decode('utf-8')
    parsed_response = xml.parse(response_text)
    return parsed_response

#download M*D09GA products
parser = argparse.ArgumentParser(prog='MODAPS downloader',description='Downloads MODAPS products')
parser.add_argument('-m', '--mode', default="search", type=str, help=(
    "Specifies what you want to do."
    " 'search' searches the MODAPS database for files according to your search parameters"
    " 'list' lists names of all MODAPS products. You can search the list with the --term flag"
    " 'download' downloads files to specified directory."
))
parser.add_argument('-t', '--term', type=str, default="", help=(
    "Search term for list mode. Wildcards (*) are supported, e.g. 'M*D09GA'"
    " Case-insensitive."
))
parser.add_argument('-n', '--north', type=float, default=90, help=(
    "Value for north boundary."
    " -90 to 90 for coordinate boundaries."
    " 0 to 17 for tile boundaries."
    ))
parser.add_argument('-s', '--south', type=float, default=-90, help=(
    "Value for south boundary."
    " -90 to 90 for coordinate boundaries."
    " 0 to 17 for tile boundaries."
))
parser.add_argument('-e', '--east', type=float, default=180, help=(
    "Value for east boundary."
    " -180 to 180 for coordinate boundaries."
    " 0 to 35 for tile boundaries."
))
parser.add_argument('-w', '--west', type=float, default=-180, help=(
    "Value for west boundary."
    " -180 to 180 for coordinate boundaries."
    " 0 to 35 for tile boundaries."
))
parser.add_argument('-c', '--coords', type=str, default="coords", help=(
    "Coordinate mode. 'coords', 'tiles', or 'global'."
    " If 'global', then coordinate values are all ignored."
    " Default is 'coords'."
))
parser.add_argument('--start', type=str, help=(
    "Start date of search. YYYY-MM-DD or YYYY-MM-DD hh:mm:ss"
))
parser.add_argument('--end', type=str, help=(
    "End date of search. YYYY-MM-DD or YYYY-MM-DD hh:mm:ss"
))
parser.add_argument('-p', '--name', type=str, default="",help=(
    "Product name."
))
parser.add_argument('-o', '--output', type=str, default="", help=(
    "Directory to which the files will be downloaded."
))
parser.add_argument('--pid', type=str, help=(
    "Comma delimited list of file IDs to download."
))

args_obj = parser.parse_args()

if (args_obj.mode == 'list'):
    print("Fetching MODAPS product list...")
    term = args_obj.term.replace("*", ".*")
    prog = re.compile(pattern=term, flags=re.IGNORECASE)
    
    if (args_obj.term != ''):
        print("Search term: {}".format(args_obj.term))

    parsed_response = getResponseDict("http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/listProducts")
    
    for obj in parsed_response['mws:Products']['mws:Product']:
        if (bool(prog.search(obj['mws:Name'])) | bool(prog.search(obj['mws:Description']))):
            print(obj['mws:Name'], ". . . . .",obj['mws:Description'])

elif (args_obj.mode == 'search'):
    if (args_obj.coords == 'tiles'):
        # Change default coord values to tile values
        # if in 'tiles' mode
        if (args_obj.north == 90): args_obj.north = 17
        if (args_obj.south == -90): args_obj.south = 0
        if (args_obj.east == 180): args_obj.east = 35
        if (args_obj.west == -180): args_obj.west = 0

    products = args_obj.name.upper() # For now a single value, should be generalized to accept list
    start_time = args_obj.start
    end_time = args_obj.end
    north = args_obj.north
    south = args_obj.south
    east = args_obj.east
    west = args_obj.west
    coords_or_tiles = args_obj.coords
    
    print("Performing search...")
    request_url = (
        "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/searchForFiles?"
        "products={}&"
        "startTime={}&"
        "endTime={}&"
        "north={}&"
        "south={}&"
        "east={}&"
        "west={}&"
        "coordsOrTiles={}&".format(products, start_time, end_time, north, south, east, west, coords_or_tiles)
        )
    print(request_url)
    response = request.urlopen(request_url)
    responseText = response.read().decode("utf-8")
    parsedResponse = xml.parse(responseText)
    
    for fileId in parsedResponse['mws:searchForFilesResponse']['return']:
        print(fileId)

    
elif (args_obj.mode == 'download'):
    if (args_obj.output == ''):
        file_name = "{}.hdf".format(time.strftime("%Y%m%d_%H_%M_%S"))
    else :
        file_name = args_obj.output
    print("file_name is {}".format(file_name))
    fileIds = args_obj.pid
    print("Downloading product {} into {}".format(args_obj.pid, file_name))

    # Get url of file of corresponding file ID
    url = "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getFileUrls?fileIds={}".format(fileIds)

    response_obj = getResponseDict(url)

    fileFtp = response_obj['mws:getFileUrlsResponse']['return']

    with request.urlopen(fileFtp) as response, open(file_name, 'wb') as out_file:
        data = response.read() 
        out_file.write(data)
    
print("Done.")