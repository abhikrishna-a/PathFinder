import signal
import sys
import time
import threading

from django.core.management.base import BaseCommand
from django.core.management import call_command

import schedule as sched

from dashboard.management.commands.run_fetcher import Command as FetcherCommand


class Command(BaseCommand):
    help = "Run both the scheduler and the Django dev server"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Auto Job Portal (scheduler + dashboard)"))

        def run_cycle():
            self.stdout.write(self.style.NOTICE("\n--- Scheduled fetch cycle ---"))
            try:
                cmd = FetcherCommand()
                cmd.handle()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Cycle failed: {e}"))

        def run_scheduler():
            sched.every(60).minutes.do(run_cycle)
            while True:
                sched.run_pending()
                time.sleep(1)

        def shutdown(sig, frame):
            self.stdout.write(self.style.WARNING("\nShutting down..."))
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        run_cycle()

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        self.stdout.write(self.style.SUCCESS(
            "\nDashboard: http://localhost:8000\n"
            "Scheduler: running every 60 minutes\n"
            "Press Ctrl+C to stop\n"
        ))

        call_command("runserver", "0.0.0.0:8000", "--noreload")
