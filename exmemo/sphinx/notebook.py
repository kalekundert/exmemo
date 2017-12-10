#!/usr/bin/env python3

import re
from .. import Workspace
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.roles import XRefRole
from pprint import pprint


def add_expts_to_toc(app, docname, source):
    """
    Update the main TOC with the list of all the experiments.

    The source argument is a list whose single element is the contents of the 
    source file. You can process the contents and replace this item to 
    implement source-level transformations.
    """
    if docname != 'index':
        return

    work = Workspace.from_dir(app.srcdir)
    entries = [
            str(work.get_notebook_entry(x).relative_to(app.srcdir))
            for x in sorted(work.iter_experiments())]

    source[0] = source[0].format(notebook_entries='\n   '.join(entries))

def add_dates_to_toc(app, doctree):
    """
    Prefix the TOC entries for each experiment with a date.

    The dates are added as literal text so that they will line up with each 
    other vertically.
    """
    docname = app.env.docname

    if docname == 'index':
        return

    try:
        ref = app.env.tocs[docname][0][0][0]
        match = re.match('(\d{8})_.*', docname)
    except:
        return

    if match:
        date, pad = match.group(1), ' '
        ref.insert(0, nodes.literal(date, date))
        ref.insert(1, nodes.Text(pad, pad))

def pubmed_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Insert a citation (including the authors, title, journal, and publication 
    date) given any valid PubMed identifier (i.e. PMID, PMCID, or DOI).

    For example:
        :pubmed:`10.1093/nar/gkw908`

    Arguments
    =========
    name:       The role name used in the document.
    rawtext:    The entire markup snippet, with role.
    text:       The text marked with the role.
    lineno:     The line number where rawtext appears in the input.
    inliner:    The inliner instance that called us.
    options:    Directive options for customization.
    content:    The directive content for customization.

    Returns
    =======
    A 2 part tuple containing a list of nodes to insert into the document and a 
    list of system messages.  Both are allowed to be empty.
    """

    import metapub
    import requests

    # Look up the article metadata on PubMed.  The method is called 
    # `article_by_doi()`, but it will also find PMIDs and PMCIDs.
    try:
        pubmed = metapub.PubMedFetcher()
        meta = pubmed.article_by_doi(text)

    # Give a useful error message is the article can't be found.
    except metapub.exceptions.MetaPubError as e:
        error = inliner.reporter.error(str(e), line=lineno)
        problem = inliner.problematic(rawtext, rawtext, error)
        return [problem], [error]

    except requests.exceptions.ConnectionError as e:
        error = inliner.reporter.warning("Couldn't connect to PubMed, may be offline.", line=lineno)
        p = nodes.paragraph(text, text)
        return [p], [error]

    # Make a paragraph containing the citation.
    p = nodes.paragraph(meta.citation, meta.citation)
    return [p], []

class ExperimentRole(XRefRole):
    """
    Make a hyperlink to another experiment.
    
    For example:
        :expt:`20170329_test_multiple_spacers`
    """
    innernodeclass = nodes.inline

    def __init__(self):
        # Copying from sphinx/domains/std.py:489
        super().__init__(warn_dangling=True)

    def process_link(self, env, refnode, has_explicit_title, title, target): #
        """
        Called after parsing title and target text, and creating the
        reference node (given in *refnode*).  This method can alter the
        reference node and must return a new (or the same) ``(title, target)``
        tuple.
        """
        refnode['refdomain'] = 'std'
        refnode['reftype'] = 'doc'

        slug = target.split('_', 1)[1]
        link = f'/{target}/{slug}'

        return super().process_link(env, refnode,
                has_explicit_title, title, link)


class UpdateDirective(Directive):
    """
    Define a directive specifically for adding new information to existing 
    notebook entries.

    .. update:: Dec 6, 2017

        Based on feedback I got at the conference, I repeated the analysis 
        for this experiment using method X...

    This directive takes a date as a positional argument, and then any amount 
    of text in an indented block.  It will render a box containing the given 
    text with a header that reads "Update — {date}".
    """
    required_arguments = 1  # <date>
    has_content = True
    final_argument_whitespace = True

    def run(self): #
        # Create the root admonition node.
        content = '\n'.join(self.content)
        options = {'classes': ['note']}
        admonition = nodes.admonition(content, **options)

        # Create the title node.
        title = f"Update — {self.arguments[0]}"
        text_nodes, _ = self.state.inline_text(title, self.lineno)
        title = nodes.title(title, '', *text_nodes)
        title.source, title.line = \
                self.state_machine.get_source_and_line(self.lineno)
        admonition += title

        # Create the content node.
        self.state.nested_parse(self.content, self.content_offset, admonition)

        return [admonition]

class ShowNodesDirective(Directive):
    """
    Pretty print all the nodes in the restructured-text contained in this 
    directive.  This is only meant to be a tool for developing and debugging 
    new Sphinx extensions.

    .. show-nodes::

        .. figure:: path/to/image.png

            A schematic of the reaction setup.
    """
    has_content = True

    def run(self): #
        wrapper = nodes.paragraph()
        self.state.nested_parse(self.content, self.content_offset, wrapper)

        for node in wrapper.children:
            print(node.pformat())

        return wrapper.children


def setup(app):
    app.connect('source-read', add_expts_to_toc)
    app.connect('doctree-read', add_dates_to_toc)

    app.add_role('expt', ExperimentRole())
    app.add_role('pubmed', pubmed_role)

    app.add_directive('update', UpdateDirective)
    app.add_directive('show-nodes', ShowNodesDirective)
