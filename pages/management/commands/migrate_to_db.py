from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pages.page import full_path_all_pages, page_wrapped

from pages.models import PikiPage

from datetime import datetime
import fstools
import os
import shutil
from zoneinfo import ZoneInfo


def add_page_data(rel_path, tags, page_txt, creation_time, creation_user, modified_time, modified_user):
    try:
        page = PikiPage.objects.get(rel_path=rel_path)
    except PikiPage.DoesNotExist:
        page = PikiPage(rel_path=rel_path)
    #
    page.tags = tags
    page.page_txt = page_txt
    #
    page.creation_time = datetime.fromtimestamp(creation_time, ZoneInfo("UTC"))
    creation_user = creation_user or "dirk"
    page.creation_user = User.objects.get(username=creation_user)
    modified_user = modified_user or "dirk"
    page.modified_time = datetime.fromtimestamp(modified_time, ZoneInfo("UTC"))
    page.modified_user = User.objects.get(username=modified_user)
    page.owner = page.owner or page.creation_user
    #
    page.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for path in full_path_all_pages():
            fs_page = page_wrapped(None, path)
            if fs_page._page.is_available():
                self.stdout.write(self.style.MIGRATE_HEADING("Migration of page '%s'" % fs_page.rel_path))
                for history_number in fs_page._page.history_numbers_list():
                    self.stdout.write(self.style.MIGRATE_HEADING("  * Adding history version %d" % history_number))
                    h_page = page_wrapped(None, path, history_version=history_number)
                    add_page_data(
                        rel_path=h_page.rel_path,
                        tags=h_page.tags,
                        page_txt=h_page._page.raw_page_src,
                        #
                        creation_time=h_page.creation_time,
                        creation_user=h_page.creation_user,
                        modified_time=h_page.modified_time,
                        modified_user=h_page.modified_user
                    )
                #
                self.stdout.write(self.style.MIGRATE_HEADING("  * Adding current version"))
                add_page_data(
                    rel_path=fs_page.rel_path,
                    tags=fs_page.tags,
                    page_txt=fs_page._page.raw_page_src,
                    #
                    creation_time=fs_page.creation_time,
                    creation_user=fs_page.creation_user,
                    modified_time=fs_page.modified_time,
                    modified_user=fs_page.modified_user
                )
                #
                src = os.path.join(path, "attachments")
                if os.path.isdir(src):
                    dst = os.path.join(settings.MYCREOLE_ROOT, fs_page.rel_path)
                    for attachment in fstools.filelist(src):
                        self.stdout.write(self.style.MIGRATE_HEADING("  * Copy attachment ''%s to new location" % os.path.basename(attachment)))
                        fstools.mkdir(dst)
                        shutil.copy(attachment, dst)
