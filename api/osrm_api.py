from settings.constants import *

BASE_URL = "http://router.project-osrm.org"


def get_fastest_route_details(profile, coords_list):
    """
    create a str from the coords_list for the api query param. try max of 3 times to get the fastest route
    using osrm api. if works - get the distance and duration. else - wait a minute and try again. if api
    fails three times, return none.
    :param profile: str of mode of transportation.
    :param coords_list: list of coordinates.
    :return: list of distance and list of duration of fastest route, else none.
    """

    tries_amount = 0

    pattern = f"[{re.escape('[] ')}]"
    coords_str = ";".join(re.sub(pattern, "", str(coords)) for coords in coords_list)

    url = f"{BASE_URL}/route/v1/{profile}/{coords_str}"
    while tries_amount < 3:
        response = requests.get(url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            distance_in_meters = [response_json["routes"][0]["legs"][i]["distance"]
                                  for i in range(len(response_json["routes"][0]["legs"]))]
            duration_in_seconds = [response_json["routes"][0]["legs"][i]["duration"]
                                   for i in range(len(response_json["routes"][0]["legs"]))]
            return distance_in_meters, duration_in_seconds
        else:
            print(f"Exception in function 'get_fastest_route': {response.text}")
            tries_amount += 1
            time.sleep(60)  # sleep for a minute
    return None, None
