from settings.constants import *
from api.osrm_api import *
from functions.lambda_functions import *
from functions.make_tables import *


def add_distance_and_duration(df, coords_columns_list, summ):
    """
    for each row in the df, calculate the distance and duration of the fastest route between the given coordinates,
    using osrm api.
    :param df: dataframe that needs distance and duration calculation.
    :param coords_columns_list: list of columns that have relevant coordinates for the calculation.
    :param summ: bool of whether to summarize columns.
    :return: original df with additional columns - distance and duration.
    """

    df["route_details"] = df.apply(lambda row: get_fastest_route_details("driving",
                                                                         [row[col] for col in coords_columns_list]),
                                                         axis=1)
    df[["distance", "duration"]] = pd.DataFrame(df["route_details"].tolist(), index=df.index)
    df.drop("route_details", axis=1, inplace=True)
    if summ:
        df["distance"] = df["distance"].apply(lambda d: sum(d))
        df["duration"] = df["duration"].apply(lambda d: sum(d))
    return df


def stop_at_home(closest_rides):
    """
    check if a driver can go home in between rides - in order to cut costs on paying for the driver's working hours.
    check by seeing if the driver can drive home and to the next ride in time. if yes, calculate the cost to
    send the driver home, and update the driver's location to their home and time to none.
    :param closest_rides: dataframe of drivers and rides matches.
    :return: float of the cost to send the drivers home, and the updated closest_rides.
    """

    home_cost = 0

    # check if driver can return home
    closest_rides = add_distance_and_duration(closest_rides, coords_columns_list=["current_coords", "city_coords", "startPoint_coords"],
                                              summ=False)

    # check if the driver can make it home and back to the start of the ride before the ride starts.
    closest_rides["can_go_home"] = closest_rides.apply(lambda row: check_arrival_time(row, summ=True), axis=1)
    go_home = closest_rides.loc[closest_rides["can_go_home"] == True]
    go_home = go_home.drop_duplicates(subset=["driverId"], keep="first")

    for i, row in go_home.iterrows():
        # calculate cost from current location to home
        route_home = {"distance": row["distance"][0], "fuelCost": row["fuelCost"], "current_time": None,
                      "duration": row["duration"][0]}
        cost_to_home = calculate_route_cost(route_home)
        home_cost += cost_to_home

        # update the time of the driver and their location - for next calculations.
        closest_rides.loc[closest_rides["driverId"] == row["driverId"], "current_coords"] = row["city_coords"]
        closest_rides.loc[closest_rides["driverId"] == row["driverId"], "current_time"] = None

    closest_rides.drop(["distance", "duration", "can_go_home"], axis=1, inplace=True)
    return home_cost, closest_rides


