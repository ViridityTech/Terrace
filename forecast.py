import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import os
from datetime import datetime

def prepare_data(df):
    """Prepare the data for forecasting"""
    # Convert day_created to datetime and extract month
    df['day_created'] = pd.to_datetime(df['day_created'])
    df['month'] = df['day_created'].dt.to_period('M')
    
    # Group by location and month and ensure integer counts
    monthly_data = df.groupby(['Media_Location_Text__c', 'month'])['Leads'].sum().round().astype(int).reset_index()
    
    # Ensure all values are positive integers
    monthly_data['Leads'] = monthly_data['Leads'].clip(lower=0)
    
    # Sort by month
    monthly_data.sort_values(['Media_Location_Text__c', 'month'], inplace=True)
    
    return monthly_data

def forecast_leads(input_file="leads_by_location_date.csv", prediction_month=None, selected_location=None):
    """Main forecasting function"""
    output_dir = "forecast_results"
    visuals_dir = "forecast_visuals"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)
    
    # Read and prepare monthly data
    df = pd.read_csv(input_file)
    df_monthly = prepare_data(df)
    
    # Get prediction month or default to current month
    if prediction_month is None:
        prediction_month = pd.Timestamp.now().to_period('M')
    else:
        prediction_month = pd.Period(prediction_month)
    
    # Get current month to determine if we're forecasting future months
    current_month = pd.Timestamp.now().to_period('M')
    is_future_month = prediction_month > current_month
    
    forecast_results = []
    
    # Filter locations based on selection
    if selected_location and selected_location != 'All Locations':
        locations = [selected_location]
    else:
        locations = df_monthly['Media_Location_Text__c'].unique()

    for location in locations:
        if location is None:
            continue
            
        print(f"\nForecasting for location: {location}")
        
        # Filter data for this location up to but NOT including prediction month
        location_data = df_monthly[
            (df_monthly['Media_Location_Text__c'] == location) &
            (df_monthly['month'] < prediction_month)  # Changed from <= to <
        ].copy()
        
        if len(location_data) < 3:  # Need at least 3 months of historical data
            print(f"Skipping {location} - insufficient monthly data")
            continue
        
        # Set up time series
        location_data.set_index('month', inplace=True)
        ts = location_data['Leads']
        
        # Get last actual data point and determine forecast needs
        last_actual_month = prediction_month - 1
        months_ahead = 1
        
        # Get training data (all data up to but not including prediction month)
        training_data = ts[ts.index <= last_actual_month]
        
        try:
            # Log transform the data (adding 1 to handle zeros)
            ts_log = np.log1p(training_data)
            
            # Fit ARIMA model on log-transformed data
            model = ARIMA(ts_log, order=(1,1,1), freq='M')
            model_fit = model.fit()
            
            # Generate forecast for prediction month
            forecast_log = model_fit.forecast(steps=1)
            conf_int_log_95 = model_fit.get_forecast(steps=1).conf_int(alpha=0.05)
            conf_int_log_50 = model_fit.get_forecast(steps=1).conf_int(alpha=0.50)
            
            # Transform predictions back to original scale and round to integers
            forecast = np.round(np.expm1(forecast_log)).astype(int)
            conf_int_95 = np.round(np.expm1(conf_int_log_95)).astype(int)
            conf_int_50 = np.round(np.expm1(conf_int_log_50)).astype(int)
            
            # Ensure predictions are non-negative integers
            forecast = np.maximum(forecast, 0)
            conf_int_95 = np.maximum(conf_int_95, 0)
            conf_int_50 = np.maximum(conf_int_50, 0)
            
            # Get previous month
            previous_month = prediction_month - 1
            previous_month_data = ts[ts.index == previous_month]
            
            # Only consider it actual data if it's in or before the current month
            is_actual = previous_month <= current_month
            previous_month_label = "Actual" if is_actual else "Predicted"
            
            # Only use previous month data if it's actual, otherwise use None
            if is_actual and not previous_month_data.empty:
                previous_month_value = int(previous_month_data.iloc[0])
            else:
                previous_month_value = None
            
            # Store results
            result_dict = {
                'Location': location,
                'Month': prediction_month.strftime('%Y-%m'),
                'Predicted_Monthly_Leads': int(forecast.iloc[0]),
                'Lower_Bound_95': int(conf_int_95.iloc[0, 0]),
                'Upper_Bound_95': int(conf_int_95.iloc[0, 1]),
                'Lower_Bound_50': int(conf_int_50.iloc[0, 0]),
                'Upper_Bound_50': int(conf_int_50.iloc[0, 1])
            }
            
            # Only add previous month data if we have an actual value
            if previous_month_value is not None:
                result_dict[f'{previous_month.strftime("%B %Y")}_{previous_month_label}'] = previous_month_value
            
            # Only add running total if we're forecasting the current month
            if prediction_month == current_month:
                current_month_data = df_monthly[
                    (df_monthly['Media_Location_Text__c'] == location) &
                    (df_monthly['month'] == prediction_month)
                ]
                running_total = int(current_month_data['Leads'].sum()) if not current_month_data.empty else 0
                result_dict[f'{prediction_month.strftime("%B %Y")}_Running_Total'] = running_total
            
            forecast_results.append(result_dict)
            
            # Create visualization
            plt.figure(figsize=(16, 6))
            
            # Get the full date range for proper x-axis labeling
            all_dates = pd.period_range(start=ts.index.min(), end=prediction_month)
            
            # Create a mapping of dates to x-positions
            date_to_position = {}
            for i, date in enumerate(all_dates):
                date_to_position[date] = i
            
            # Plot historical data with correct x-positions
            historical_x = [date_to_position[date] for date in training_data.index]
            plt.plot(historical_x, training_data.values, 'b-', label='Historical')
            plt.plot(historical_x, training_data.values, 'bo')  # Add blue dots
            
            # Plot forecast point at the correct x-position
            forecast_x = date_to_position[prediction_month]
            plt.plot(forecast_x, forecast.iloc[0], 'ro',
                    label=f'Forecast ({prediction_month.strftime("%B %Y")})')
            
            # Plot confidence intervals at the correct x-position
            plt.fill_between([forecast_x-0.2, forecast_x+0.2], 
                           [conf_int_95.iloc[0, 0], conf_int_95.iloc[0, 0]], 
                           [conf_int_95.iloc[0, 1], conf_int_95.iloc[0, 1]], 
                           color='#9932CC',
                           alpha=0.3,
                           label='95% Confidence Interval')
            
            # Add confidence interval values
            plt.text(forecast_x, conf_int_95.iloc[0, 1], 
                    f'{int(conf_int_95.iloc[0, 1])}', 
                    horizontalalignment='center', 
                    verticalalignment='bottom')
            plt.text(forecast_x, conf_int_95.iloc[0, 0], 
                    f'{int(conf_int_95.iloc[0, 0])}', 
                    horizontalalignment='center', 
                    verticalalignment='top')
            
            plt.fill_between([forecast_x-0.2, forecast_x+0.2], 
                           [conf_int_50.iloc[0, 0], conf_int_50.iloc[0, 0]], 
                           [conf_int_50.iloc[0, 1], conf_int_50.iloc[0, 1]], 
                           color='red', 
                           alpha=0.3,
                           label='50% Confidence Interval')
            
            # Add forecast value directly above the dot
            plt.text(forecast_x, forecast.iloc[0] + 0.5, 
                    f'{int(forecast.iloc[0])}', 
                    horizontalalignment='center', 
                    verticalalignment='bottom')
            
            # Add values for last 3 months of historical data
            for i in range(min(3, len(training_data))):
                idx = len(training_data) - 3 + i
                if idx >= 0:
                    date = training_data.index[idx]
                    value = training_data.values[idx]
                    x_pos = date_to_position[date]
                    plt.text(x_pos, value + 0.5, 
                            f'{int(value)}',
                            horizontalalignment='center', 
                            verticalalignment='bottom')
            
            # Set x-axis labels for all months
            x_ticks = list(range(len(all_dates)))
            x_labels = [d.strftime('%b %y') for d in all_dates]
            plt.xticks(x_ticks, x_labels, rotation=45, ha='right')
            
            # Remove grid
            plt.grid(False)
            
            # Add a note if we're using predicted data for forecasting
            title_text = f'Monthly Lead Forecast for {location}\nPrediction for {prediction_month.strftime("%B %Y")}'
            if is_future_month:
                title_text += f'\n(Using predicted data for months after {current_month.strftime("%B %Y")})'
            
            plt.title(title_text)
            plt.xlabel('Month')
            plt.ylabel('Number of Leads')
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.legend(loc='upper left')
            plt.savefig(f'{visuals_dir}/{location}_forecast.png', bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"Error forecasting for {location}: {str(e)}")
    
    if forecast_results:
        results_df = pd.DataFrame(forecast_results)
        
        # Only save results file if we processed all Locations
        if selected_location is None or selected_location == 'All Locations':
            results_df.to_csv(f'{output_dir}/forecast_results.csv', index=False)
            print(f"\nForecast results saved to {output_dir}/forecast_results.csv")
        return results_df
    else:
        print("No forecast results generated")
        return None

if __name__ == "__main__":
    forecast_leads() 