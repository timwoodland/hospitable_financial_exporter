import requests
import pandas as pd
from decouple import config
from pathlib import Path
import os
import logging
from datetime import datetime

# Inputs set from .env
PAT = config("PAT", default="", cast=str)
TOKEN = "Bearer " + config("PAT", default="", cast=str)
PROPERTY_NAME = config("PROPERTY_NAME", default="", cast= str, )
START_DATE = config("START_DATE", default="", cast=str)
END_DATE = config("END_DATE", default="", cast=str)
DEBUG = config("DEBUG", default=False, cast=bool)

# set basic logging config. Add level=logging.DEBUG for debugging
os.makedirs("./logs", exist_ok=True)

if DEBUG == True:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(
    level=log_level,
    format="{asctime} - {levelname} - {message}", 
    style="{", datefmt="%Y-%m-%d %H:%M",
    handlers=[
        logging.FileHandler(filename="./logs/log.txt", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
    )

def validate_inputs(pat, property_name, start_date, end_date, debug):
    try:
        errors = 0

        if (not os.path.isfile("./.env")):
            logging.error("The '.env' file is missing so one has been created. Please populate the variables within the '.env' file that are required for this script.")
            errors =+ 1
            # as the .env does not exist, create one as a template
            with open(".env", "w+") as f:
                f.write("PAT = 'xxx'\nPROPERTY_NAME = 'xxx'\nSTART_DATE = 'yyyy-mm-dd'\nEND_DATE = 'yyyy-mm-dd'\n\n# DEBUG = 'False'\n# Set to 'True' if more debugging detail in the 'log.txt' file is required.")

        if len(pat) == 0:
            logging.error("The PAT variable has a lenght of zero. Please check that a valid PAT variable has been supplied in the '.env' file.")
            errors =+ 1
        
        if len(property_name) == 0:
            logging.error("The PROPERTY_NAME variable has a lenght of zero. Please check that a valid PROPERTY_NAME variable has been supplied in the '.env' file.")
            errors =+ 1

        if type(debug) is not bool:
            logging.error(f"The DEBUG variable of `{debug}` is invalid. Please ensure that the DEBUG variable in the '.env' file is set to 'True' or 'False', or is removed altogether.")
            errors =+ 1

        # check date format
        format = "%Y-%m-%d"

        start_ok = True
        end_ok = True

        try:
            start_ok = bool(datetime.strptime(start_date, format))
        except:
            start_ok = False

        try:
            end_ok = bool(datetime.strptime(end_date, format))
        except:
            end_ok = False

        if (not start_ok):
            logging.error(f"The START_DATE variable of `{start_date}` is invalid. Please ensure that the START_DATE variable is correctly set in the '.env' file using the format 'yyyy-mm-dd' and as a string.")
            errors =+ 1

        if (not end_ok):
            logging.error(f"The END_DATE variable of `{end_date}` is invalid. Please ensure that the END_DATE variable is correctly set in the '.env' file using the format 'yyyy-mm-dd' and as a string.")
            errors =+ 1

        return errors
    
    except:
        logging.error("Validating the inputs from the '.env' file failed. Check the 'log.txt' file for more details.", exc_info=True)

def get_property_id(token, property_name):
    try:
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
        
        logging.debug("get_property_id() completed successfully.")
        
        return property_id
    
    except:
        logging.error("Getting the propertyID from Hospitable failed. Check the 'PAT' and 'PROPERTY_NAME' variables in the '.env' file.", exc_info=True)


def get_reservation_data(token, start_date, end_date, property_id):
    try:
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

        #TODO if DEBUG is  True, output this JSON to a file for review

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
    
        logging.debug("get_reservations_data() completed successfully.")

        return reservations_dict

    except:
        logging.error("Getting the reservations data from Hospitable failed. Check the 'log.txt' file for more details.", exc_info=True)


def create_dataframe(reservations_dict):
    try:
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

        logging.debug("create_dataframe() completed successfully.")

        return reservations_df

    except:
        logging.error("creation of Pandas dataframe failed", exc_info=True)


def create_output(reservations_df, start_date, end_date):
    try:
        export_name = f"export_{start_date}_to_{end_date}"
        
        Path("output").mkdir(parents=True, exist_ok=True)
        
        reservations_df.to_csv(f"output/{export_name}.csv",index=False)

        logging.debug("create_output() completed successfully.")
        logging.info(f"'{export_name}.csv' successfully created in the output directory.")

        return export_name
    
    except:
        logging.error("export of csv file failed. Check the 'log.txt' file for more details", exc_info=True)

def main():
    try:
        logging.debug("START: main() has started...")

        error_count = validate_inputs(PAT, PROPERTY_NAME, START_DATE, END_DATE, DEBUG)

        if error_count > 0:
            logging.error(f"END: Inputs from the '.env' file are invalid. {error_count} error(s) identified. Check the 'log.txt' file for more details.", exc_info=True)
            return
        
        property_id = get_property_id(TOKEN, PROPERTY_NAME)

        reservations_dict = get_reservation_data(TOKEN, START_DATE, END_DATE, property_id)

        reservations_df = create_dataframe(reservations_dict)

        export_name = create_output(reservations_df, START_DATE, END_DATE)

        logging.debug("END: main() completed successfully.")

    except:
        logging.error("END: the main() function has failed. Check the 'log.txt' file for more details", exc_info=True)

if __name__ == "__main__":
    main()