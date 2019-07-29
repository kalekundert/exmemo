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
    
    Usage:

        :expt:`20170329_test_multiple_spacers`

    You must specify the full name to the experiment, including the date.
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
    """
    Display protocols in a collapsible widget.

    Usage:

        .. protocol:: <file-1> <file-2> ... <file-N>

            <restructured text>

            [***]

            <restructured text>

            ...

    It's important for protocols to be as detailed as possible, but it's 
    annoying when this detail overwhelms your notebook and gets in the way of 
    data and conclusions that are usually more interesting.  The `protocol` 
    directive helps with this by making protocols collapsible.  It also helps 
    combine protocol information from files (e.g. what you were trying to do) 
    and free-form text (e.g. what you actually did).

    Any number of files can be specified as optional arguments.  These 
    files will be incorporated into the document in the order specified.  Text 
    files (i.e. files with the extension ".txt") will be copied into a 
    preformatted block.  Any other files will made available to download.  The 
    file arguments are separated by spaces.  Use quotes or backslashes (as you 
    would in the shell) to escape any file names containing spaces.

    The body of this directive can contain any regular restructured text.  By 
    default, this text will be shown above any protocol files.  You can use 
    also the pattern "***", alone on its own line, to control where your 
    annotations appear with respect to the protocol files.  Each use of "***" 
    will be replaced by the next protocol file to be displayed.  It's ok to 
    specify "***" fewer times than there are protocol files; any left-over 
    files will just be put at the end.
    """

    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        from more_itertools import interleave_longest

        protocol = ProtocolNode()

        if not self.content and not self.arguments:
            self.state.inliner.reporter.warning(f"empty protocol.")

        def split_arguments():
            import shlex
            if not self.arguments:
                return
            for path in shlex.split(self.arguments[0]):
                yield Path(path)

        def split_content():
            content_blocks = []

            # Use slicing to split the blocks, because this automatically makes 
            # properly configured docutils.statemachine.StringList views.
            i = 0
            for j, line in enumerate(self.content):
                if line.strip() == '***':
                    content_blocks += [self.content[i:j]]
                    i = j + 1

            content_blocks += [self.content[i:]]
            return content_blocks

        def attach_literal_node(path):
            from sphinx.directives.code import LiteralIncludeReader
            from sphinx.util.nodes import set_source_info
            nonlocal protocol

            if path.suffix == '.txt':
                # <literal_block highlight_args="{'linenostart': 1}" 
                # linenos="False" 
                # source="/home/kale/research/projects/201904_bind_dna/notebook/20190604_dnase_pick_qpcr_primers/20190604_pcr.txt" 
                # xml:space="preserve">
                #     ...

                # From `sphinx/directives/code.py`:
                env = self.state.document.settings.env
                location = self.state_machine.get_source_and_line(self.lineno)
                rel_filename, filename = env.relfn2path(str(path))
                env.note_dependency(rel_filename)

                reader = LiteralIncludeReader(filename, self.options, env.config)
                text, lines = reader.read(location=location)

                literal_node = nodes.literal_block(text, text, source=filename)
                set_source_info(self, literal_node)

                protocol += [literal_node]

            else:
                from sphinx.roles import specific_docroles
                protocol += specific_docroles['download'](
                        'download',
                        rawtext=str(path),
                        text=str(path),
                        lineno=self.lineno,
                        inliner=self.state.inliner,
                )[0]

        def attach_content_node(content):
            if content:
                self.state.nested_parse(content, content.offset(0), protocol)

        content = [(attach_content_node, x) for x in split_content()]
        literal = [(attach_literal_node, x) for x in split_arguments()]

        for add_to_protocol, *args in interleave_longest(content, literal):
            add_to_protocol(*args)

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

    Usage:

        .. update:: <date>

            <restructured text>

    This directive takes a date as a positional argument (typically a date), 
    and then any amount of text in an indented block.  It will render a box 
    containing the given text with a header that reads "Update — {argument}".
    """
    required_arguments = 1  # <date>
    final_argument_whitespace = True
    has_content = True

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

    Example:

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
