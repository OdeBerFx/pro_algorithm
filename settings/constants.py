import json
import os
import requests
import pandas as pd
import re
from datetime import datetime, timedelta
import time


DRIVERS_JSON_PATH = r"jsons/drivers.json"
RIDES_JSON_PATH = r"jsons/rides.json"
