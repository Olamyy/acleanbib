#!/usr/bin/env python

import click
from cleaner import ACLCleaner


@click.command()
@click.argument('bibtex', type=click.Path(), required=False)
@click.argument('output', type=click.Path(), required=False)
@click.option('--keepkey', type=click.INT, default=1, help='Keep current key')
@click.option('--concise/--not-concise', default=False, help='Do deep cleaning')
@click.option('--keepkey/--replace-key', default=False, help='Keep Key')
@click.option('--verbose', '-v/-q', default=False, help="Verbose Logging")
def aclbibcleaner(bibtex, output, keepkey, concise, verbose):
    output = output if output else "cleaned_bib.bib"
    try:
        cleaner = ACLCleaner(bibtex, output, keepkey, concise=concise, verbose=verbose, stream=False)
        return cleaner.clean()
    except TypeError:
        bibtex = click.get_text_stream('stdin').read()
        cleaner = ACLCleaner(bibtex, output, keepkey, concise=concise, verbose=verbose, stream=True)
        return cleaner.clean()


if __name__ == '__main__':
    aclbibcleaner()