def assign_rides(closest_rides):
    """
    simultaneously assign best rides for drivers to make based on time, location, and cost.
    every time a driver is assigned a ride, remove the ride from the other drivers options.
    if more than one driver has the same most optimal next ride, assign it to the first driver, and look for the
    next best alternatives for the other drivers, until there is no competition between the drivers.
    in addition, check if the driver can return home to cut costs. if yes, send the driver home.
    calculate the total cost of all the trips in between rides - 'empty rides'.
    :param closest_rides: dataframe of drivers and rides matches.
    :return: float of cost of 'empty rides', and updated closest_rides.
    """

    final_chosen_rides = pd.DataFrame()
    home_cost = 0

    while len(closest_rides) > 0:
        # remove routes that already started
        closest_rides.drop(
            [i for i, row in closest_rides.iterrows() if row["current_time"] if row["startTime"] < row["current_time"]],
            axis=0, inplace=True)

        if len(closest_rides) == 0:
            break

        closest_rides = add_distance_and_duration(closest_rides, coords_columns_list=["current_coords", "startPoint_coords"],
                                                  summ=True)

        # remove rows where the driver can't get to the ride in time before it starts
        closest_rides["get_in_time"] = closest_rides.apply(lambda row: check_arrival_time(row, summ=False), axis=1)
        closest_rides.drop([i for i, row in closest_rides.iterrows() if row["get_in_time"] == False], axis=0, inplace=True)
        closest_rides.drop("get_in_time", axis=1, inplace=True)

        # get arrival to routes cost - by drivers time (now till start of route \ time to get there) + fuel cost (distance * fuelCost)
        closest_rides["cost_to_route_start"] = closest_rides.apply(calculate_route_cost, axis=1)
        closest_rides.sort_values(["driverId", "cost_to_route_start"], ascending=True, inplace=True)

        # get the optimal ride for each driver
        chosen_rides = pick_chosen_rides(closest_rides)

        final_chosen_rides = pd.concat([final_chosen_rides, chosen_rides])
        for i, row in chosen_rides.iterrows():
            # update the time of the driver and their location to the end of their optimal ride - for next calculation.
            closest_rides.loc[closest_rides["driverId"] == row["driverId"], "current_coords"] = row["endPoint_coords"]
            closest_rides.loc[closest_rides["driverId"] == row["driverId"], "current_time"] = row["endTime"]

        closest_rides.drop(["distance", "duration"], axis=1, inplace=True)

        if len(closest_rides) == 0:
            break

        # check if the drivers can be sent home in between rides.
        home_costs, closest_rides = stop_at_home(closest_rides)
        home_cost += home_costs

    final_cost = home_cost + sum(final_chosen_rides["cost_to_route_start"])
    return final_cost, final_chosen_rides


def get_final_rides(final_chosen_rides):
    """
    calculate the cost of all the final rides themselves.
    :param final_chosen_rides: dataframe of all the assigned rides to the drivers.
    :return: float of cost of all the rides, and updated final_chosen_rides.
    """

    final_chosen_rides["current_time"] = None
    final_chosen_rides.drop(['distance', 'duration', 'cost_to_route_start'], axis=1, inplace=True)
    final_chosen_rides = add_distance_and_duration(final_chosen_rides, coords_columns_list=["startPoint_coords", "endPoint_coords"],
                                                   summ=True)
    final_chosen_rides["route_cost"] = final_chosen_rides.apply(calculate_route_cost, axis=1)
    return sum(final_chosen_rides["route_cost"]), final_chosen_rides


def get_return_home_cost(final_chosen_rides):
    """
    from final_chosen_rides, keep only the drivers that aren't yet home after their last ride. calculate the cost
    to send these drivers home.
    :param final_chosen_rides: dataframe of all the assigned rides to the drivers.
    :return: float of cost to send drivers home at the end of their day.
    """

    # keep last ride of drivers that aren't yet home
    return_home = final_chosen_rides.loc[final_chosen_rides["city_coords"] != final_chosen_rides["current_coords"]]
    return_home = return_home.drop_duplicates(subset="driverId", keep="last", inplace=False)
    return_home.drop(['distance', 'duration', 'route_cost'], axis=1, inplace=True)
    return_home = add_distance_and_duration(final_chosen_rides, coords_columns_list=["current_coords", "city_coords"],
                                            summ=True)
    return_home["route_cost"] = return_home.apply(calculate_route_cost, axis=1)
    return sum(return_home["route_cost"])


def make_final_result(final_chosen_rides, final_cost):
    """
    create a dict from the drivers and their assigned rides, and the final cost.
    :param final_chosen_rides: dataframe of all the assigned rides to the drivers.
    :param final_cost: float of final total cost - rides, in between rides, and sending drivers home.
    :return: dict of final result - all the drivers with their assigned rides and the final total cost.
    """

    final_result = {"assignments": [], "totalCost": final_cost}

    drives_dict = final_chosen_rides.groupby("driverId")["_id"].apply(list).to_dict()
    for driver, rides in drives_dict.items():
        driver_d = {"driverId": driver, "rideIds": rides}
        final_result["assignments"].append(driver_d)
    return final_result
