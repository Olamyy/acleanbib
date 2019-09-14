import os
from pathlib import Path
import bibtexparser
import pandas
import yaml
from bibtexparser.bibdatabase import BibDatabase, BibDataStringExpression, BibDataString
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import type as bib_type
from bibtexparser.customization import author, editor, journal, keyword, link, page_double_hyphen, doi, convert_to_unicode
from tabulate import tabulate
import logging

logger = logging.getLogger('aclean')


def _str_or_expr_to_bibtex(e):
    if isinstance(e, BibDataStringExpression):
        return ' # '.join([_str_or_expr_to_bibtex(s) for s in e.expr])
    elif isinstance(e, BibDataString):
        return e.name
    else:
        return '"{}"'.format(e)


class Writer(BibTexWriter):
    def write(self, bib_database):
        bibtex = ''
        for content in self.contents:
            try:
                bibtex += getattr(self, '_' + content + '_to_bibtex')(bib_database)
            except AttributeError:
                print("BibTeX item '{}' does not exist and will not be written. Valid items are {}.".format(content, self._valid_contents))
        return bibtex

    def _entry_to_bibtex(self, entry):
        bibtex = ''
        bibtex += '@' + entry['ENTRYTYPE'] + '{' + entry['ID']
        display_order = [i for i in self.display_order if i in entry]
        display_order += [i for i in sorted(entry) if i not in self.display_order]
        if self.comma_first:
            field_fmt = u"\n{indent}, {field:<{field_max_w}} = {value}"
        else:
            field_fmt = u",\n{indent}{field:<{field_max_w}} = {value}"
        for field in [i for i in display_order if i not in ['ENTRYTYPE', 'ID']]:
            try:
                bibtex += field_fmt.format(
                    indent=self.indent,
                    field=field,
                    field_max_w=self._max_field_width,
                    value=_str_or_expr_to_bibtex(entry[field]))
            except TypeError:
                raise TypeError(u"The field %s in entry %s must be a string"
                                % (field, entry['ID']))
        if self.add_trailing_comma:
            if self.comma_first:
                bibtex += '\n' + self.indent + ','
            else:
                bibtex += ','
        bibtex += "\n}\n" + self.entry_separator
        return bibtex


def customizations(record):
    record = bib_type(record)
    record = author(record)
    record = editor(record)
    record = journal(record)
    record = keyword(record)
    record = link(record)
    record = page_double_hyphen(record)
    record = doi(record)
    return record


class ACLCleaner(object):
    def __init__(self, bibtex, output, keepkey=True, show_output=False, concise=False, write_to_file=False):
        self.bibtex = bibtex
        self.output = output
        self.keepkey = keepkey
        self.show_ouput = show_output
        self.concise = concise
        self.write_to_file = write_to_file
        self.anthology_path = list(Path(os.path.dirname(__file__)).joinpath('data').iterdir())[1]
        self.venues_path = list(Path(os.path.dirname(__file__)).joinpath('data').iterdir())[0]
        self.bibdata = pandas.read_csv(self.anthology_path, compression='zip', low_memory=False)

    def match_title(self, value):
        m = self.bibdata[self.bibdata.title.str.contains(value[:-1], regex=False)]
        return m

    def match_authors(self, value, inp=None):
        value = " ".join(value)
        m = inp[inp.author.str.contains(value, na=False)] if inp is not None else self.bibdata[self.bibdata.author.str.contains(value, na=False)]
        return m

    def match_date(self, inp, year):
        m = inp[inp['year'] == int(year)]
        return m

    def clean_output(self, data, bib_id):
        data = data.fillna(' ').astype(str).to_dict(orient='records')
        if self.keepkey:
            data[0]['ID'] = bib_id
        return data[0]

    def match(self, *args):
        title = self.match_title(args[0].get('title'))
        if title.empty or len(title) > 1:
            authors = self.match_authors(args[0].get('author')) if title.empty else self.match_authors(args[0].get('author'), inp=title)
            if authors.empty:
                return False, args[0]
            elif len(authors) > 1:
                date = self.match_date(authors, args[0].get('year'))
                if date.empty:
                    return False, args[0]
                else:
                    return True, self.clean_output(date, args[0].get('ID'))
            else:
                return True, self.clean_output(authors, args[0].get('ID'))
        else:
            return True, self.clean_output(title, args[0].get('ID'))

    def clean(self):
        with open(self.bibtex) as bibfile:
            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            bibdata = bibtexparser.load(bibfile, parser=parser)
        out = []
        output = list(map(self.match, bibdata.entries))
        out.append(output)

        if self.show_ouput:
            report = [[i[1].get('title'), i[0]] for i in out[0]]
            print(tabulate(report, headers=["Paper", "Match Found"], tablefmt="github"))

        db = BibDatabase()
        bibcontent = [i[1] for i in out[0]]
        with open(self.output, 'w') as bibfile:
            for bib in bibcontent:
                cleaned_bib = {k: v for k, v in bib.items() if len(v) != 1}

                if self.concise:
                    cleaned_bib['publisher'] = self.get_publish()
                    to_remove = ["abstracts"]
                    cleaned_bib = {k: v for k, v in cleaned_bib.items() if k not in to_remove}
                db.entries = [cleaned_bib]
                writer = Writer()
                writer.order_entries_by = ('ID', 'title', 'author', 'booktitle', 'month', 'year', 'address', 'publisher', 'url', 'pages')
                writer.indent = '  '
                writer.align_values = True
                if self.write_to_file:
                    bibfile.write(writer.write(db))
                else:
                    print(writer.write(db))
        return True

    def get_publish(self):
        with open(self.venues_path, 'r') as f:
            venues = yaml.load(f)
        return True

