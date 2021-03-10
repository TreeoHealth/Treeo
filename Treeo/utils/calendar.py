from calendar import HTMLCalendar

from ReqAppt.models import ApptTable



# python built in HTML calendar
class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None, request=None):
        self.year = year
        self.month = month
        self.request = request
        super(Calendar, self).__init__()


    # formats a day and then filters the events by the day
    def formatTheDay(self, day, events):
        events_per_day = events.filter(meetingDate__day=day)
        dday = ''

        # TODO THIS SECTION CAN BE USED TO MARK PATIENTS
        confirmed = True
        for event in events_per_day:
            dday += f'<li class="calendar-patient {"confirmed" if confirmed else "pending" }"> {event.meetingDate.strftime("%I:%M %p") } {event.provider.user.first_name} {event.provider.user.last_name}</li>'

        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {dday} </ul></td>"
        return '<td></td>'

    # formats a week as a table row
    def formatTheWeek(self, calweek, events):
        week = ''
        for dday, weekday in calweek:
            week += self.formatTheDay(dday, events)
        return f'<tr> {week} </tr>'

    # formats a month as a table and filter events by a year and a month
    def formatTheMonth(self, withyear=True):
        if self.request.user.user_type == 1:
            events = ApptTable.objects.filter(meetingDate__year=self.year, meetingDate__month=self.month)
        elif self.request.user.user_type == 2:
            events = ApptTable.objects.filter(provider= self.request.user.provider.id).filter(meetingDate__year=self.year, meetingDate__month=self.month)
        elif self.request.user.user_type == 3:
            events = ApptTable.objects.filter(patient=self.request.user.patient.id).filter(meetingDate__year=self.year, meetingDate__month=self.month)
        else:
            events = ApptTable.objects.none()
        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatTheWeek(week, events)}\n'
        return cal