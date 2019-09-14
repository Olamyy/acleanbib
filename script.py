#!/usr/bin/env python

import click
from cleaner import ACLCleaner


@click.command()
@click.argument('bibtex', type=click.Path())
@click.option('--output', type=click.Path())
@click.option('--keepkey', type=click.INT, default=1, help='Keep current key')
@click.option('--concise', type=click.INT, default=1, help='Do deep cleaning.')
@click.option('--show_output', type=click.INT, default=0, help="Show cleaning report in a table")
@click.option('--write_to_file', type=click.INT, default=0, help="Write output to file")
def aclbibcleaner(bibtex, output, keepkey, concise, show_output, write_to_file):
    output = output if output else "cleaned_bib.bib"
    cleaner = ACLCleaner(bibtex, output, keepkey, concise=concise, show_output=show_output, write_to_file=write_to_file)
    return cleaner.clean()


if __name__ == '__main__':
    aclbibcleaner()


