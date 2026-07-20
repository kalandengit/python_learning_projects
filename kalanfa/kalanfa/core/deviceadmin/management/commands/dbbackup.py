import logging

from django.core.management.base import BaseCommand

import kalanfa
from kalanfa.utils import server

from ...utils import dbbackup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    output_transaction = True

    # @ReservedAssignment
    help = (
        "Create a database backup of Kalanfa. This is not intended for "
        "replication across different devices, but *only* for restoring a "
        "single device from a local backup of the database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "dest_folder",
            nargs="?",
            type=str,
            help=(
                "Specifies which folder to create the dump in, otherwise it "
                "is created in the default location ~/.kalanfa/backups"
            ),
        )

    def handle(self, *args, **options):
        try:
            server.get_status()
            self.stderr.write(
                self.style.ERROR(
                    "Cannot restore while Kalanfa is running, please run:\n"
                    "\n"
                    "    kalanfa stop\n"
                )
            )
            raise SystemExit()
        except server.NotRunning:
            # Great, it's not running!
            pass

        dest_folder = options.get("dest_folder", None)

        backup = dbbackup(kalanfa.__version__, dest_folder=dest_folder)
        self.stdout.write(
            self.style.SUCCESS("Backed up database to: {path}".format(path=backup))
        )
