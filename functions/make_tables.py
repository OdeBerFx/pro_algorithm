from settings.constants import *


def open_json(path):
    """
    open json file if exists.
    :param path: str of file path
    :return: json of the file, or None if there are errors.
    """

    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                return json_data
        except Exception as e:
            print(f"Exception in function 'open_json': {e}")
            return None
    else:
        print("Exception in function 'open_json': path doesn't exist")
        return None


def create_df_from_file(path):
    """
    create a df from the given path. expecting a path to a json file.
    if the function open_json returns None, the function returns None as well.
    :param path: str of file path
    :return: df of given json file
    """

    json_obj = open_json(path)
    if json_obj:
        df = pd.DataFrame(json_obj)
        return df
    return None


def create_riders_df(path):
    """
    prepare a dataframe of all the rides.
    :param path: str of path to the rides json file.
    :return: dataframe of all the rides.
    """

    df = create_df_from_file(path)
    df["startTime"] = df.apply(lambda row: datetime.strptime(f"{row['date']} {row['startTime']}", "%Y-%m-%d %H:%M"), axis=1)
    df["endTime"] = df.apply(lambda row: datetime.strptime(f"{row['date']} {row['endTime']}", "%Y-%m-%d %H:%M"), axis=1)
    df = df.sort_values('startTime')
    df["startPoint_coords"] = df["startPoint_coords"].astype(str)
    df["endPoint_coords"] = df["endPoint_coords"].astype(str)
    df["temp_id"] = 0
    return df


def create_drivers_df(path):
    """
    prepare a dataframe of all the drivers.
    :param path: str of path to the drivers json file.
    :return: dataframe of all the drivers.
    """

    df = create_df_from_file(path)
    df["city_coords"] = df["city_coords"].astype(str)
    df["current_coords"] = df["city_coords"]
    df["current_time"] = None
    df["temp_id"] = 0
    return df


def create_all_combinations_df(rides_df, drivers_df):
    """
    prepare a dataframe of all the possible driver and rides combinations by merging rides_df and drivers_df and
    removing rows with too many seats for the driver.
    :param rides_df: dataframe of all the possible rides.
    :param drivers_df: dataframe of all the drivers.
    :return: dataframe of all the possible rides for each driver to make.
    """

    closest_rides = pd.merge(drivers_df, rides_df, on="temp_id", how="outer")
    closest_rides.drop(['temp_id', 'firstName', 'lastName', 'mainPhone', 'status', 'licenceDegree', 'date', 'city',
                        'startPoint', 'endPoint'], axis=1, inplace=True)
    # remove combinations of drivers and rides that are irrelevant because of number of seats.
    closest_rides.drop([i for i, row in closest_rides.iterrows() if row["numberOfSeats_y"] > row["numberOfSeats_x"]],
                       axis=0, inplace=True)
    return closest_rides


def pick_chosen_rides(closest_rides):
    """
    find the optimal next ride for each driver. check by smallest cost to get to the start of the ride.
    if more than one driver has the same most optimal next ride, assign it to the first driver, and look for the
    next best alternative for the other drivers, until there is no competition between the drivers.
    :param closest_rides: dataframe of drivers and rides matches.
    :return: dataframe of the next best ride for each driver to make.
    """

    chosen_rides = pd.DataFrame(columns=closest_rides.columns)

    # continue until there is no competition, then move to next stop
    while len(closest_rides) > 0:
        # from closest_rides, leave combinations for drivers that don't already have a chosen next ride.
        top_picks = closest_rides[~closest_rides["driverId"].isin(list(chosen_rides["driverId"]))].drop_duplicates(
            subset="driverId")
        top_picks.sort_values(by=["_id", "cost_to_route_start"], ascending=True, inplace=True)

        # check if drivers are competing for the next ride.
        top_picks["duplicate"] = top_picks.duplicated(subset="_id", keep="first")
        no_competition = top_picks[top_picks["duplicate"] == False]
        # save driver and rides combinations that don't have competition.
        if chosen_rides.empty:
            chosen_rides = no_competition
        else:
            chosen_rides = pd.concat([chosen_rides, no_competition])

        # remove rides that are taken by other drivers
        closest_rides.drop([i for i, row in closest_rides.iterrows() if row["_id"] in list(no_competition["_id"])],
                           axis=0, inplace=True)

        # end search of next ride for the drivers once there is no competition
        competition = top_picks[top_picks["duplicate"] == True]
        if len(competition) == 0:
            break

    return chosen_rides
