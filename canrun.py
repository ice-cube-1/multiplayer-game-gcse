import vars
from datetime import datetime, timedelta
import threading


def timeUntilMorning() -> float:
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("08:30", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()


def checkRunnable() -> None:
    while True:
        vars.can_run = True
        threading.Event().wait(timeUntilMorning())
        if datetime.today().weekday() < 5:
            vars.can_run = False
        threading.Event().wait(3.75*60*60)
        vars.can_run = True
        threading.Event.wait(45*60)
        if datetime.today().weekday() < 5:
            vars.can_run = False
        threading.Event.wait(3.25*60*60)
        vars.can_run = True


offlineThread = threading.Thread(target=checkRunnable)
offlineThread.start()
