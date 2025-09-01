import numpy as np
import pandas as pd

COLUMNS = ["Time", "Oven", "Grill", "Microwave"]
INGREDIENTS = [f"Ing_{i}" for i in range(20)]
CRITERIA = INGREDIENTS + COLUMNS

# TODO: only load CRITERIA if nothing exists in database
df = pd.dataframe(columns=CRITERIA)
# TODO: otherwise load from database



        

