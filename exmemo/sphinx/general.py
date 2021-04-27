#!/usr/bin/env python3

import docutils.core
import pandas as pd

from pathlib import Path
from functools import partial
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from jinja2 import Environment, FileSystemLoader

PLUGIN_DIR = Path(__file__).parent

class DataTable(SphinxDirective):
    """
    Create a table using the data from the given spreadsheet file.

    The table will be rendered in the browser using a javascript library that 
    makes the data selectable and sortable as if it were in Excel.  A caption 
    describing the data will be rendered below the table, if provided.
    
    Usage:
        .. datatable:: <path>

            [<caption>]

    Arguments:
        <path>
            The path to a file containing the tabular data to display.  The 
            following formats are supported: CSV, TSV, XLS, XLSX
            
        <caption>
            A description of the table.  Typically this would include a brief 
            title and detailed descriptions of each column.

    Derived from `sphinxcontrib-excel-table` by `hackerain`.
    """

    # Possible features:
    # - Provide link to download the underlying file.
    # - Show a summary if the table exceeds some (configurable) limits.

    required_arguments = 1
    has_content = True
    final_argument_whitespace = True
    option_spec = {
        'sheet': directives.unchanged,
        'range': directives.unchanged,
    }

    def run(self):
        # Parse the indicated parts of the given file (e.g. worksheets, rows, 
        # selections, etc.) into a list-of-lists data structure (`table`).

        data_path = Path(self.arguments[0])
        sheet_name = self.options.get('sheet') or 0
        range = self.options.get('range')

        div_ids = ['datatable', data_path.stem, str(sheet_name)]
        data_path_root, data_path_abs = self.env.relfn2path(str(data_path))
        self.env.note_dependency(data_path_root)

        if not Path(data_path_abs).exists():
            raise self.error(f"data table not found: {data_path}")

        parsers = {
                '.csv': pd.read_csv,
                '.tsv': partial(pd.read_csv, sep='\t'),
                '.xls': partial(pd.read_excel, sheet_name=sheet_name),
                '.xlsx': partial(pd.read_excel, sheet_name=sheet_name),
        }

        try:
            parser = parsers[data_path.suffix]
        except KeyError:
            return [document.reporter.error(f"no known parser for '{datapath.suffix}'", line=self.lineno)]

        table = parser(data_path_abs)
        header = pd.Series(table.columns)

        # Render the table in HTML/javascript using `handsontable`.

        jinja_context = {
                # This kinda sucks.  The normal way to get Sphinx to use a 
                # javascript file to Sphinx is to call `app.add_javascript()` 
                # in `setup()`.  But this adds the script at the end of <body>, 
                # and I need Handsontable to be defined in the middle of where 
                # this element occurs.  I tried using jquery to postpone the 
                # evaluation of this element, but the RTD theme doesn't load 
                # jquery until the end of <body>.
                'handsontable_js': PLUGIN_DIR / 'static' / 'handsontable.full.min.js',

                'div_id': '_'.join(div_ids),
                'data': table.to_json(orient='values'),
                'caption': ' '.join(self.content),
                'header': header.to_json(orient='values'),
        }
        jinja_env = Environment(
                loader=FileSystemLoader(str(PLUGIN_DIR / 'templates')),
                keep_trailing_newline=True,
                trim_blocks=True,
                lstrip_blocks=True,
        )
        jinja_template = jinja_env.get_template('datatable.html')

        html = jinja_template.render(**jinja_context)
        return [docutils.nodes.raw('', html, format='html')]


def setup(app):
    app.add_directive('datatable', DataTable)
    app.add_css_file(str(PLUGIN_DIR / 'static' / 'handsontable.full.min.css'))
    #app.add_javascript(str(PLUGIN_DIR / 'static' / 'handsontable.full.min.js'))

