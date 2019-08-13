#!/usr/bin/env python

import click
from cleaner import ACLCleaner


@click.command()
@click.argument('bibtex', type=click.Path())
@click.option('--output', type=click.Path())
@click.option('--interactive', type=click.INT, default=1, help='Interactively confirm matches')
def aclbibcleaner(bibtex, output, interactive):
    output = output if output else "cleaned_bib.bib"
    cleaner = ACLCleaner(bibtex, output)
    return cleaner.clean()
