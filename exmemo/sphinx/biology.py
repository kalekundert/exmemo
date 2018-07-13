#!/usr/bin/env python3

## Plugin ideas

# `figure-tif`: A directive that's just like figure, but it uses imagemagick to 
# convert its image from a TIF to a PNG, then copies the PNG to the output 
# directory.

# A way to display a command and the image/plot it generates.

# A directive for listing reagents and product numbers.

## Add an OD600 directive

from docutils import nodes
from docutils.parsers.rst.directives.tables import Table

def dilution(argument): #
    import re
    match = re.match(r'(\d+)x', str(argument))

    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"dilution should be a number followed by 'x' (e.g. '20x'), not '{argument}'")

def make_row(*cells): #
    row = nodes.row()

    for text in map(str, cells):
        entry = nodes.entry()
        entry += [nodes.paragraph(text, text)]
        row += entry

    return row

def make_cols(directive, num_cols): #
    tgroup = nodes.tgroup(cols=num_cols)
    col_widths = directive.get_column_widths(num_cols)

    for w in col_widths:
        colspec = nodes.colspec()
        colspec['colwidth'] = w
        tgroup += colspec

    return tgroup

def align_cols(table, *alignments): #
    for tgroup in table:
        if isinstance(tgroup, nodes.tgroup):
            for child in tgroup:
                if isinstance(child, (nodes.thead, nodes.tbody)):
                    for row in child:
                        for cell, alignment in zip(row, alignments):
                            cell['classes'].append(f'{alignment}-align')

class OdDirective(Table): #
    has_content = True
    option_spec = {
            'title': lambda x: x,
            'dilution': dilution,
            **Table.option_spec
    }
    
    def run(self): #
        table = nodes.table()

        dilution = self.options.get('dilution', None)
        num_cols = 3 if dilution else 2
        col_widths = self.get_column_widths(num_cols)

        tgroup = nodes.tgroup(cols=num_cols)
        table += tgroup

        for w in col_widths:
            colspec = nodes.colspec()
            colspec['colwidth'] = w
            tgroup += colspec

        thead = nodes.thead()
        title = self.options.get('title', 'Strain')

        if dilution:
            thead += make_row(title, f'OD600/{dilution}', 'OD600')
        else:
            thead += make_row(title, 'OD600')

        tbody = nodes.tbody()
        for line in self.content:
            strain, od = line.split(':')

            if dilution:
                real_od = f'{float(dilution) * float(od):0.3f}'
                tbody += make_row(strain, od, real_od)
            else:
                tbody += make_row(strain, od)

        tgroup += thead
        tgroup += tbody

        alignments = ['left'] + (num_cols - 1) * ['right']
        align_cols(table, *alignments)

        return [table]

## Add an electrotransformation directive

# I should rename this directive, now that I'm doing library-scale chemical 
# transformations with yeast.

# .. electrotransformation::
#    :dilutions: 10 ^ 1 2 3 4
#    :plate: 20 μL
# 
#    theo rhi 4,4:
#       colonies: x x 69 5
#       recover: 2032 μL
#       conc: 115.8 ng/μL
#    theo rhi 4,5:
#       colonies: x x 54 10
#       recover: 3070 μL
#       conc: 100.0 ng/μL
#    theo rhi 5,4:
#       colonies: x x 85 7
#       recover: 3057 μL
#       conc: 147.9 ng/μL
#    theo rhi 5,5:
#       colonies: x x 81 10
#       recover: 4089 μL
#       conc: 137.1 ng/μL

# .. electrotransformation::
#    :dilutions: 5 ^ 1 2 3
#    :plate: 20 μL
# 
#    theo ux:
#       colonies: 17 9 2
#       recover: 20800 μL
#       library_size: 1024 + 16384 + 262144

from docutils import nodes
from docutils.parsers.rst.directives.tables import Table
from nonstdlib import sci

class Dilutions: #

    def __init__(self, *args): #
        self.base = None
        self.powers = None
        self.override = None

        if len(args) == 1:
            self.override = args[0]
        elif len(args) == 2:
            self.base, self.powers = args
        else:
            raise ValueError(f"expected 1 or 2 arguments, got {len(args)}.")

    @property #
    def dilutions(self):
        if self.override:
            return self.override
        else:
            return [self.base ** x for x in self.powers]

    @property #
    def labels(self):
        if self.override:
            format = lambda x: sci(x)
        else:
            format = lambda x: sci(x, base=self.base, exp_only=True)

        return [format(x) for x in self.dilutions]

