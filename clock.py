from apscheduler.schedulers.blocking import BlockingScheduler
from prayer import main

sched = BlockingScheduler()

# @sched.scheduled_job('cron', day_of_week='*', hour=2, minute=52)
# def timed_job():
#     print("in clock.py")
#     main("MST")

# @sched.scheduled_job('interval', minutes=5)
# def timed_job():
#     main("MST")

@sched.scheduled_job('cron', day_of_week='*', hour=3)
def scheduled_job_a():
    print("in clock.py")
    main(["ADT"])

@sched.scheduled_job('cron', day_of_week='*', hour=4)
def scheduled_job_b():
    print("in clock.py")
    main(["AST","EDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=5)
def scheduled_job_c():
    print("in clock.py")
    main(["EST","CDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=6)
def scheduled_job_d():
    print("in clock.py")
    main(["CST","MDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=7)
def scheduled_job_e():
    print("in clock.py")
    main(["MST","PDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=8)
def scheduled_job_f():
    print("in clock.py")
    main(["PST","ASDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=9)
def scheduled_job_g():
    print("in clock.py")
    main(["AKST","HDT"])

@sched.scheduled_job('cron', day_of_week='*', hour=10)
def scheduled_job_h():
    print("in clock.py")
    main(["HST"])


sched.start()