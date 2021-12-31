from django.core.management.base import BaseCommand
import homeet_bot


class Command(BaseCommand):
    help = 'start telegram bot'

    def handle(self, *args, **options):
        homeet_bot.bot_start()
