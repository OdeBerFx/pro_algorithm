from functions.make_tables import *
from functions.manipulate_tables import *


def main(rides_path, drivers_path):
    """
    get paths to the rides and drivers jsons. check all possible rides and drivers combinations.
    assign optimal rides to drivers by location and duration. get cost of the rides, of the routes in between
    the rides, and back home. create dict of the final result.
    :param rides_path: str of path to rides json.
    :param drivers_path: str of path to drivers json.
    :return: dict of drivers with their assigned rides, and the final total cost.
    """

    print("starting function main")
    rides_df = create_riders_df(rides_path)
    drivers_df = create_drivers_df(drivers_path)

    closest_rides = create_all_combinations_df(rides_df, drivers_df)
    in_between_cost, final_chosen_rides = assign_rides(closest_rides)
    final_rides_cost, final_chosen_rides = get_final_rides(final_chosen_rides)
    back_home_cost = get_return_home_cost(final_chosen_rides)

    final_cost = in_between_cost + final_rides_cost + back_home_cost
    final_result = make_final_result(final_chosen_rides, final_cost)
    return final_result


if __name__ == '__main__':
    final_result_dict = main(RIDES_JSON_PATH, DRIVERS_JSON_PATH)
    print("final result:", final_result_dict)
