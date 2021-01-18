import datetime
from datetime import date, datetime,timezone
from datetime import datetime
from pytz import timezone


def testDates(strDate):
    if(datetime.now().strftime('%Y-%m-%d')>strDate):
        return True
    else:
        return False
    
def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = timezone(tz1)
    tz2 = timezone(tz2)

    dt = datetime.strptime(dt,"%Y-%m-%dT%H:%M:%S")
    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)
    dt = dt.strftime("%Y-%m-%dT%H:%M:%S")

    return dt

def convert(strDate):
    #2021-01-16T02:56:53Z
    fmt = "%Y-%m-%dT%H:%M:%S"
    now_time = datetime.now(timezone("US/Eastern"))
    print(now_time.strftime(fmt))
    
    eastern = timezone('US/Eastern')
    loc_dt = eastern.localize(strDate)
    print(loc_dt)
    
print(convert_datetime_timezone("2020-01-15T02:56:53",'UTC' ,"US/Eastern"))
print(convert_datetime_timezone("2021-01-14T02:56:53",'UTC' ,"US/Eastern"))
print(convert_datetime_timezone("2021-01-16T02:56:53",'UTC' ,"US/Eastern"))