# Hospitable Financial Exporter
This is a Python script to export financial data from Hospitable to csv for a given date range.

## How it works
The `main.py` file is a python script that runs using a PAT generated from Hospitable to retrieve the financial data for a date range the you specify. It will then output this data into a .csv file for you to use.
Once the requirements have been met (below) simply run the `main.py` file and your csv will be created in an `output` directory.

## Requirements
1. Python is installed
2. The packages per the `requirements.txt` file are installed
3. A .env file is created to supply the necessary inputs (further details on this are below)

## Creating the .env file
The `.env` file is where you specify the variables to be used by the script. You need to either create this file manually and add the variables listed below, or run the script once and it will create the `.env` file for you, after which you need to update the variables.

### Variables required in the `.env` file

```
PAT = 'abc123-MYPAT'
PROPERTY_NAME = 'The Beach House, Dunsborough, Western Australia'
START_DATE = '2024-07-01'
END_DATE = '2025-06-30'
```

#### Description of each variable
`PAT` This is your personal access token from Hospitable. Please follow the [instructions](https://help.hospitable.com/en/articles/8609392-accessing-the-public-api-with-a-personal-access-token) provided by Hospiable for creating a PAT. Note that only Read permissions are required for this script.

`PROPERTY_NAME` This

`START_DATE` This is the start of the date range that you wish to use for this script. The date format must be `'yyyy-mm-dd'`.

`END_DATE` This is the start of the date range that you wish to use for this script. The date format must be `'yyyy-mm-dd'`.

#### Optional variables
In addition to the four required variables listed above, you may also supply the following optional variables.
`DEBUG` Set this to either `'True'` or `'False'`. Setting to `'True'` will run the script in debug mode which will result in more details being added to the `log.txt` file.
