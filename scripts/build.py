#!/usr/bin/env python3
"""Fetch pinned originals, patch Apout, and assemble the original runtime loader."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
DOWNLOADS = ROOT / 'downloads'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guest_limits():
    # Apout exposes this limit to 16-bit guests: 1048576 would wrap to zero.
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(soft, 64), hard))


def fetch():
    sources = json.loads((ROOT / 'sources.json').read_text())
    DOWNLOADS.mkdir(exist_ok=True)
    for name, source in sources.items():
        path = DOWNLOADS / name
        if not path.exists():
            partial = path.with_suffix(path.suffix + '.part')
            subprocess.run(['curl', '-fL', '--retry', '2', '--connect-timeout', '30',
                            '--max-time', '300', source['url'], '-o', str(partial)],
                           check=True)
            if sha256(partial) != source['sha256']:
                raise RuntimeError('SHA256 mismatch: ' + str(partial))
            partial.replace(path)
        if sha256(path) != source['sha256']:
            raise RuntimeError('SHA256 mismatch: ' + str(path))
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-only', action='store_true')
    args = parser.parse_args()
    sources = fetch()
    if args.fetch_only:
        return
    BUILD.mkdir(exist_ok=True)
    ready = BUILD / 'ready.json'
    ready.unlink(missing_ok=True)
    original = BUILD / 'original'
    original.mkdir(exist_ok=True)
    # Copy named regular files only; never unpack archive paths or symlinks.
    with tarfile.open(DOWNLOADS / 'algol68.tar.gz') as archive:
        for name in ('alg68', 'a68rte', 'a68.s', 'ago.s', 'articles', 'lsquare.a68'):
            member = archive.getmember(name)
            if not member.isfile():
                raise RuntimeError('Not a regular file: ' + name)
            (original / name).write_bytes(archive.extractfile(member).read())
    apout = BUILD / 'Apout'
    if apout.exists():
        shutil.rmtree(apout)
    apout.mkdir()
    with tarfile.open(DOWNLOADS / 'apout.tar.gz') as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if len(parts) == 2 and member.isfile():
                name = parts[1]
                if Path(name).suffix in ('.c', '.h') or name in ('LICENSE', 'COPYRIGHT', 'README'):
                    (apout / name).write_bytes(archive.extractfile(member).read())
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i',
                    str(ROOT / 'patches/apout-algol68.patch')], cwd=apout, check=True)
    flags = ['-O2', '-w', '-DDEBUG', '-DEMU211', '-DNATIVES']
    cc = shlex.split(os.environ.get('CC', 'cc'))
    subprocess.run([*cc, *flags, '-o', str(BUILD / 'apout'),
                    *map(str, sorted(apout.glob('*.c'))), '-lm'], check=True)
    bsd = BUILD / 'bsd'
    bsd.mkdir(exist_ok=True)
    # TUHS's root.afio.gz is an old portable ASCII cpio (070707) archive.
    # Extract only bin/as and README, with no ownership/permission restoration.
    subprocess.run(['cpio', '-id', '--quiet', '--no-preserve-owner',
                    '--no-absolute-filenames', '-u', 'bin/as', 'README'],
                   input=gzip.decompress((DOWNLOADS / 'bsd-root.afio.gz').read_bytes()),
                   cwd=bsd, check=True)
    assembler = bsd / 'bin/as'
    if not assembler.is_file():
        raise RuntimeError('BSD installation archive did not contain bin/as')
    env = dict(os.environ, APOUT_ROOT='/', APOUT_UNIX_VERSION='2.11BSD')
    subprocess.run([str(BUILD / 'apout'), str(assembler), '-o', str(BUILD / 'ago'),
                    str(original / 'ago.s')], cwd=BUILD, env=env,
                   preexec_fn=guest_limits, check=True, timeout=30)
    if (BUILD / 'ago').read_bytes()[:2] != b'\x07\x01':
        raise RuntimeError('Expected writable combined-I&D 0407 loader')
    etc = BUILD / 'root/etc'
    etc.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original / 'a68rte', etc / 'a68rte')
    provenance = dict(sources=sources, cc_version=subprocess.check_output(
        [*cc, '--version'], text=True), cflags=flags,
        patch_sha256=sha256(ROOT / 'patches/apout-algol68.patch'),
        original_sha256={p.name: sha256(p) for p in sorted(original.iterdir())},
        assembler_sha256=sha256(assembler))
    ready.write_text(json.dumps(provenance, indent=2) + '\n')
    print('Built original Algol 68S compiler/runtime demonstration.')


if __name__ == '__main__':
    main()
