import streamlit as st
import pandas as pd
from query import get_salesforce_data
from forecast import forecast_leads
import zipfile
import os
from datetime import datetime
import io
import configparser
import os.path

def create_download_zip(forecast_results, visuals_dir):
    """Create a ZIP file containing forecast results and visualizations"""
    with io.BytesIO() as zip_buffer:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add forecast results CSV
            results_csv = forecast_results.to_csv(index=False)
            zip_file.writestr('forecast_results.csv', results_csv)
            
            # Add visualizations only for the locations in forecast_results
            for location in forecast_results['Location'].unique():
                image_path = f"{visuals_dir}/{location}_forecast.png"
                if os.path.exists(image_path):
                    zip_file.write(image_path, os.path.basename(image_path))
        
        return zip_buffer.getvalue()

def generate_chain_forecast(output_file, selected_date, selected_location, adjustment_factor: float = 1.0):
    """Generate forecasts for future months by creating a chain of predictions"""
    # Convert selected date to datetime
    target_date = pd.to_datetime(selected_date)
    current_date = pd.Timestamp.now()
    
    # If target date is current month or past, just do a regular forecast
    if target_date.year < current_date.year or (target_date.year == current_date.year and target_date.month <= current_date.month):
        return forecast_leads(output_file, selected_date, selected_location, adjustment_factor=adjustment_factor)
    
    # We need to forecast intermediate months
    st.info(f"Generating predicted intermediary forecasts from {current_date.strftime('%B %Y')} to {target_date.strftime('%B %Y')}")
    
    # Start with current month's data
    current_month = pd.Period(current_date, freq='ME')
    
    # Create a temporary dataframe to store our data
    temp_df = pd.read_csv(output_file)
    
    # Add debug information about initial data
    st.write(f"Initial data contains {len(temp_df)} records")
    if 'Bettendorf' in temp_df['Media_Location_Text__c'].values:
        bettendorf_data = temp_df[temp_df['Media_Location_Text__c'] == 'Bettendorf']
        st.write(f"Initial Bettendorf data: {len(bettendorf_data)} records")
        if not bettendorf_data.empty:
            latest_date = pd.to_datetime(bettendorf_data['day_created']).max()
            st.write(f"Latest Bettendorf data date: {latest_date.strftime('%Y-%m-%d')}")
    
    # Generate forecasts for each month between current and target
    months_to_forecast = []
    month_iter = current_month
    target_month = pd.Period(target_date, freq='ME')
    
    st.write(f"Will forecast from {current_month} to {target_month}")
    
    while month_iter <= target_month:
        months_to_forecast.append(month_iter)
        month_iter = month_iter + 1
    
    # For each month, generate forecast and add to our dataset
    final_results = None
    
    # Create a copy of the original dataset to preserve it
    original_df = temp_df.copy()
    
    for i, month in enumerate(months_to_forecast):
        month_str = month.strftime('%Y-%m')
        st.write(f"Generating predicted forecast for {month.strftime('%B %Y')}...")
        
        # Generate forecast for this month
        forecast_results = forecast_leads(output_file, month_str, selected_location, adjustment_factor=adjustment_factor)
        
        # Debug information for Bettendorf
        if forecast_results is not None and 'Bettendorf' in forecast_results['Location'].values:
            bettendorf_forecast = forecast_results[forecast_results['Location'] == 'Bettendorf']
            st.write(f"Bettendorf forecast for {month_str}: {bettendorf_forecast['Predicted_Monthly_Leads'].values[0]} leads")
        elif selected_location == 'Bettendorf' or selected_location == 'All Locations':
            st.warning(f"No Bettendorf forecast generated for {month_str}. This may cause issues with the visualization.")
        
        # Save the final month's results
        if month == target_month:
            final_results = forecast_results
        
        # If not the last month, add forecasted data to our dataset for next iteration
        if i < len(months_to_forecast) - 1:
            # For each location in the forecast, add a new row to our temp dataset
            if forecast_results is not None:
                # Reset temp_df to original data plus any previously added forecasts
                # This prevents duplicate data from being added
                if i == 0:
                    temp_df = original_df.copy()
                
                # Filter out any existing data for the month we're about to add
                next_month = months_to_forecast[i+1]
                next_month_str = next_month.strftime('%Y-%m')
                temp_df = temp_df[~(pd.to_datetime(temp_df['day_created']).dt.strftime('%Y-%m') == next_month_str)]
                
                for _, row in forecast_results.iterrows():
                    location = row['Location']
                    predicted_leads = row['Predicted_Monthly_Leads']
                    
                    # Create a new row for each day in the month (distribute leads evenly)
                    days_in_month = pd.Period(month_str).days_in_month
                    leads_per_day = predicted_leads / days_in_month
                    
                    for day in range(1, days_in_month + 1):
                        day_date = f"{month_str}-{day:02d}"
                        new_row = {
                            'Media_Location_Text__c': location,
                            'day_created': day_date,
                            'Leads': leads_per_day
                        }
                        temp_df = pd.concat([temp_df, pd.DataFrame([new_row])], ignore_index=True)
                
                # Save updated dataset for next iteration
                temp_df.to_csv(output_file, index=False)
                
                # Debug information after adding new data
                if 'Bettendorf' in temp_df['Media_Location_Text__c'].values:
                    bettendorf_data = temp_df[temp_df['Media_Location_Text__c'] == 'Bettendorf']
                    latest_date = pd.to_datetime(bettendorf_data['day_created']).max()
                    st.write(f"After adding {month_str} data, latest Bettendorf date: {latest_date.strftime('%Y-%m-%d')}")
                
                st.info(f"Added predicted data for {month.strftime('%B %Y')} to use as input for next month's forecast")
            else:
                st.error(f"No forecast results generated for {month_str}. Cannot continue chain forecasting.")
                break
    
    # Final check to ensure we have data for the target month
    if final_results is not None and selected_location != 'All Locations':
        if selected_location not in final_results['Location'].values:
            st.error(f"No forecast generated for {selected_location} in {target_date.strftime('%B %Y')}.")
            # Try to generate a direct forecast for the location
            st.write(f"Attempting direct forecast for {selected_location}...")
            direct_forecast = forecast_leads(output_file, selected_date, selected_location, adjustment_factor=adjustment_factor)
            if direct_forecast is not None and selected_location in direct_forecast['Location'].values:
                st.success(f"Direct forecast for {selected_location} successful!")
                final_results = direct_forecast
    
    # Restore original data to prevent contamination of future runs
    original_df.to_csv(output_file, index=False)
    
    return final_results

