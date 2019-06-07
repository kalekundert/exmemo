#!/usr/bin/env python3

import re
import time
from .. import app, Workspace
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.roles import XRefRole
from pathlib import Path

from html.parser import HTMLParser

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

def doi_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
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

    # There are some inefficiencies due to this function being called once for 
    # each role.  Ideally we'd like to only load the cache once, and ask for 
    # all the DOIs we care about in a single request to the Crossref.  There's 
    # probably a way to do this, but it would require some coordination between 
    # roles.

    # Dealing with all the roles together might also give me a way to line them 
    # up in a <table>.  Maybe I want a bibliography directive or something...

    # Also, would be nice to have formatting in the citations (i.e. bold, 
    # italic, etc.) and to have a link to the actual paper (via the DOI).

    import json
    import habanero
    import requests

    # Try to cache queries.
    cache_path = Path(app.user_cache_dir) / 'crossref.json'
    cache = {}

    if cache_path.exists():
        with cache_path.open() as f:
            cache = json.load(f)

    if text in cache:
        meta = cache[text]

    else:
        # Look up the article metadata on CrossRef.
        try:
            crossref = habanero.Crossref(mailto='kale_kundert@hms.harvard.edu')
            meta = crossref.works(ids=[text])['message']

            # The reference list is big, and we don't care about it, so don't 
            # cache it.
            if 'reference' in meta:
                del meta['reference']

            cache[text] = meta
            cache_path.parent.mkdir(exist_ok=True)
            with cache_path.open('w') as f:
                json.dump(cache, f)

        # Give a useful warning if the article can't be found.
        except requests.exceptions.HTTPError as e:
            warning = inliner.reporter.warning(f"No matches found for DOI: {text}", line=lineno)
            p = nodes.paragraph(text, text)
            return [p], [warning]

        except requests.exceptions.ConnectionError as e:
            warning = inliner.reporter.warning("Couldn't connect to CrossRef, may be offline.", line=lineno)
            p = nodes.paragraph(text, text)
            return [p], [warning]

    # Make a paragraph containing the citation.

    def format_author(author):
        initials = ''.join(x[0] for x in author['given'].split())
        return f"{author['family']} {initials}"

    def format_authors(authors):
        authors = [format_author(x) for x in authors]

        if len(authors) == 1:
            return authors[0]
        elif len(authors) < 5:
            return ", ".join(x for x in authors[:-1]) + " & " + authors[-1]
        else:
            return f"{authors[0]} et al"

    def format_title(meta):
        return meta['title'][0]

    def format_journal_issue_date(meta):
        issue = ':'.join(
                meta[k] for k in ('volume', 'issue', 'page')
                if k in meta
        )
        if issue:
            issue += ' '

        return f"{meta['container-title'][0]} {issue}({meta['issued']['date-parts'][0][0]})"

    citation = (
            f"{format_authors(meta['author'])}. "
            f"{format_title(meta)}. "
            f"{format_journal_issue_date(meta)}. "
    )

    p = nodes.paragraph(citation, citation)
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



class ProtocolDirective(Directive):

    optional_arguments = 1
    has_content = True

    def run(self):
        protocol = ProtocolNode()

        self.state.nested_parse(self.content, self.content_offset, protocol)

        if self.arguments:
            from sphinx.directives.code import LiteralIncludeReader
            from sphinx.util.nodes import set_source_info

            # <literal_block highlight_args="{'linenostart': 1}" linenos="False" source="/home/kale/research/projects/201904_bind_dna/notebook/20190604_dnase_pick_qpcr_primers/20190604_pcr.txt" xml:space="preserve">
            #     ...

            # From `sphinx/directives/code.py`:

            env = self.state.document.settings.env
            location = self.state_machine.get_source_and_line(self.lineno)
            rel_filename, filename = env.relfn2path(self.arguments[0])
            env.note_dependency(rel_filename)

            reader = LiteralIncludeReader(filename, self.options, env.config)
            text, lines = reader.read(location=location)

            literal = nodes.literal_block(text, text, source=filename)
            set_source_info(self, literal)

            protocol += literal

        else:
            print("No args, skipping.")

        paragraph = nodes.paragraph()
        paragraph += protocol
        return [paragraph]

class ProtocolNode(nodes.General, nodes.Element):

    @staticmethod
    def visit(visitor, node):
        visitor.body.append('<details class="protocol"><summary>Protocol</summary>')

    @staticmethod
    def depart(visitor, node):
        visitor.body.append('</details>')



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
    app.add_role('doi', doi_role)

    app.add_directive('update', UpdateDirective)
    app.add_directive('show-nodes', ShowNodesDirective)

    app.add_directive('protocol', ProtocolDirective)
    app.add_node(ProtocolNode,
            html=(ProtocolNode.visit, ProtocolNode.depart),
    )

    css_path = Path(__file__).parent / 'tweaks.css'
    app.add_stylesheet(str(css_path))
