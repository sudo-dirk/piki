from datetime import datetime
from django.conf import settings

import fstools
import logging
import os
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh import index, qparser

from .models import PikiPage

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
    pages = PikiPage.objects.all()
    for pp in pages:
        if not pp.deleted:
            add_item(ix, pp)
    return len(pages)


def load_index():
    mk_whooshpath_if_needed()
    try:
        ix = index.open_dir(settings.WHOOSH_PATH)
    except index.EmptyIndexError:
        ix = create_index()
    else:
        logger.debug('Search Index opened.')
    return ix


def add_item(ix, pp: PikiPage):
    # Define Standard data
    #
    data = dict(
        id=pp.rel_path,
        #
        title=pp.title,
        page_src=pp.page_txt,
        tag=pp.tags,
        #
        creation_time=pp.creation_time,
        modified_time=pp.modified_time,
        modified_user=None if pp.modified_user is None else pp.modified_user.username
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


def delete_item(ix, pp: PikiPage):
    with ix.writer() as w:
        logger.info('Removing document with id=%s from the search index.', pp.rel_path)
        w.delete_by_term("id", pp.rel_path)


def update_item(pp: PikiPage):
    ix = load_index()
    delete_item(ix, pp)
    add_item(ix, pp)
