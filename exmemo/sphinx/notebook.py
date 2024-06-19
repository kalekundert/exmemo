#!/usr/bin/env python3

import re
import time
from .. import app, Workspace, Experiment, ExperimentNotFound
from docutils import nodes as n
from docutils.parsers.rst import Directive
from docutils.transforms import Transform
from sphinx.roles import XRefRole
from sphinx.transforms import SphinxTransform
from sphinx import addnodes as nn
from pathlib import Path

from html.parser import HTMLParser

class AddIdToTitle(SphinxTransform):
    default_priority = 499

    def apply(self):
        try:
            expt = Experiment.from_sphinx_env(self.env)
        except ExperimentNotFound:
            return

        id_str = f'#{expt.id}: '
        id_node = n.Text(id_str, id_str)

        if title := find_title(self.document):
            title.insert(0, id_node)

class BuildToc(SphinxTransform):
    default_priority = 500

    def apply(self):

        # Find experiments:

        if self.env.docname == self.config.master_doc:
            work = Workspace.from_sphinx_env(self.env)
            toc_expts = work.iter_experiments(recursive=False)

        else:
            try:
                curr_expt = Experiment.from_sphinx_env(self.env)
                toc_expts = curr_expt.iter_experiments_toc()
            except ExperimentNotFound:
                return

        # Create or update the TOC:
        
        toc_refs = [
                ref_from_expt(self.env, expt, absolute=False)
                for expt in sorted(toc_expts, key=lambda x: x.id)
        ]

        # sort...
            
        if toc := find_toc(self.document):
            entries = toc.attributes['entries']
            includes = toc.attributes['includefiles']

            if '.experiments' not in toc.attributes['includefiles']:
                i = len(includes)
            else:
                i = includes.index('.experiments')
                del includes[i]
                del entries[i]

            def expand(l, i, e):
                e = [x for x in e if x not in l]
                return l[:i] + e + l[i:]

            toc.attributes['includefiles'] = expand(includes, i, toc_refs)
            toc.attributes['entries'] = expand(
                    entries, i, 
                    [(None, x) for x in toc_refs]
            )

        else:
            toc = nn.toctree()
            toc['hidden'] = True
            toc['maxdepth'] = -1
            toc['entries'] = []
            toc['includefiles'] = []
            toc['maxdepth'] = -1
            toc['caption'] = ""
            toc['glob'] = False
            toc['hidden'] = True
            toc['includehidden'] = False
            toc['numbered'] = False
            toc['titlesonly'] = False
            toc['entries'] = [(None, x) for x in toc_refs]
            toc['includefiles'] = toc_refs

            if title := find_title(self.document):
                title.parent.append(toc)

class ExperimentRole(XRefRole):
    """
    Make a hyperlink to another experiment by referencing its id number:

        :expt:`1`

    """
    innernodeclass = n.inline

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

        process_link = super().process_link
        defer_to_super = lambda: process_link(
                    env, refnode, has_explicit_title, title, target)

        # Find the experiment being referred to:
        try:
            target_id = int(target)
        except ValueError:
            return defer_to_super()

        if target_id < 0:
            curr_expt = Experiment.from_sphinx_env(env)
            target_expt = curr_expt.get_ancestor(-target_id)

        else:
            try:
                work = Workspace.from_sphinx_env(env)
                target_expt = work.find_experiment(target_id)
            except ExperimentNotFound as err:
                return defer_to_super()

        # Annotate the cross-ref node:
        refnode['refdomain'] = 'std'
        refnode['reftype'] = 'doc'
        ref = ref_from_expt(env, target_expt)

        return super().process_link(
                env, refnode, has_explicit_title, title, ref)



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

                literal_node = n.literal_block(text, text, source=filename)
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

        paragraph = n.paragraph()
        paragraph += protocol
        return [paragraph]

class ProtocolNode(n.General, n.Element):

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
        admonition = n.admonition(content, **options)

        # Create the title node.
        title = f"Update — {self.arguments[0]}"
        text_nodes, _ = self.state.inline_text(title, self.lineno)
        title = n.title(title, '', *text_nodes)
        title.source, title.line = \
                self.state_machine.get_source_and_line(self.lineno)
        admonition += title

        # Create the content node.
        self.state.nested_parse(self.content, self.content_offset, admonition)

        return [admonition]

def find_title(doc):
    return find_first_node(doc, n.title)

def find_toc(doc):
    return find_first_node(doc, nn.toctree)

def find_first_node(doc, cls):

    class FindFirstByClass(n.NodeVisitor):

        def __init__(self, doc, cls):
            super().__init__(doc)
            self.cls = cls
            self.node = None

        def dispatch_visit(self, node):
            if isinstance(node, self.cls):
                self.node = node
                raise n.StopTraversal

    visitor = FindFirstByClass(doc, cls)
    doc.walk(visitor)
    return visitor.node

def ref_from_expt(env, expt, absolute=True):
    rel_path = expt.note_path.relative_to(env.srcdir)
    return f'{"/" if absolute else ""}{rel_path.with_suffix("")}'

def update_note_ids(app):
    work = Workspace.from_dir(app.project.srcdir)
    work.assign_experiment_ids()


def setup(app):
    app.connect('builder-inited', update_note_ids)

    app.add_transform(AddIdToTitle)
    app.add_transform(BuildToc)

    app.add_role('expt', ExperimentRole())

    app.add_directive('update', UpdateDirective)
    app.add_directive('protocol', ProtocolDirective)
    app.add_node(ProtocolNode,
            html=(ProtocolNode.visit, ProtocolNode.depart),
    )

    css_path = Path(__file__).parent / 'tweaks.css'
    app.add_css_file(str(css_path))
