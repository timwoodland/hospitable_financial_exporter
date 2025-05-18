import requests
import pandas as pd
from decouple import config
from pathlib import Path
import os
import logging
from datetime import datetime
import json

# Inputs set from .env
PAT = config("PAT", default="", cast=str)
TOKEN = "Bearer " + config("PAT", default="", cast=str)
UUID = config("UUID", default="", cast= str)
START_DATE = config("START_DATE", default="", cast=str)
END_DATE = config("END_DATE", default="", cast=str)
DEBUG = config("DEBUG", default=False, cast=bool)
GNU = config("GNU", default=False, cast=bool)

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

def validate_inputs(pat, uuid, start_date, end_date, debug, gnu):
    try:
        errors = 0

        if (not os.path.isfile("./.env")):
            logging.error("The '.env' file is missing so one has been created. Please populate the variables within the '.env' file that are required for this script.")
            errors =+ 1
            # as the .env does not exist, create one as a template
            with open(".env", "w+") as f:
                f.write("PAT = 'abc123-YourPAT'\nUUID = 'xyz789-YourUUID'\nSTART_DATE = 'yyyy-mm-dd'\nEND_DATE = 'yyyy-mm-dd'\n\n# DEBUG = 'False'\n# Set to 'True' if more debugging detail in the 'log.txt' file is required.")

        if len(pat) == 0:
            logging.error("The PAT variable has a lenght of zero. Please check that a valid PAT variable has been supplied in the '.env' file.")
            errors =+ 1

        if len(uuid) == 0:
            logging.error("The UUID variable has a lenght of zero. Please check that a valid UUID variable has been supplied in the '.env' file.")
            errors =+ 1

        if type(debug) is not bool:
            logging.error(f"The DEBUG variable of `{debug}` is invalid. Please ensure that the DEBUG variable in the '.env' file is set to 'True' or 'False', or is removed altogether.")
            errors =+ 1

        if type(gnu) is not bool:
            logging.error(f"The GNU variable of `{gnu}` is invalid. Please ensure that the GNU variable in the '.env' file is set to 'True' or 'False', or is removed altogether.")
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


def get_reservation_data(token, start_date, end_date, property_id, debug):
    try:
        # Get reservations data with financials using the property ID
        url = "https://public.api.hospitable.com/v2/reservations"

        querystring = {"per_page":"100","properties[]":property_id,"date_query":"checkin","start_date":start_date,"end_date":end_date,"include":"financials"}

        headers = {
            "Content-Type": "",
            "Accept": "application/json",
            "Authorization": token
        }

        response = requests.get(url, headers=headers, params=querystring)

        reservations_json = response.json()

        # If debug is True, export raw json response
        if debug:
            try:
                Path("debug").mkdir(parents=True, exist_ok=True)
                with open(f"./debug/raw_{start_date}_to_{end_date}.json", "w+") as f:
                    f.write(json.dumps(reservations_json, indent=4))
                logging.debug(f"'raw_{start_date}_to_{end_date}.json' successfully created in the debug directory. This is the raw data obtained from the Hospitable API")
            except:
                logging.error("Unable to export the raw JSON data for debugging. Check the 'log.txt' file for more details.", exc_info=True)

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
        logging.error("Getting the reservations data from Hospitable failed. Check the all variables in the '.env' file are accurate. Check the 'log.txt' file for more details.", exc_info=True)


def create_reservations_dataframe(reservations_dict):
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
        reservations_df = reservations_df.sort_values(by=["check_in"])

        logging.debug("create_reservations_dataframe() completed successfully.")

        return reservations_df

    except:
        logging.error("creation of Pandas reservation data dataframe failed", exc_info=True)

