import os
from pathlib import Path
import bibtexparser
import pandas
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import type as bib_type
from bibtexparser.customization import author, editor, journal, keyword, link, page_double_hyphen, doi, convert_to_unicode


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
    def __init__(self, bibtex, output):
        self.bibtex = bibtex
        self.output = output
        self.anthology_path = list(Path(os.path.dirname(__file__)).joinpath('data').iterdir())[0]
        self.bibdata = pandas.read_csv(self.anthology_path, low_memory=False)

    def match_title(self, value):
        m = self.bibdata[self.bibdata.title.str.contains(value, regex=False)]
        return m

    def match_authors(self, value, inp=None):
        value = " ".join(value)
        print(value)
        m = inp[inp.author.str.contains(value, na=False)] if inp is not None else self.bibdata[self.bibdata.author.str.contains(value, na=False)]
        return m

    def match_date(self, inp, year):
        m = inp[inp['year'] == int(year)]
        return m

    def clean_output(self, data, bib_id):
        data = data.fillna(' ').astype(str).to_dict(orient='records')
        data[0]['ID'] = bib_id
        return data

    def match(self, *args):
        title = self.match_title(args[0].get('title'))
        if title.empty or len(title) > 1:
            authors = self.match_authors(args[0].get('author')) if title.empty else self.match_authors(args[0].get('author'), inp=title)
            if authors.empty:
                print("NO MATCH FOUND FOR {}".format(args[0].get('title')))
                return args[0]
            elif len(authors) > 1:
                date = self.match_date(authors, args[0].get('year'))
                if date.empty:
                    print("NO MATCH FOUND FOR {}".format(args[0].get('title')))
                    return args[0]
                else:
                    return self.clean_output(date, args[0].get('ID'))
            else:
                return self.clean_output(authors, args[0].get('ID'))
        else:
            return self.clean_output(title, args[0].get('ID'))

    def clean(self):
        with open(self.bibtex) as bibfile:
            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            bibdata = bibtexparser.load(bibfile, parser=parser)
        out = []
        output = list(map(self.match, bibdata.entries))
        out.append(output)

        db = BibDatabase()
        with open(self.output, 'w') as bibfile:
            for bib in out[0]:
                db.entries = bib
                writer = BibTexWriter()
                writer.indent = '  '
                writer.align_values = True
                bibfile.write(writer.write(db))
        return True
