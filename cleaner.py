import os
from pathlib import Path
import io
import bibtexparser
import pandas
import yaml
from bibtexparser.bibdatabase import BibDatabase, BibDataStringExpression, BibDataString
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import type as bib_type
from bibtexparser.customization import author, editor, journal, keyword, link, page_double_hyphen, doi, convert_to_unicode
import logging

logging.getLogger().setLevel(logging.INFO)


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
    def __init__(self, bibtex, output, keepkey=False, verbose=True, concise=False, stream=False,):
        self.bibtex = bibtex
        self.output = output
        self.keepkey = keepkey
        self.verbose = verbose
        self.concise = concise
        self.stream = stream
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

    def clean_output(self, data, bib_id, status):
        data = data.fillna(' ').astype(str).to_dict(orient='records')
        if self.verbose:
            if status:
                logging.info("Matched key {} to Anthology paper ID {}".format(bib_id, data[0].get('ID')))
            else:
                logging.info("Could not match key {}.".format(data[0].get('ID')))
        if self.keepkey:
            data[0]['ID'] = bib_id
        return data[0]

    def match(self, *args):
        title_df = self.match_title(args[0].get('title'))
        if title_df.empty or len(title_df) > 1:
            authors_df = self.match_authors(args[0].get('author')) if title_df.empty else self.match_authors(args[0].get('author'), inp=title_df)
            if authors_df.empty:
                if self.verbose:
                    logging.info("Could not match key {}.".format(args[0].get('ID')))
                return args[0]
            elif len(authors_df) > 1:
                date_df = self.match_date(authors_df, args[0].get('year'))
                if date_df.empty:
                    if self.verbose:
                        logging.info("Could not match key {}.".format(args[0].get('ID')))
                    return args[0]
                else:
                    return self.clean_output(date_df, args[0].get('ID'), True)
            else:
                return self.clean_output(authors_df, args[0].get('ID'), True)
        else:
            return self.clean_output(title_df, args[0].get('ID'), True)

    def clean(self):
        bibstream = open(self.bibtex) if not self.stream else io.StringIO(self.bibtex)
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bibdata = bibtexparser.load(bibstream, parser=parser)
        output = list(map(self.match, bibdata.entries))

        db = BibDatabase()
        bibcontent = [i for i in output]

        for bib in bibcontent:
            cleaned_bib = {k: v.replace('\n', '') for k, v in bib.items() if len(v) != 1}

            if self.concise:
                cleaned_bib['publisher'] = self.get_publish()
                to_remove = ["abstracts"]
                cleaned_bib = {k: v for k, v in cleaned_bib.items() if k not in to_remove}
            db.entries = [cleaned_bib]
            writer = Writer()
            writer.order_entries_by = ('ID', 'title', 'author', 'booktitle', 'month', 'year', 'address', 'publisher', 'url', 'pages')
            writer.indent = '  '
            writer.align_values = True
            if Path(self.output).exists():
                with open(self.output, 'w') as bibfile:
                    bibfile.write(writer.write(db))
            else:
                print(writer.write(db))
        return True

    def get_publish(self):
        with open(self.venues_path, 'r') as f:
            venues = yaml.load(f)
        return True