def create_gnu_dataframe(reservations_df):
    try:
        # Create a dataframe using the initial reservations dataframe
        accounting_df = reservations_df.copy()
        accounting_df["accom"] = accounting_df["accom"] + accounting_df["discounts"] + accounting_df["taxes"]
        accounting_df["date"] = accounting_df["check_in"]
        accounting_df["description"] = accounting_df[["platform", "id"]].agg(" booking ".join, axis=1)
        accounting_df = accounting_df[["id", "date", "platform", "description", "accom", "guest_fees", "host_fees"]]

        # define function to add tax to booking.com host fees
        def add_tax(row):
            if row["platform"] == "booking":
                value = row["host_fees"] * 1.1
            else:
                value = row["host_fees"]

            return value
    
        
        # apply function to df to add tax to booking.com host fees
        accounting_df.loc[:,"host_fees"] = accounting_df.apply(add_tax, axis=1)         

        # define function to add receivable amount
        def add_receivable(row):
            if row["platform"] == "booking":
                value = row["accom"] + row["guest_fees"]
            else:
                value = row["accom"] + row["guest_fees"] + row["host_fees"]

            return value * -1
        
        # apply function to df to add receivable
        accounting_df.loc[:,("receivable")] = accounting_df.apply(add_receivable, axis=1)     

        # define function to add payable amount
        def add_payable(row):
            if row["platform"] == "booking":
                value = row["host_fees"]
            else:
                value = 0.0

            return value * -1
        
        # apply function to df to add receivable
        accounting_df.loc[:,("payable")] = accounting_df.apply(add_payable, axis=1)    

        # use pd.melt() to un-pivot the df, bring it closer to the required gnucash input format
        accounting_df_melt = pd.melt(accounting_df, id_vars=["id", "date", "platform", "description"], value_vars=["accom", "guest_fees", "host_fees", "receivable", "payable"])
        accounting_df_melt = accounting_df_melt.sort_values(by=["date","variable"])
        accounting_df_melt.reset_index(drop=True)

        accounting_df_melt = accounting_df_melt.drop(accounting_df_melt[accounting_df_melt["value"]==0].index)

        # define function to use to create account names in the df
        def add_account(row):
            if row["platform"] == "airbnb" and row["variable"] == "accom":
                value = "Income:Booking Income:AirBnb:Accommodation"
            elif row["platform"] == "airbnb" and row["variable"] == "guest_fees":
                value = "Income:Booking Income:AirBnb:Guest Fees"
            elif row["platform"] == "airbnb" and row["variable"] == "host_fees":
                value = "Expenses:Platform Fees and Subscriptions:Booking Platform Fees:AirBnb Fees"

            elif row["platform"] == "booking" and row["variable"] == "accom":
                value = "Income:Booking Income:Booking.com:Accommodation"
            elif row["platform"] == "booking" and row["variable"] == "guest_fees":
                value = "Income:Booking Income:Booking.com:Guest Fees"
            elif row["platform"] == "booking" and row["variable"] == "host_fees":
                value = "Expenses:Platform Fees and Subscriptions:Booking Platform Fees:Booking.com Fees"

            elif row["platform"] == "homeaway" and row["variable"] == "accom":
                value = "Income:Booking Income:Vrbo:Accommodation"
            elif row["platform"] == "homeaway" and row["variable"] == "guest_fees":
                value = "Income:Booking Income:Vrbo:Guest Fees"
            elif row["platform"] == "homeaway" and row["variable"] == "host_fees":
                value = "Expenses:Platform Fees and Subscriptions:Booking Platform Fees:Vrbo Fees"

            elif row["platform"] == "manual" and row["variable"] == "accom":
                value = "Income:Booking Income:Direct Booking:Accommodation"
            elif row["platform"] == "manual" and row["variable"] == "guest_fees":
                value = "Income:Booking Income:Direct Booking:Guest Fees"

            elif row["variable"] == "receivable":
                value = "Assets:Accounts Receivable"
            elif row["variable"] == "payable":
                value = "Liabilities:Accounts Payable"


            else:
                value = "unknown"
        
            return value
        
        # apply function to df to add account names
        accounting_df_melt["account"] = accounting_df_melt.apply(add_account, axis=1)

        logging.debug("create_gnu_dataframe() completed successfully.")

        return accounting_df_melt

    except:
        logging.error("creation of Pandas gnuCash dataframe failed", exc_info=True)

def create_reservations_output(reservations_df, start_date, end_date):
    try:
        export_name = f"reservations_export_{start_date}_to_{end_date}"
        
        Path("output").mkdir(parents=True, exist_ok=True)
        
        reservations_df.to_csv(f"output/{export_name}.csv",index=False)

        logging.debug("create_reservations_output() completed successfully.")
        logging.info(f"'{export_name}.csv' successfully created in the output directory.")

        return export_name
    
    except:
        logging.error("export of reservations csv file failed. Check the 'log.txt' file for more details", exc_info=True)

def create_gnu_output(gnu_df, start_date, end_date):
    try:
        export_name = f"gnu_export_{start_date}_to_{end_date}"
        
        Path("output").mkdir(parents=True, exist_ok=True)
        
        gnu_df.to_csv(f"output/{export_name}.csv",index=False)

        logging.debug("create_gnu_output() completed successfully.")
        logging.info(f"'{export_name}.csv' successfully created in the output directory.")

        return export_name
    
    except:
        logging.error("export of gnuCash csv file failed. Check the 'log.txt' file for more details", exc_info=True)

def main():
    try:
        logging.debug("START: main() has started...")

        error_count = validate_inputs(PAT, UUID, START_DATE, END_DATE, DEBUG, GNU)

        if error_count > 0:
            logging.error(f"END: Inputs from the '.env' file are invalid. {error_count} error(s) identified. Check the 'log.txt' file for more details.", exc_info=True)
            return

        reservations_dict = get_reservation_data(TOKEN, START_DATE, END_DATE, UUID, DEBUG)

        reservations_df = create_reservations_dataframe(reservations_dict)

        gnu_df = create_gnu_dataframe(reservations_df)

        create_reservations_output(reservations_df, START_DATE, END_DATE)

        if GNU:
            create_gnu_output(gnu_df, START_DATE, END_DATE)

        logging.debug("END: main() completed successfully.")

    except:
        logging.error("END: the main() function has failed. Check the 'log.txt' file for more details", exc_info=True)

if __name__ == "__main__":
    main()