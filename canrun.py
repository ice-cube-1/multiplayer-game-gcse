import vars
from datetime import datetime, timedelta
import threading


def timeUntilMorning() -> float:
    """gets the number of seconds until 8.30AM - when the game is first blocked during the day"""
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("08:30", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()


def checkRunnable(global_vars: vars.GLOBAL) -> None:
    """continuous loop that blocks the game between
     - 8:30 - 12:15
     - 13:00 - 16.15\n
     only on weekdays"""
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
    """initializes the blocking at certain times of day thread"""
    offlineThread = threading.Thread(target=checkRunnable, args=(global_vars,))
    offlineThread.start()
