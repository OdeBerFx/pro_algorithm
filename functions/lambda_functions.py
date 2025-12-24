from settings.constants import *


def check_arrival_time(row, summ):
    """
    if current_time isn't none, calculate and return if the driver can reach the ride in time. else - True.
    :param row: series of a row from a dataframe.
    :param summ: bool of whether to summarize the duration.
    :return: True if the driver can make it in time to the ride, else False.
    """

    if row["current_time"]:
        row_duration = sum(row["duration"]) if summ else row["duration"]
        arrival_time = row["current_time"] + timedelta(seconds=row_duration)
        if arrival_time <= row["startTime"]:
            return True
        return False
    return True


def calculate_route_cost(row):
    """
    convert distance from meters to km, and duration from seconds to hours.
    calculate the cost for a driver to make a trip, by the cost of fuel, and the cost of the driver's time.
    :param row: series of a row from a dataframe.
    :return: float of final cost to make a trip.
    """

    fuel_cost = (row["distance"] / 1000) * row["fuelCost"]

    if row["current_time"]:  # has time - by startTime to current_time
        time_in_seconds = (row["startTime"] - row["current_time"]).seconds
    else:  # no time constraints - by duration to start of route
        time_in_seconds = row["duration"]
    time_in_hours = time_in_seconds / (60 * 60)
    time_cost = time_in_hours * 30

    final_cost = round(fuel_cost + time_cost, 2)
    return final_cost