def dilution_list(argument): #
    tokens = argument.split()

    # If the dilution is specified as something like "10 ^ 2 3 4 5", calculate 
    # the dilutions as 10**3, 10**4, etc. and keep note of the fact that all 
    # the dilutions are powers of 10.  This will allow us to make more succinct 
    # column headers later on.
    if len(tokens) > 2 and tokens[1] == '^':
        base = eval(tokens[0])
        powers = list(map(eval, tokens[2:]))
        return Dilutions(base, powers)

    # Otherwise, treat each word as a different dilution.
    else:
        dilutions = map(eval, tokens)
        return Dilutions(dilutions)

def value_in(unit, cast=float): #

    def converter(argument): #
        import re
        unit.replace('μ', '[uμ]')
        value = r'([-+]?[0-9]*\.?[0-9]+)'
        match = re.match(f'({value}) {unit}', str(argument))

        if match:
            return cast(match.group(1))
        else:
            raise ValueError(f"expected a value in {unit} (e.g. '20 {unit}'), not '{argument}'")

    return converter

# Fucks up if wrong number of colony counts are given (shifts subsequent 
# columns over, should either fill with zero or throw error).
#
# Throws exceptions in a few places where it should use directive.error().

class ElectrotransformationDirective(Table): #
    has_content = True
    option_spec = {
            'dilutions': dilution_list,
            'plate': value_in('μL'),
            'recover': value_in('μL'),
            **Table.option_spec
    }
    
    def run(self): #
        data = self.load_data()
        dilutions = self.options.get('dilutions', dilution_list('10 ^ 2 3 4 5'))

        headers = [
                'Library',
                'DNA (ng/μL)',
                'Plated (μL)',
                'Recovered (μL)',
                *[f'CFU/{x}' for x in dilutions.labels],
                '# Transformed',
                '# Unique',
                'Coverage (%)',
                'Coverage (fold)',
        ]

        table = nodes.table()

        num_cols = len(headers)
        tgroup = make_cols(self, num_cols)
        table += tgroup

        thead = nodes.thead()
        thead += make_row(*headers)
        tgroup += thead

        import sys; sys.path.append('/home/kale/sgrna/scripts')
        from count_transformants import count_transformants, parse_library, evaluate_coverage

        tbody = nodes.tbody()
        tgroup += tbody

        for lib in data:
            plate_uL = data[lib]['plate']
            recover_uL = data[lib]['recover']
            num_cfus = data[lib]['colonies']
            num_unique = data[lib].get('library_size')
            if num_unique is not None and not isinstance(num_unique, int):
                num_unique = eval(num_unique)
            num_transformed = count_transformants(
                    recover_uL, plate_uL, num_cfus,
                    dilutions=dilutions.dilutions)
            library_name, library_size = parse_library(lib, num_unique)
            num_unique, percent_coverage, fold_coverage = evaluate_coverage(
                    library_size, num_transformed)
                
            assert len(dilutions.labels) == len(num_cfus)

            tbody += make_row(
                    lib,
                    data[lib].get('conc', '—'),
                    f'{plate_uL:.0f}',
                    f'{recover_uL:.0f}',
                    *num_cfus,
                    f'{sci(num_transformed)}',
                    f'{int(round(num_unique))}',
                    f'{percent_coverage * 100:.1f}%',
                    f'{fold_coverage:.1f}x',
            )

        alignments = ['left'] + (num_cols - 1) * ['right']
        align_cols(table, *alignments)

        return [table]

    def load_data(self): #
        """
        Parse the content of the directive using YAML, then cast things and 
        fill in default values as necessary.
        """
        import yaml
        data = yaml.load('\n'.join(self.content))

        default_plate = self.options.get('plate', 20)
        default_recover = self.options.get('recover', 1100)

        def colonies(argument):
            colonies = []
            for x in argument.split():
                if x in 'xX-*': colonies.append('lawn')
                else: colonies.append(eval(x))
            return colonies

        for lib in data:
            if 'colonies' not in data[lib]:
                raise ValueError(f"'colonies' not specified for '{lib}'")
                
            data[lib]['colonies'] = colonies(data[lib]['colonies'])

            if 'plate' in data[lib]:
                data[lib]['plate'] = value_in('μL')(data[lib]['plate'])
            else:
                data[lib]['plate'] = default_plate

            if 'recover' in data[lib]:
                data[lib]['recover'] = value_in('μL')(data[lib]['recover'])
            else:
                data[lib]['recover'] = default_recover

            if 'conc' in data[lib]:
                data[lib]['conc'] = value_in('ng/μL')(data[lib]['conc'])

        return data

def setup(app):
    # Add some science-themed directives.
    app.add_directive('od', OdDirective)
    app.add_directive('electrotransformation', ElectrotransformationDirective)

