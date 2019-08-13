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


if __name__ == '__main__':
    import platform

    print('Python Version      :', platform.python_version())
    print('Version tuple:', platform.python_version_tuple())
    print('Compiler     :', platform.python_compiler())
    print('Build        :', platform.python_build())
    aclbibcleaner()


