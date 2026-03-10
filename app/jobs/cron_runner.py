from apscheduler.schedulers.blocking import BlockingScheduler
from app.jobs.daily_job import run_daily_job

scheduler = BlockingScheduler()

# Run every day at 02:00 AM
scheduler.add_job(
    run_daily_job,
    "cron",
    hour=2,
    minute=0
)

if __name__ == "__main__":
    print("RTR Scheduler started...")
    scheduler.start()

