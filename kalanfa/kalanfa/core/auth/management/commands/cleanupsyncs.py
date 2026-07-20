from django.core.management.base import CommandError
from morango.management.commands.cleanupsyncs import Command as CleanupsyncCommand

from kalanfa.core.device.utils import device_provisioned


class Command(CleanupsyncCommand):
    def handle(self, *args, **options):
        if not device_provisioned():
            raise CommandError("Kalanfa is unprovisioned")

        return super().handle(*args, **options)
