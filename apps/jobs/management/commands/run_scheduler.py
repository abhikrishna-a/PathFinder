import signal
import sys
import time

from django.core.management.base import BaseCommand

import schedule as sched

from config.settings import FETCH_INTERVAL_MINUTES
from apps.jobs.management.commands.run_fetcher import Command as FetcherCommand


class Command(BaseCommand):
    help = "Run the fetcher on a schedule loop"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            f"Starting scheduler (every {FETCH_INTERVAL_MINUTES} minutes)"
        ))

        def run_cycle():
            self.stdout.write(self.style.NOTICE("\n--- Scheduled fetch cycle ---"))
            try:
                cmd = FetcherCommand()
                cmd.handle()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Cycle failed: {e}"))

        def shutdown(sig, frame):
            self.stdout.write(self.style.WARNING("\nShutting down scheduler..."))
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        run_cycle()

        sched.every(FETCH_INTERVAL_MINUTES).minutes.do(run_cycle)

        self.stdout.write(self.style.SUCCESS("Scheduler running. Press Ctrl+C to stop."))

        while True:
            sched.run_pending()
            time.sleep(1)
