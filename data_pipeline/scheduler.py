"""Blocking scheduler (docs/DECISIONS.md D6 — APScheduler).

Run: python -m data_pipeline.scheduler

NYSE closes 16:00 New York = 22:00 Paris; daily_update fires 22:30 Europe/Paris
on trading weekdays.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from .jobs import daily_update


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    scheduler = BlockingScheduler(timezone="Europe/Paris")
    scheduler.add_job(daily_update, "cron", day_of_week="mon-fri", hour=22, minute=30)
    print("Scheduler running: daily_update at 22:30 Europe/Paris, Mon-Fri. Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
