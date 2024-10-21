from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pages.models import PikiPage

from datetime import datetime
import fstools
from zoneinfo import ZoneInfo


SYSTEM_PAGES = {
    "tree": """= Tree
<<allpagestree>>""",
    "index": """= Index
<<allpages>>""",
}


def add_page_data(rel_path, tags, page_txt, creation_time, creation_user, modified_time, modified_user):
    try:
        page = PikiPage.objects.get(rel_path=rel_path)
    except PikiPage.DoesNotExist:
        page = PikiPage(rel_path=rel_path)
    #
    page.tags = tags
    page.page_txt = page_txt
    #
    page.creation_time = creation_time
    try:
        page.creation_user = User.objects.get(username=creation_user)
    except User.DoesNotExist:
        page.creation_user = None
    page.modified_time = modified_time
    try:
        page.modified_user = User.objects.get(username=modified_user)
    except User.DoesNotExist:
        page.modified_user = None
    #
    page.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for rel_path in SYSTEM_PAGES:
            self.stdout.write(self.style.MIGRATE_HEADING("Migration of page '%s'" % rel_path))
            #
            dtm = datetime.now(ZoneInfo("UTC"))
            add_page_data(
                rel_path,
                "",
                SYSTEM_PAGES[rel_path],
                dtm,
                None,
                dtm,
                None
            )
