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
        'Bettendorf',
        'Boise',
        'Chesterfield',
        'Chicago',
        'Coeur d\'Alene',
        'Coeur dAlene',
        'Crystal Lake',
        'De Pere',
        'Eau Claire',
        'Elgin',
        'Geneva',
        'Iowa City',
        'Janesville',
        'LaCrosse',
        'Lake Geneva',
        'Mequon',
        'Meridian',
        'Nampa',
        'Oakville',
        'Pewaukee',
        'Rolling Meadows',
        'St. Cloud',
        'Urbandale',
        'Warrenville',
        'Weldon Spring',
        'West Madison',
        'Geneva/St.Charles',
        'Warrenville/Naperville',
        'Chicago/Irving Park'
    ]

def map_location_name(location):
    """Map location names to their standardized forms"""
    location_mapping = {
        'Geneva/St.Charles': 'Geneva',
        'Warrenville/Naperville': 'Warrenville',
        'Chicago/Irving Park': 'Chicago',
        'Coeur dAlene': 'Coeur d\'Alene'
    }
    return location_mapping.get(location, location)

def get_leads_for_month(sf, start_date, end_date):
    valid_locations = get_valid_locations()
    # Escape single quotes in location names
    escaped_locations = [loc.replace("'", "\\'") for loc in valid_locations]
    location_filter = "', '".join(escaped_locations)
    
    # Update query to include Status field and filter by correct API names
    query = f"""
    SELECT 
        Id,
        CreatedDate, 
        Media_Location_Text__c,
        Status
    FROM Lead
    WHERE 
        CreatedDate >= {start_date} AND 
        CreatedDate <= {end_date} AND
        Media_Location_Text__c IN ('{location_filter}') AND
        Status IN ('Unqualified Lead', 'Converted', 'Client Registration', 'TOF Waitlist', 'Future Prospect', 'Prospect Connect')
    ORDER BY 
        CreatedDate ASC
    """
    
    try:
        result = sf.query_all(query)
        df = pd.DataFrame(result['records'])
        if not df.empty:
            # Add a count column for aggregation
            df['Leads'] = 1
            # Map location names to standardized forms
            df['Media_Location_Text__c'] = df['Media_Location_Text__c'].apply(map_location_name)
            # Ensure Id is preserved
            if 'Id' in df.columns:
                df = df[['Id', 'CreatedDate', 'Media_Location_Text__c', 'Status', 'Leads']]
        return df
    except Exception as e:
        print(f"Query error: {str(e)}")
        return pd.DataFrame()

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
    
    # Initialize empty list to store all DataFrames
    all_dfs = []
    
    # Query each month and combine results
    for start_date, end_date in get_date_ranges(prediction_month):
        query_results = get_leads_for_month(sf, start_date, end_date)
        if not query_results.empty:
            all_dfs.append(query_results)
    
    if not all_dfs:
        print("No data retrieved from Salesforce")
        return None, "No data retrieved from Salesforce"
    
    # Combine all DataFrames
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove the extra 'attributes' column if present
    if 'attributes' in df.columns:
        df = df.drop(columns='attributes')
    
    # Filter for only Leads (Future Prospect, Converted, Client Registration, TOF Waitlist)
    df = df[df['Status'].isin(['Future Prospect', 'Converted', 'Client Registration', 'TOF Waitlist'])]
    
    # Group by date and location
    df['day_created'] = pd.to_datetime(df['CreatedDate']).dt.date
    
    # Aggregate counts by date and location while preserving Id
    result_df = df.groupby(['day_created', 'Media_Location_Text__c', 'Id'])['Leads'].sum().reset_index()
    
    print("\nGrouped lead counts by location & date:")
    print(result_df)
    
    # Save Results to CSV
    output_file = "leads_by_location_date.csv"
    result_df.to_csv(output_file, index=False)
    print(f"\nSaved results to {output_file}")
    
    return output_file, None