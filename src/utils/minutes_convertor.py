import datetime

def time_to_minutes(time_str):
    time_part = time_str.split(',')[1] if ',' in time_str else time_str
    time_part = time_part.strip('()') 
    time_obj = datetime.strptime(time_part, "%H:%M")
    return time_obj.hour * 60 + time_obj.minute

def minutes_to_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02}:{mins:02}"
