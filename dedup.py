from blake3 import blake3
import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand
import click_log
#import click_completion

from humanfriendly import parse_size

from tqdm import tqdm

import hashlib
from pathlib import Path

from collections import defaultdict

import logging

logger = logging.getLogger(__name__)

click_log.basic_config(logger)

from IPython import embed


#click_completion.init()

@click.group(cls=HelpColorsGroup,
             help_headers_color='yellow',
             help_options_color='green')
def cli():
    pass

# https://izziswift.com/get-md5-hash-of-big-files-in-python/
# def md5_for_file(path, block_size=256*128, hex_result=False):
#     '''
#     Block size directly depends on the block size of your filesystem
#     to avoid performances issues
#     Here I have blocks of 4096 octets (Default NTFS)
#     '''
#     md5 = hashlib.md5()
#     with open(path,'rb') as f:
#         for chunk in iter(lambda: f.read(block_size), b''):
#              md5.update(chunk)
#     if hex_result:
#         return md5.hexdigest()
#     return md5.digest()


# def blake3_for_file(path, block_size=256*128, hex_result=False):
#     b3 = blake3()
#     with open(path,'rb') as f:
#         for chunk in iter(lambda: f.read(block_size), b''):
#              b3.update(chunk)

#     return b3.hexdigest() if hex_result else b3.digest()


def hash_file(filepath, block_size=65536, hex_result=True, hash_constructor=hashlib.md5):
    hasher = hash_constructor()
    with open(filepath,'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
             hasher.update(chunk)

    return hasher.hexdigest() if hex_result else hasher.digest()


# @cli.command()
# @click.argument('filepath', type=click.Path(exists=True))
# def list_dups(filepath):

#     dups = defaultdict(list)

#     p = Path(filepath).expanduser()
#     ## FIXME: recurse
#     p1 = p.glob('**/*')
#     # FIXME: switch to tqdm?
#     with click.progressbar(p1) as files:
#         for f in files:
#             if f.is_file() and not f.is_symlink():
#                 #click.echo(f'file: {f}')
#                 md5res = md5_for_file(f, block_size=65536, hex_result=True)
#                 #click.echo(f'md5: {md5res}')
#                 dups[md5res].append(f)
#     d2 = {k: v for (k, v) in dups.items() if len(v) > 1}
#     # FIXME: convert to pandas?
#     embed()


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('-s', '--min-size', default='1', show_default=True)
@click.option('-h', '--hash-type', type=click.Choice(['md5', 'blake3']), default='md5', show_default=True)
#@click.option() # block-size (adaptive?)
@click_log.simple_verbosity_option(logger)
def list_dups_b3(filepath, min_size, hash_type):

    logger.debug(f'hash-type: {hash_type}')

    hash_constructor = hashlib.md5
    if hash_type == 'blake3':
        hash_constructor = blake3


    min_sz = parse_size(min_size)

    dups = defaultdict(list)
    hardlinked = defaultdict(list)

    logger.debug(f'min-size: {min_sz}')

    p = Path(filepath).expanduser()

    p1 = p.glob('**/*')

    for f in tqdm(p1):
        if f.is_file() and not f.is_symlink():
            s = f.stat()
            if (s.st_size > min_sz):
                logger.debug(f'processing: {f}')
                # FIXME check if s.st_size > minsize
                if s.st_nlink > 1:
                    logger.debug(f'hardlinks [{s.st_nlink}]: file: {f}')
                    # Same Inodes:
                    hardlinked[(s.st_ino, s.st_dev)].append(f)
                # FIXME: adaptive block_size??
                hash_res = hash_file(f, block_size=65536, hex_result=True, hash_constructor=hash_constructor)
                #click.echo(f'hash[{hash_type}]: {hash_res}')
                dups[hash_res].append(f)

    d2 = {k: v for (k, v) in dups.items() if len(v) > 1}
    # FIXME: convert to pandas?
    embed()



if __name__ == '__main__':
    cli()
