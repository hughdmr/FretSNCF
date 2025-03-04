from datetime import datetime, timedelta, time
import pandas as pd

def time_to_minutes(day_of_week, time_str, total_jours):
    # Convert the day of the week to an integer (0 = Monday, 6 = Sunday)
    day_of_week = int(day_of_week)-1
    if day_of_week + 7 < total_jours:
        day_of_week2 = day_of_week + 7
    else:
        day_of_week2 = day_of_week
    # Convert the time part to a datetime object
    time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    
    # Calculate the total minutes
    total_minutes = day_of_week * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    total_minutes2 = day_of_week2 * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    if total_minutes == total_minutes2:
        total_minutes2 = 0
    return [total_minutes, total_minutes2]

def time_to_minutes_2(date_str, time_str, jour1):
    if type(date_str) == str:
        # Convert the date part to a datetime object
        date_obj = datetime.strptime(date_str.strip(), "%d/%m/%Y")
    elif type(date_str) == datetime or type(date_str) == pd._libs.tslibs.timestamps.Timestamp:
        date_obj = date_str
    
    
    # Get the day of the week (0 = Monday, 6 = Sunday...jusqu'à finir le total des jours)
    day_diff = date_obj- jour1
    number_day = day_diff.days
    
    if type(time_str) == str:
        # Convert the time part to a datetime object
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    elif type(time_str) == time:
        time_obj = time_str
    
    # Calculate the total minutes
    total_minutes = number_day * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    return total_minutes

def minute_to_jour(minutes, jour1):
    jour = jour1 + timedelta(minutes//(24*60))
    # Format the date to "dd/mm/yyyy"
    date_str = jour.strftime("%d/%m/%Y")
    
    return date_str

def minute_to_jour2(minutes, jour1):
    # Add the minutes to the initial date
    jour = jour1 + timedelta(minutes=minutes)
    
    # Format the date to "dd/mm/yyyy"
    date_str = jour.strftime("%d/%m/%Y")
    
    # Format the time to "HH:MM"
    time_str = jour.strftime("%H:%M")
    
    return date_str, time_str