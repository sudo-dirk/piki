from django.conf import settings

import fstools
import logging
import os
from whoosh.fields import Schema, ID, TEXT
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh import index, qparser

from pages.page import base_page

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


SCHEMA = Schema(
    id=ID(unique=True, stored=True),
    # Page
    title=TEXT,
    page_src=TEXT
)


def mk_whooshpath_if_needed():
    if not os.path.exists(settings.WHOOSH_PATH):
        fstools.mkdir(settings.WHOOSH_PATH)


def create_index():
    mk_whooshpath_if_needed()
    logger.debug('Search Index created.')
    return index.create_in(settings.WHOOSH_PATH, schema=SCHEMA)


def rebuild_index(ix):
    page_path = fstools.dirlist(settings.PAGES_ROOT, rekursive=False)
    for path in page_path:
        bp = base_page(path)
        add_item(ix, bp)
    return len(page_path)


def load_index():
    mk_whooshpath_if_needed()
    try:
        ix = index.open_dir(settings.WHOOSH_PATH)
    except index.EmptyIndexError:
        ix = create_index()
    else:
        logger.debug('Search Index opened.')
    return ix


def add_item(ix, bp: base_page):
    # Define Standard data
    #
    data = dict(
        id=bp.rel_path,
        title=bp.title,
        page_src=bp.raw_page_src
    )
    with ix.writer() as w:
        logger.info('Adding document with id=%s to the search index.', data.get('id'))
        w.add_document(**data)
        for key in data:
            logger.debug('  - Adding %s=%s', key, repr(data[key]))


def whoosh_search(search_txt):
    ix = load_index()
    qp = qparser.MultifieldParser(['title', 'page_src'], ix.schema)
    qp.add_plugin(DateParserPlugin(free=True))
    try:
        q = qp.parse(search_txt)
    except AttributeError:
        return None
    except Exception:
        return None
    with ix.searcher() as s:
        results = s.search(q, limit=None)
        rpl = []
        for hit in results:
            rpl.append(hit['id'])
        return rpl


def delete_item(ix, bp: base_page):
    with ix.writer() as w:
        logger.info('Removing document with id=%s from the search index.', bp.rel_path)
        w.delete_by_term("task_id", bp.rel_path)


def update_item(bp: base_page):
    ix = load_index()
    delete_item(ix, bp)
    add_item(ix, bp)

