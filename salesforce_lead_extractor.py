from simple_salesforce import Salesforce
import pandas as pd
import os
import configparser
from dotenv import load_dotenv

def get_credentials_from_ini():
    """
    Read Salesforce credentials from credentials.ini file
    
    Returns:
    - tuple: (username, password, security_token) or (None, None, None) if file not found
    """
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.ini')
    
    if os.path.exists(ini_path):
        try:
            config.read(ini_path)
            if 'salesforce' in config:
                username = config['salesforce'].get('username')
                password = config['salesforce'].get('password')
                security_token = config['salesforce'].get('security_token')
                
                if all([username, password, security_token]):
                    print(f"Credentials loaded from credentials.ini")
                    return username, password, security_token
                else:
                    print("Credentials in credentials.ini are incomplete")
            else:
                print("No 'salesforce' section found in credentials.ini")
        except Exception as e:
            print(f"Error reading credentials.ini: {str(e)}")
    else:
        print(f"credentials.ini not found at {ini_path}")
    
    return None, None, None

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
    """Return the list of valid locations for filtering"""
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

def get_leads(sf, start_date=None, end_date=None, limit=None):
    """
    Get individual lead records from Salesforce
    
    Parameters:
    - sf: Salesforce connection object
    - start_date: Optional start date for filtering (format: YYYY-MM-DDT00:00:00Z)
    - end_date: Optional end date for filtering (format: YYYY-MM-DDT00:00:00Z)
    - limit: Optional limit on number of records to return
    
    Returns:
    - List of lead records
    """
    valid_locations = get_valid_locations()
    # Escape single quotes in location names
    escaped_locations = [loc.replace("'", "\\'") for loc in valid_locations]
    location_filter = "', '".join(escaped_locations)
    
    # Build WHERE clause based on provided parameters
    where_clauses = [f"Media_Location_Text__c IN ('{location_filter}')"]
    
    if start_date:
        where_clauses.append(f"CreatedDate >= {start_date}")
    
    if end_date:
        where_clauses.append(f"CreatedDate <= {end_date}")
    
    where_clause = " AND ".join(where_clauses)
    
    # Limit clause if provided
    limit_clause = f" LIMIT {limit}" if limit else ""
    
    # Query for individual leads with important fields
    query = f"""
    SELECT 
        Id,
        LastName,
        FirstName,
        Name,
        Email,
        Phone,
        MobilePhone,
        Company,
        Status,
        CreatedDate,
        LeadSource,
        Media_Location_Text__c,
        Title,
        Street,
        City,
        State,
        PostalCode,
        Country,
        Industry,
        Rating,
        IsConverted,
        ConvertedDate,
        UTM_Source__c,
        UTM_Medium__c, 
        UTM_Campaign__c,
        UTM_Content__c,
        UTM_Term__c,
        Client_Age__c,
        Child_DOB__c,
        Child_Name__c,
        Preferred_Location__c,
        Primary_Clinic__c,
        Lead_Source_Type__c,
        Lead_Origin__c,
        Referred_By__c,
        Insurance__c,
        Secondary_Insurance__c,
        Primary_Language__c,
        Interpreter_Needed__c,
        Preferred_Method_of_Contact__c
    FROM Lead
    WHERE {where_clause}
    ORDER BY CreatedDate ASC
    {limit_clause}
    """
    
    try:
        result = sf.query_all(query)
        if result['totalSize'] > 0:
            print(f"Retrieved {result['totalSize']} individual leads")
            return result['records']
        else:
            print("No leads found matching the criteria")
            return []
    except Exception as e:
        print(f"Query error: {str(e)}")
        return []

def clean_salesforce_records(records):
    """
    Clean Salesforce records by removing metadata and formatting
    
    Parameters:
    - records: List of Salesforce record dictionaries
    
    Returns:
    - List of cleaned record dictionaries
    """
    cleaned_records = []
    for record in records:
        # Remove the attributes dictionary that Salesforce includes
        if 'attributes' in record:
            record.pop('attributes')
        cleaned_records.append(record)
    
    return cleaned_records

def main():
    """Main function to execute when run as a script"""
    # First try to get credentials from credentials.ini
    username, password, security_token = get_credentials_from_ini()
    
    # If credentials.ini failed, try environment variables
    if not all([username, password, security_token]):
        # Try to load credentials from .env file if it exists
        load_dotenv(override=True)
        
        username = os.getenv('SF_USERNAME')
        password = os.getenv('SF_PASSWORD')
        security_token = os.getenv('SF_SECURITY_TOKEN')
        
        # If still not found, prompt user
        if not all([username, password, security_token]):
            print("Salesforce credentials not found in credentials.ini or environment variables.")
            username = input("Enter Salesforce username: ")
            password = input("Enter Salesforce password: ")
            security_token = input("Enter Salesforce security token: ")
    
    # Authenticate with Salesforce
    sf, error = get_salesforce_auth(username, password, security_token)
    
    if error:
        print(f"Error authenticating with Salesforce: {error}")
        return
    
    # Get time period from user (optional)
    use_date_filter = input("Do you want to filter by date? (y/n): ").lower() == 'y'
    start_date = None
    end_date = None
    
    if use_date_filter:
        start_year = input("Enter start year (YYYY): ")
        start_month = input("Enter start month (MM): ")
        start_date = f"{start_year}-{start_month}-01T00:00:00Z"
        
        end_year = input("Enter end year (YYYY): ")
        end_month = input("Enter end month (MM): ")
        # Calculate the first day of the next month as the end date
        if end_month == '12':
            next_year = str(int(end_year) + 1)
            next_month = '01'
        else:
            next_year = end_year
            next_month = str(int(end_month) + 1).zfill(2)
        
        end_date = f"{next_year}-{next_month}-01T00:00:00Z"
    
    # Ask for a limit to avoid overwhelming results
    limit_str = input("Enter maximum number of records to retrieve (leave blank for all): ")
    limit = int(limit_str) if limit_str.strip() else None
    
    # Get the leads
    print(f"Retrieving leads from Salesforce...")
    leads = get_leads(sf, start_date, end_date, limit)
    
    if not leads:
        print("No leads found or error occurred.")
        return
    
    # Clean the records
    cleaned_leads = clean_salesforce_records(leads)
    
    # Convert to DataFrame
    df = pd.DataFrame(cleaned_leads)
    
    # Display some information about the data
    print(f"\nRetrieved a total of {len(df)} individual leads")
    if not df.empty:
        print("\nColumns in the dataset:")
        print(df.columns.tolist())
        
        print("\nSample of the data (first 5 rows):")
        print(df.head(5))
    
    # Ask for output filename
    default_filename = "salesforce_leads.csv"
    output_file = input(f"Enter output filename (default: {default_filename}): ")
    if not output_file:
        output_file = default_filename
    
    # Ensure it has .csv extension
    if not output_file.endswith('.csv'):
        output_file += '.csv'
    
    # Save Results to CSV
    df.to_csv(output_file, index=False)
    print(f"\nSaved {len(df)} lead records to {output_file}")

if __name__ == "__main__":
    main() 