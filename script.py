#!/usr/bin/env python

import click
from cleaner import ACLCleaner


@click.command()
@click.argument('bibtex', type=click.Path())
@click.option('--output', type=click.Path())
@click.option('--keepkey', type=click.INT, default=1, help='Keep current key')
def aclbibcleaner(bibtex, output, keepkey):
    output = output if output else "cleaned_bib.bib"
    cleaner = ACLCleaner(bibtex, output, keepkey)
    return cleaner.clean()


if __name__ == '__main__':
    aclbibcleaner()


