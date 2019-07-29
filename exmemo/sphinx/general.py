#!/usr/bin/env python3

import json
import datetime
import docutils.core
import openpyxl

from pathlib import Path
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from jinja2 import Environment, FileSystemLoader

PLUGIN_DIR = Path(__file__).parent

class DataTable(Directive):
    """
    Create a table using the data from the given spreadsheet file.

    The table will be rendered in the browser using a javascript library that 
    makes the data selectable and sortable as if it were in Excel.  A caption 
    describing the data will be rendered below the table, if provided.
    
    Usage:
        .. datatable:: <xlsx>

            [<caption>]

    Arguments:
        <path>
            The path to an *.xlsx file.
            
        <caption>
            A description of the table.  Typically this would include a brief 
            title and detailed descriptions of each column.

    Options:
        :sheet:
            Which sheet to display.  The default is to display the first.
        :range:
            Which cells to display, e.g. "A1:E5".  The default is to display 
            all cells in the chosen worksheet.

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

        sphinx_env = self.state.document.settings.env

        xlsx_path = Path(self.arguments[0])
        sheet_name = self.options.get('sheet')
        range = self.options.get('range')

        div_ids = ['datatable', xlsx_path.stem]
        xlsx_path_root, xlsx_path_abs = sphinx_env.relfn2path(str(xlsx_path))
        sphinx_env.note_dependency(xlsx_path_root)

        book = openpyxl.load_workbook(filename=xlsx_path_abs, data_only=True)

        if sheet_name and sheet_name not in book.sheetnames:
            msg = f"sheet '{sheet_name}' does not exist"
            return [document.reporter.warning(msg, line=self.lineno)]

        if sheet_name:
            sheet = book[sheet_name]
            div_ids.append(sheet_name)
        else:
            sheet = book.worksheets[0]

        if range:
            sheet_data = sheet[range]
        else:
            sheet_data = sheet

        # Remove unlabeled columns and empty rows.

        header = list(sheet_data.values)[0]
        header_i = set(
                i for i, cell in enumerate(header)
                if cell is not None
        )
        rows = [
                row for row in list(sheet_data.values)[1:]
                if not set(row) == set([None])
        ]
        table = [
                [cell for i, cell in enumerate(row) if i in header_i]
                for row in rows
        ]

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
                'data': to_json(table),
                'caption': ' '.join(self.content),
                'header': to_json([x for x in header if x is not None]),
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

def to_json(data):

    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.date):
                return obj.strftime('%Y-%m-%d')
            if isinstance(obj, datetime.datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            return json.JSONEncoder.default(self, obj)

    return json.dumps(data, cls=DateTimeEncoder)


def setup(app):
    app.add_directive('datatable', DataTable)
    app.add_stylesheet(str(PLUGIN_DIR / 'static' / 'handsontable.full.min.css'))
    #app.add_javascript(str(PLUGIN_DIR / 'static' / 'handsontable.full.min.js'))

