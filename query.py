from simple_salesforce import Salesforce
import pandas as pd

def get_salesforce_auth(username, password, security_token):
    """Authenticate to Salesforce with provided credentials"""
    try:
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain='login'
        )
        print(f"Authenticated as user: {sf.user_id}")
        return sf, None
    except Exception as e:
        error_message = str(e)
        print(f"Authentication error: {error_message}")
        return None, error_message

def get_valid_locations():
    return [
        'Ankeny',
        'Beloit',
        'Bettendorf',
        'Boise',
        'Chicago',
        'Coeur d\'Alene',
        'Crystal Lake',
        'Eau Claire',
        'Elgin',
        'Fond du Lac',
        'Geneva',
        'Iowa City',
        'Lake Geneva',
        'Meridian',
        'Moorhead',
        'Nampa',
        'Rolling Meadows',
        'Spokane',
        'Urbandale',
        'Warrenville',
        'Weldon Spring',
        'West Madison'
    ]

def get_leads_for_month(sf, start_date, end_date):
    valid_locations = get_valid_locations()
    # Escape single quotes in location names
    escaped_locations = [loc.replace("'", "\\'") for loc in valid_locations]
    location_filter = "', '".join(escaped_locations)
    
    soql_query = f"""
    SELECT
        Media_Location_Text__c,
        DAY_ONLY(pi__created_date__c) day_created,
        COUNT(Id) lead_count
    FROM Lead
    WHERE pi__created_date__c >= {start_date}
        AND pi__created_date__c < {end_date}
        AND Media_Location_Text__c IN ('{location_filter}')
    GROUP BY Media_Location_Text__c, DAY_ONLY(pi__created_date__c)
    ORDER BY Media_Location_Text__c, DAY_ONLY(pi__created_date__c)
    """
    print(f"Querying data for period: {start_date} to {end_date}")
    return sf.query(soql_query)

def get_date_ranges(prediction_month=None):
    # Get target month for prediction
    if prediction_month is None:
        current_date = pd.Timestamp.now()
    else:
        current_date = pd.Timestamp(prediction_month)
    
    current_month_start = current_date.strftime('%Y-%m-01T00:00:00Z')
    next_month = (current_date + pd.DateOffset(months=1))
    next_month_start = next_month.strftime('%Y-%m-01T00:00:00Z')
    
    # Generate all months from Jan 2023 to prediction month
    date_range = pd.date_range(start='2023-01-01', 
                             end=current_date, 
                             freq='MS')
    
    ranges = []
    for date in date_range:
        start = date.strftime('%Y-%m-01T00:00:00Z')
        end = (date + pd.DateOffset(months=1)).strftime('%Y-%m-01T00:00:00Z')
        ranges.append((start, end))
    
    return ranges

def get_salesforce_data(username, password, security_token, prediction_month=None):
    # Get Salesforce connection
    sf, error = get_salesforce_auth(username, password, security_token)
    
    if sf is None:
        return None, error
    
    # Initialize empty list to store all records
    all_records = []
    
    # Query each month and combine results
    for start_date, end_date in get_date_ranges(prediction_month):
        query_results = get_leads_for_month(sf, start_date, end_date)
        all_records.extend(query_results['records'])
    
    # Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    # Remove the extra 'attributes' column if present
    if 'attributes' in df.columns:
        df = df.drop(columns='attributes')
    
    print("\nGrouped lead counts by location & date:")
    print(df)
    
    # Save Results to CSV
    output_file = "leads_by_location_date.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved results to {output_file}")
    
    return output_file, None 