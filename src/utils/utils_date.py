from datetime import datetime, timedelta, time
import pandas as pd

def time_to_minutes(day_of_week, time_str, total_jours,day_1):
    """Convert the time to minutes depending of the week, same as the 2nd function. Convert the day of the week to an integer (0 = Monday, 6 = Sunday)"""
    day_of_week = int(day_of_week)-1 - day_1
    if day_of_week + 7 < total_jours-day_1:
        day_of_week2 = day_of_week + 7
    else:
        day_of_week2 = day_of_week
    time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    
    total_minutes = day_of_week * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    total_minutes2 = day_of_week2 * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    if total_minutes == total_minutes2:
        total_minutes2 = 0
    return [total_minutes, total_minutes2]

def time_to_minutes_2(date_str, time_str, jour1,day_1):
    """Convert the time to minutes. Get the day of the week (0 = Monday, 6 = Sunday...jusqu'à finir le total des jours)"""
    if type(date_str) == str:
        date_obj = datetime.strptime(date_str.strip(), "%d/%m/%Y")
    elif type(date_str) == datetime or type(date_str) == pd._libs.tslibs.timestamps.Timestamp:
        date_obj = date_str
    
    day_diff = date_obj- jour1
    number_day = day_diff.days-day_1
    
    if type(time_str) == str:
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    elif type(time_str) == time:
        time_obj = time_str
    
    total_minutes = number_day * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    return total_minutes

def time_to_minutes_3(day, time_str, day_1):
    """Convert the time to minutes"""
    number_day = int(day)

    if type(time_str) == str:
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
    elif type(time_str) == time:
        time_obj = time_str
    
    total_minutes = number_day * 24 * 60 + time_obj.hour * 60 + time_obj.minute
    return total_minutes

def minute_to_date(minutes, jour1):
    """Convert the minutes to a date"""
    jour = jour1 + timedelta(minutes//(24*60))
    date_str = jour.strftime("%d/%m/%Y")
    
    return date_str

def minute_to_date2(minutes, jour1):
    """Convert the minutes to a date"""
    jour = jour1 + timedelta(minutes=minutes)
    
    date_str = jour.strftime("%d/%m/%Y")
    time_str = jour.strftime("%H:%M")
    
    return date_str, time_str