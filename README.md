# Hospitable Financial Exporter
This is a Python script to export financial data from Hospitable to a `.csv` file for a given date range.

## How it works
The `main.py` file is a python script that runs using a PAT generated from Hospitable to retrieve the financial data for a date range the you specify. It will then output this data into a .csv file for you to use.
Once the requirements have been met (below) simply run the `main.py` file and your csv will be created in an `output` directory.
The script is using the Hospitable Public API v2.

## Requirements
1. Python is installed
2. The packages per the `requirements.txt` file are installed. There are plenty of guides online explaining how to install packages from a  `requirements.txt` file, but if you wish to do this manually the key packages used are; `pandas`, `requests`, and `python-decouple`, along with each of their associated dependencies.
3. A .env file is created to supply the necessary inputs (further details on this are below)

## Creating the .env file
The `.env` file is where you specify the variables to be used by the script. You need to either create this file manually and add the variables listed below, or run the script once and it will create the `.env` file for you, after which you need to update the variables.

### Variables required in the `.env` file

```
PAT = 'abc123-YourPAT'
UUID = 'xyz789-YourUUID'
START_DATE = '2024-07-01'
END_DATE = '2025-06-30'
```

#### Description of each variable
`PAT` This is your personal access token from Hospitable. Please follow the [instructions](https://help.hospitable.com/en/articles/8609392-accessing-the-public-api-with-a-personal-access-token) provided by Hospiable for creating a PAT. Note that only **Read** permissions are required for this script.

`UUID` This is the unique ID for your Hospitable property. You can obtain this from Hospitable by navigating to **Properties > Name of your property > Details > Scroll to the bottom of the page**.

`START_DATE` This is the start of the date range that you wish to use for this script. The date format must be `'yyyy-mm-dd'`.

`END_DATE` This is the start of the date range that you wish to use for this script. The date format must be `'yyyy-mm-dd'`.

### Optional variables
In addition to the four required variables listed above, you may also supply the following optional variables.
`DEBUG` Set this to either `'True'` or `'False'`. Setting to `'True'` will run the script in debug mode which will result in more details being added to the `log.txt` file.

### Date Ranges
This script currenrly only uses the **Check-In date** for the date range, however in the future I will add the option to use the **Reservation date**.

## Output
The script produces a `.csv` file in a folder called `output`. The `.csv` will be named based on the date range you provided in the `.env` file.

### Output fields
The fields included in the `.csv` file are:
1. `id` This is the reservation ID.
2. `platform` The booking platform (e.g. airbnb).
3. `booked_date` The date the booking was made.
4. `check_in` The check-in date for the booking.
5. `check_out` The check-out date for the booking.
6. `nights` The number of nights booked.
7. `accom` The accommodation cost paid to the host.
8. `guest_fees` The fees paid to the host.
9. `discounts` The value of any discounts applied (from the perspective of the host).
10. `adjustments` The value of any adjustments applied (from the perspective of the host).
11. `taxes` The value of any taxes applied (from the perspective of the host).
12. `host_fees` The value of any host fees applied (from the perspective of the host).
13. `revenue` The revenue the host made from the booking. This should be the sum of fields 7 to 12.