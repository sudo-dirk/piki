from django.core.management.base import BaseCommand
from pages.search import create_index, rebuild_index


class Command(BaseCommand):
    def handle(self, *args, **options):
        ix = create_index()
        n = rebuild_index(ix)
        self.stdout.write(self.style.SUCCESS('Search index for %d items created.') % n)
