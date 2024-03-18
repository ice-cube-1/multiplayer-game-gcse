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


def checkRunnable(global_vars: vars.GLOBAL) -> None:
    while True:
        global_vars.can_run = True
        threading.Event().wait(timeUntilMorning())
        if datetime.today().weekday() < 5:
            global_vars.can_run = False
        threading.Event().wait(3.75*60*60)
        global_vars.can_run = True
        threading.Event.wait(45*60)
        if datetime.today().weekday() < 5:
            global_vars.can_run = False
        threading.Event.wait(3.25*60*60)
        global_vars.can_run = True

def start(global_vars: vars.GLOBAL) -> None:
    offlineThread = threading.Thread(target=checkRunnable, args=(global_vars,))
    offlineThread.start()
