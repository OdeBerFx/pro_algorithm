# **pro_algorithm**

Interview assignment for Pro Algorithm: assign drivers to rides.

### **Code Flow:**
- Using pandas library, create dataframes of all the rides and drivers.
- Create a dataframe of all the possible combinations between drivers and rides, and remove irrelevant combinations based on seats.
- Iterate over the combinations dataframe to find the most optimal next ride for each driver, based on location, time, and cost.
- If more than one driver has the same next optimal ride, pick the next best one so that rides aren't repeated.
- Once the next ride is chosen for each driver, save the rides in a dedicated dataframe, remove the rides from the combinations options, and update the drivers location and time to the end point of their ride.
- If a driver can be sent home in between rides, update their location to their home in order to save cost on drivers working hours.
- Calculate the cost of all: the final rides, the drivers trips in between rides, and the drivers trips to their home in between rides and at the end of the day.
- Create a dictionary of the final result containing: all the drivers and their rides, and the final total cost.

### **Code Decisions:**
- OSRM api: Repeated requests in order to get the most accurate calculations. Did not use ariel distance because it's not accurate - ariel distance may differ greatly from actual road route. In addition, repeated api requests that had same coordinates because the order may make a difference in the route to and from, because of road constrictions.
- Did not calculate all possible routes to begin with - would greatly increase api requests and calculations much more than necessary.
- Home: Sent drivers home in between rides to save cost on their working hours. The placement of the 'stop_at_home' function is at the end of each ride calculation because it wasn't as effective when placed elsewhere in the code flow.

### **Possible Changes:**
- Implement geopandas library in order to minimize use of OSRM api - use geopandas distance to optimize api use and requests.
- Find a shp file of the routes and their details in the areas of the rides instead of using OSRM api.
- Save previous calculations of routes in order to not calculate routes more than once.
- Check if the cost to send a driver home in between rides is less than the cost to go straight to the next ride.
