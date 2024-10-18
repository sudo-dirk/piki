from datetime import datetime
from django.conf import settings

import fstools
import logging
import os
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh import index, qparser

from pages.page import page_wrapped, full_path_all_pages

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


SCHEMA = Schema(
    id=ID(unique=True, stored=True),
    # Page
    title=TEXT,
    page_src=TEXT,
    tag=TEXT,
    # metadata
    creation_time=DATETIME,
    modified_time=DATETIME,
    modified_user=TEXT
)


def mk_whooshpath_if_needed():
    if not os.path.exists(settings.WHOOSH_PATH):
        fstools.mkdir(settings.WHOOSH_PATH)


def create_index():
    mk_whooshpath_if_needed()
    logger.debug('Search Index created.')
    return index.create_in(settings.WHOOSH_PATH, schema=SCHEMA)


def rebuild_index(ix):
    page_path = full_path_all_pages()
    for path in page_path:
        pw = page_wrapped(None, path)
        add_item(ix, pw)
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


def add_item(ix, pw: page_wrapped):
    # Define Standard data
    #
    data = dict(
        id=pw.rel_path,
        #
        title=pw.title,
        page_src=pw.raw_page_src,
        tag=pw.tags,
        #
        creation_time=datetime.fromtimestamp(pw.creation_time),
        modified_time=datetime.fromtimestamp(pw.modified_time),
        modified_user=pw.modified_user
    )
    with ix.writer() as w:
        logger.info('Adding document with id=%s to the search index.', data.get('id'))
        w.update_document(**data)
        for key in data:
            logger.debug('  - Adding %s=%s', key, repr(data[key]))


def whoosh_search(search_txt):
    ix = load_index()
    qp = qparser.MultifieldParser(['title', 'page_src', 'tag'], ix.schema)
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


def delete_item(ix, pw: page_wrapped):
    with ix.writer() as w:
        logger.info('Removing document with id=%s from the search index.', pw.rel_path)
        w.delete_by_term("id", pw.rel_path)


def update_item(pw: page_wrapped):
    ix = load_index()
    delete_item(ix, pw)
    add_item(ix, pw)
