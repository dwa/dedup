import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand
import click_log
#import click_completion

import pandas as pd

from humanfriendly import parse_size, format_size

from tqdm import tqdm

from pathlib import Path

from collections import defaultdict

import logging

logger = logging.getLogger(__name__)

click_log.basic_config(logger)

from IPython import embed

available_hashes = {}

try:
    from hashlib import md5
    default_hash = 'md5'
    available_hashes[default_hash] = md5
except:
    pass
try:
    from blake3 import blake3
    default_hash = 'blake3'
    available_hashes[default_hash] = blake3

except:
    pass
try:
    from xxhash import xxh3_128
    default_hash = 'xxh3'
    available_hashes[default_hash] = xxh3_128
except:
    pass


#click_completion.init()

@click.group(cls=HelpColorsGroup,
             help_headers_color='yellow',
             help_options_color='green')
def cli():
    pass


# FIXME: rewrite this, assume filepath is a Path object:
# - filepath.open()
# - check size: do a simple hashing if size < block_size
def hash_file(filepath, block_size=65536, hex_result=True, hash_constructor=md5):
    hasher = hash_constructor()
    with open(filepath,'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
             hasher.update(chunk)

    return hasher.hexdigest() if hex_result else hasher.digest()


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('-h', '--hash-type', type=click.Choice(available_hashes.keys()), default=default_hash, show_default=True)
@click.option('-b', '--block-size', default='64K', show_default=True) # block-size (adaptive?)
def hash_me(filepath, hash_type, block_size):
    '''Don't use this, too much overhead!'''
    hash_constructor = available_hashes[hash_type]

    blk_sz = parse_size(block_size, binary=True)

    h = hash_file(filepath,
                  block_size=blk_sz,
                  hex_result=True,
                  hash_constructor=hash_constructor)

    print(h)


# FIXME: do what it says on the tin
@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('-s', '--min-size', default='1', show_default=True)
@click.option('-h', '--hash-type', type=click.Choice(available_hashes.keys()), default=default_hash, show_default=True)
@click.option('-b', '--block-size', default='64K', show_default=True) # block-size (adaptive?)
@click_log.simple_verbosity_option(logger)
def list_dups(filepath, min_size, hash_type, block_size):

    logger.debug(f'hash-type: {hash_type}')

    hash_constructor = available_hashes[hash_type]

    min_sz = parse_size(min_size)

    blk_sz = parse_size(block_size, binary=True)

    dups = defaultdict(list)
    hardlinked = defaultdict(list)

    logger.debug(f'min-size: {min_sz}')
    logger.debug(f'block-size: {blk_sz}')

    p = Path(filepath).expanduser()

    p1 = p.glob('**/*')

    for f in tqdm(p1):
        if f.is_file() and not f.is_symlink():
            s = f.stat()
            if (s.st_size > min_sz):
                #logger.debug(f'processing: {f}')
                if s.st_nlink > 1:
                    logger.debug(f'hardlinks [{s.st_nlink}]: file: {f}')
                    # Same Inodes:
                    hardlinked[(s.st_ino, s.st_dev)].append(f)
                # FIXME: adaptive block_size??
                hash_res = hash_file(f, block_size=blk_sz, hex_result=True, hash_constructor=hash_constructor)
                #click.echo(f'hash[{hash_type}]: {hash_res}')
                dups[hash_res].append(f)

    records = [[(k,
                 p.resolve().as_posix(),
                 p.stat().st_size,
                 format_size(p.stat().st_size))
                for p in p] for (k,p) in dups.items() if len(p) > 1]

    if len(records) > 0:
        cols = ['hash', 'file_path', 'size', 'human_size']
        df = (pd.concat(pd.DataFrame.from_records(r, columns=cols) for r in records)
              .sort_values(by='size', ascending=False))
    embed()


if __name__ == '__main__':
    cli()