# Function to load credentials from file
def load_credentials():
    creds = {
        "username": "",
        "password": "",
        "security_token": ""
    }
    
    # Check if credentials file exists
    if os.path.isfile('credentials.ini'):
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        
        if 'salesforce' in config:
            sf_config = config['salesforce']
            creds["username"] = sf_config.get('username', '')
            creds["password"] = sf_config.get('password', '')
            creds["security_token"] = sf_config.get('security_token', '')
            
    return creds

# Load credentials at startup
credentials = load_credentials()

def main():
    st.set_page_config(page_title="Terrece - Orchard's Lead Forecasting Agent", layout="wide")
    
    # Add logo and title in a container
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.title("🌱 Terrece")
            st.subheader("Orchard's Caravel Lead Forecasting Agent")
        with col2:
            st.image("orchard_logo.png", width=200)
    
    # Create a sidebar for Salesforce credentials
    st.sidebar.header("Salesforce Authentication")
    
    # Pre-populate fields with values from credentials file if available
    username = st.sidebar.text_input("Username", value=credentials["username"])
    password = st.sidebar.text_input("Password", value=credentials["password"], type="password")
    security_token = st.sidebar.text_input("Security Token", value=credentials["security_token"], type="password")
    
    # Display a message if credentials were loaded from file
    if credentials["username"] and credentials["password"] and credentials["security_token"]:
        st.sidebar.success("Test credentials loaded from credentials.ini")
    
    # Forecast Adjustment input
    forecast_adjustment = st.sidebar.number_input(
        label="Forecast Adjustment (0-1)",
        min_value=0.0,
        max_value=1.0,
        value=1.0,
        step=0.01,
        help="Multiply all forecast results by this factor (e.g., 0.8 for 80%)"
    )
    
    # Add debug mode in the sidebar
    with st.sidebar:
        st.title("Settings")
        debug_mode = st.toggle("Debug Mode", value=False, help="Enable to see detailed lead data")
        st.session_state['debug_mode'] = debug_mode
    
    # Date selection
    available_dates = pd.date_range(
        start='2025-01',
        periods=12,
        freq='ME'
    )
    selected_date = st.selectbox(
        "Select prediction month",
        available_dates.strftime('%Y-%m'),
        format_func=lambda x: pd.to_datetime(x).strftime('%B %Y')
    )
    
    # Location selection
    location_options = ['All Locations'] + [
        'Ankeny', 'Beloit', 'Bettendorf', 'Boise', 'Chicago',
        'Coeur d\'Alene', 'Crystal Lake', 'Eau Claire', 'Elgin',
        'Fond du Lac', 'Geneva', 'Iowa City', 'Lake Geneva',
        'Meridian', 'Moorhead', 'Nampa', 'Rolling Meadows',
        'Spokane', 'Urbandale', 'Warrenville', 'Weldon Spring',
        'West Madison'
    ]
    selected_location = st.selectbox("Select location", location_options)
    
    if st.button("Generate Forecast"):
        # Validate credentials are provided
        if not username or not password or not security_token:
            st.error("Please provide your Salesforce credentials in the sidebar before generating a forecast.")
            return
        
        with st.spinner("Authenticating with Salesforce and fetching data..."):
            # Get data from Salesforce with provided credentials
            output_file, error = get_salesforce_data(username, password, security_token, selected_date)
            
            if error:
                st.error(f"Authentication failed: {error}")
                return
            
            if not output_file:
                st.error("Failed to retrieve data from Salesforce.")
                return
            
            # Display debug information if debug mode is enabled
            if debug_mode:
                st.header("Debug Information")
                st.subheader("Detailed Lead Data")
                
                # Sort data by location and date
                debug_df = pd.read_csv(output_file).copy()
                debug_df['day_created'] = pd.to_datetime(debug_df['day_created'])
                debug_df = debug_df.sort_values(['Media_Location_Text__c', 'day_created'])
                
                # Display data for each location
                for location in debug_df['Media_Location_Text__c'].unique():
                    with st.expander(f"Lead data for {location}"):
                        location_data = debug_df[debug_df['Media_Location_Text__c'] == location]
                        
                        # Show summary statistics
                        st.write(f"Total leads: {len(location_data)}")
                        st.write(f"Date range: {location_data['day_created'].min().strftime('%Y-%m-%d')} to {location_data['day_created'].max().strftime('%Y-%m-%d')}")
                        
                        # Display each lead as its own row with Lead ID
                        # Ensure the table includes all available columns
                        # Format the DataFrame to show necessary columns first
                        
                        # Reorder columns to put important ones first
                        columns_to_show = ['Id', 'day_created', 'Leads', 'Media_Location_Text__c']
                        
                        # Add any other columns that exist in the DataFrame
                        other_columns = [col for col in location_data.columns if col not in columns_to_show]
                        display_columns = columns_to_show + other_columns
                        
                        # Filter to only include columns that actually exist
                        display_columns = [col for col in display_columns if col in location_data.columns]
                        
                        # Format date for better readability
                        if 'day_created' in location_data.columns:
                            location_data['day_created'] = location_data['day_created'].dt.strftime('%Y-%m-%d')
                        
                        # Display the detailed data
                        st.dataframe(location_data[display_columns])
                        
                        # Add download button for this location's data
                        csv = location_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"Download {location} leads CSV",
                            data=csv,
                            file_name=f"{location}_leads.csv",
                            mime="text/csv"
                        )
            
            # Use chain forecasting for future months
            print(f"DEBUG: Passing forecast_adjustment value: {forecast_adjustment}")
            forecast_results = generate_chain_forecast(output_file, selected_date, selected_location, adjustment_factor=forecast_adjustment)
            
            if forecast_results is not None:
                # Display results
                st.subheader("Forecast Results")
                st.dataframe(forecast_results)

                # Debug comparison of original vs adjusted
                if debug_mode and 'Original_Predicted_Monthly_Leads' in forecast_results.columns:
                    st.subheader("Forecast Adjustment Debug")
                    debug_df = forecast_results[[
                        'Location', 'Month', 'Original_Predicted_Monthly_Leads', 'Predicted_Monthly_Leads'
                    ]].rename(columns={
                        'Original_Predicted_Monthly_Leads': 'Original_Predicted_Leads',
                        'Predicted_Monthly_Leads': 'Adjusted_Predicted_Leads'
                    })
                    st.dataframe(debug_df)
                
                # Display visualizations
                st.subheader("Forecast Visualizations")
                cols = st.columns(2)
                col_idx = 0
                
                for location in forecast_results['Location'].unique():
                    image_path = f"forecast_visuals/{location}_forecast.png"
                    if os.path.exists(image_path):
                        cols[col_idx].image(image_path)
                        col_idx = (col_idx + 1) % 2
            
                # Download button - only include selected location data
                zip_data = create_download_zip(forecast_results, "forecast_visuals")
                st.download_button(
                    label="📥 Download Analysis",
                    data=zip_data,
                    file_name=f"terrece_analysis_{selected_date}_{selected_location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
            else:
                st.error("No forecast results were generated. Please check the logs for details.")

if __name__ == "__main__":
    main() 