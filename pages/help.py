from django.utils.translation import gettext as _
import mycreole
import pages
from themes import color_icon_url


HELP_UID = 'help'

MAIN = mycreole.render_simple(_(
    """
= Piki

**piki** is a minimal wiki implemented with python and django.

== Help
* [[creole|Creole Markup Language]]
* [[access|Access Control for the site content]]
* [[search|Help on Search]]
"""))

CREOLE = mycreole.mycreole_help_pagecontent()
CREOLE += mycreole.render_simple("""
= Piki Markup
| {{{[[rel_path_to_page|Name]]}}} | will result in a Link to the given wiki page. |
| {{{<<subpages>>}}}              | will result in a list of all subpages below the current page. |
| {{{<<subpages=N,startswith>>}}} | will result in a list of subpages below the current page.\
                                    N will reduce the depth of the subpages to N. \
                                    startswith  will reduce the hits to all pages starting with the given string. \
                                    You can give one or both Parameters. |
| {{{<<allpages>>}}}              | will result in a last of all pages. You can use [N,startswith] as with subpages. |
""")

ACCESS = mycreole.render_simple(_("""
= TBD
"""))

SEARCH = mycreole.render_simple(_("""
= TBD
"""))

help_pages = {
    'main': MAIN,
    'creole': CREOLE,
    'access': ACCESS,
    'search': SEARCH,
}


def actionbar(context, request, current_help_page=None, **kwargs):
    actionbar_entries = (
        ('1', 'Main'),
        ('2', 'Creole'),
        ('3', 'Access'),
        ('4', 'Search'),
    )
    for num, name in actionbar_entries:
        context[context.ACTIONBAR].append_entry(
            HELP_UID + '-%s' % name.lower(),                        # uid
            _(name),                                                # name
            color_icon_url(request, num + '.png'),                  # icon
            pages.url_helpview(request, name.lower()),              # url
            True,                                                   # left
            name.lower() == current_help_page,                      # active
        )
