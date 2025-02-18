import requests
import pandas as pd
from decouple import config
from pathlib import Path


# Inputs set from .env
pat = config("PAT")
property_name = config("property_name")
start_date = config("start_date")
end_date = config("end_date")

# Set the name for the csv file to be exported at the end of the process
export_name = f"export_{start_date}_to_{end_date}"

# Get property ID
token = "Bearer " + pat

url = "https://public.api.hospitable.com/v2/properties"

headers = {
    "Content-Type": "",
    "Accept": "application/json",
    "Authorization": token
}
response = requests.get(url, headers=headers)

properties_list_json = response.json()

for p in properties_list_json['data']:
    if p['name'] == property_name:
        property_id = p['id']

# Get reservations data with financials using the property ID
url = "https://public.api.hospitable.com/v2/reservations"

querystring = {"per_page":"100","properties[]":property_id,"start_date":start_date,"end_date":end_date,"include":"financials"}

headers = {
    "Content-Type": "",
    "Accept": "application/json",
    "Authorization": token
}

response = requests.get(url, headers=headers, params=querystring)

reservations_json = response.json()

# Create a dictionary of reservations dictionaries with the data points of interest
reservations_dict = {}

for r in reservations_json['data']:
    status = r["reservation_status"]["current"]["category"]
    if status == "accepted":
        id = r["code"]
        platform = r["platform"]
        booked_date = r["booking_date"]
        check_in = r["check_in"]
        check_out = r["check_out"]
        nights = r["nights"]
        accom = r["financials"]["host"]["accommodation"]["amount"]
        revenue = r["financials"]["host"]["revenue"]["amount"]

        guest_fees = 0
        for g in r["financials"]["host"]["guest_fees"]:
            guest_fees += g["amount"]

        host_fees = 0
        for h in r["financials"]["host"]["host_fees"]:
            host_fees += h["amount"]

        discounts = 0
        for d in r["financials"]["host"]["discounts"]:
            discounts += d["amount"]

        adjustments = 0
        for a in r["financials"]["host"]["adjustments"]:
            adjustments += a["amount"]

        taxes = 0
        for t in r["financials"]["host"]["taxes"]:
            taxes += t["amount"]
        
        reservation_data_dict = {"id":id, "platform":platform, "booked_date":booked_date, "check_in":check_in, "check_out":check_out, "nights":nights, "accom":accom,"guest_fees":guest_fees ,"discounts":discounts,"adjustments":adjustments, "taxes":taxes, "host_fees":host_fees, "revenue":revenue,}
        
        reservations_dict[id] = (reservation_data_dict)

# Create a pandas dataframe from the reservations dictionary
reservations_df = pd.DataFrame.from_dict(reservations_dict, orient="index")

# Convert the amounts into dollars as they are currently stored as cents
reservations_df[["accom","discounts","host_fees","revenue","guest_fees","taxes","adjustments"]] = reservations_df[["accom","discounts","host_fees","revenue","guest_fees","taxes","adjustments"]].div(100)

# Format the date columns
date_cols = ['booked_date', 'check_in','check_out']
for d in date_cols:
    reservations_df[d] = reservations_df[d].str.slice(stop=10)
    reservations_df[d] = pd.to_datetime(reservations_df[d], format="%Y-%m-%d")

# Sort the dataframe by check-in date
reservations_df.sort_values(by=["check_in"])

# Create the output
Path("output").mkdir(parents=True, exist_ok=True)
reservations_df.to_csv(f"output/{export_name}.csv",index=False)