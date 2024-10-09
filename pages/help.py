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

SEARCH = mycreole.render_simple(_(
    """
= Search
The search looks up full words in //title (page basename)// and //page_src (the creole source)// without giving \
special search commands in the search string.

=== Search fields
* title (TEXT)
* page_src (TEXT)
* creation_time (DATETIME)
* modified_time (DATETIME)
* modified_user (TEXT)

== Search syntax (Whoosh)
=== Logic operators
* AND
** **Example:** "foo AND bar" - Search will find all items with foo and bar.
* OR
** **Example:** "foo OR bar" - Search will find all items with foo, bar or with foo and bar.
* NOT
** **Example:** "foo NOT bar" - Search will find all items with foo and no bar.
=== Search in specific fields
A search pattern like //foo:bar// does look for //bar// in the field named //foo//.

This search pattern can also be combined with other search text via logical operators.
=== Search for specific content
* **Wildcards:**
* **Range:**
** From To:
** Above:
** Below:
* **Named constants:**
** //now//: Current date
** //-[num]y//: Current date minus [num] years
** //+[num]mo//: Current date plus [num] months
** //-[num]d//: Current date minus [num] days
** ...

== Examples
* [[/search/?q=modified_user:system-page|modified_user:system-page]] results in a list of all system pages.
* [[/search/?q=modified_time%3A%5B-5d+to+now%5D| modified_time:[-5d to now] ]] results in a list of all pages which have been modified within the last 5 days.
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
