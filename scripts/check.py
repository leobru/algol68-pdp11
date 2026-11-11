#!/usr/bin/env python3
"""Exercise the downloaded compiler, original loader and runtime end to end."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
START = ' \nALGOL68 - UOM V1:  EXECUTION STARTED\n \n'
END = ' \nALGOL68: END OF EXECUTION.\n \n'


def main():
    images = [BUILD / 'original' / n for n in ('alg68', 'a68rte')]
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
    checked = []
    logs = BUILD / 'test-results'
    logs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='check-', dir=BUILD) as tmp:
        work = Path(tmp)

        def run(tool, *args, source=None):
            return subprocess.run([str(ROOT / tool), *map(str, args)], input=source,
                                  text=True, cwd=work, capture_output=True, timeout=30)

        def compile_file(source, options='-su'):
            result = run('alg', options, source)
            assert result.returncode == 0, result.stdout + result.stderr
            assert (work / 'a68.out').is_file()
            return result.stdout

        def execute(label):
            result = run('ago')
            (logs / (label + '.txt')).write_text(result.stdout + result.stderr)
            assert result.returncode == 0, result.stdout + result.stderr
            assert not result.stderr, result.stderr
            assert result.stdout.startswith(START), repr(result.stdout)
            assert result.stdout.endswith(END), repr(result.stdout)
            return result.stdout[len(START):-len(END)]

        compile_file(ROOT / 'examples/hello.a68')
        output = execute('hello')
        assert 'Hello from PDP-11 Algol 68S!' in output and '+42' in output, output
        checked.append('file input, strings, integer arithmetic, newline, runtime completion')
        compile_file(ROOT / 'examples/factorial.a68')
        assert '+5040' in execute('factorial')
        checked.append('recursive procedures and conditionals')
        compile_file(ROOT / 'examples/manorboy.a68')
        assert execute('manorboy').strip() == '-1'
        checked.append('man-or-boy test with K=7 returned -1')
        quine = ROOT / 'examples/quine.a68'
        compile_file(quine)
        assert execute('quine') == quine.read_text()
        checked.append('quine output exactly matched source including newline')
        result = run('alg', '-su', source='BEGIN print(2.0 + 3.0) END\n')
        assert result.returncode == 0, result.stdout + result.stderr
        assert re.search(r'\+5\.0+E\s*\+0', execute('real'))
        checked.append('standard input and basic real arithmetic')
        listing = compile_file(ROOT / 'examples/hello.a68', '-lsu')
        assert 'print' in listing, listing
        (logs / 'listing.txt').write_text(listing)
        checked.append('source listing')
        rejected = run('alg', '-su', ROOT / 'examples/invalid.a68')
        assert rejected.returncode != 0 and 'ERROR' in rejected.stdout, rejected
        assert not (work / 'a68.out').exists()
        assert run('ago').returncode != 0
        (logs / 'diagnostic.txt').write_text(rejected.stdout + rejected.stderr)
        checked.append('syntax diagnostic, failed compile removed stale object, missing object rejected')
        compile_file(BUILD / 'original/lsquare.a68')
        output = execute('lsquare')
        assert output.count(' solution:') == 12, output
        assert output.count(' residue:') == 12, output
        checked.append('all 12 archived least-squares cases completed (numerical accuracy not certified)')
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
    checked.append('original compiler/runtime image hashes unchanged')
    (logs / 'summary.json').write_text(json.dumps(checked, indent=2) + '\n')
    for item in checked:
        print('PASS:', item)


if __name__ == '__main__':
    main()
