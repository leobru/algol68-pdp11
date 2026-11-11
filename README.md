# PDP-11 Algol 68S demonstration

Run the historical PDP-11 Algol 68S compiler and runtime on a modern Linux
host using Apout. This repository downloads the original binaries, builds a
patched emulator, assembles the original runtime loader and checks real
compilations and executions.

Requirements: a little-endian Linux host, Python 3.8 or newer, a C compiler,
Make, curl, patch and GNU cpio. On Debian/Ubuntu:

```sh
sudo apt-get install build-essential python3 curl patch cpio
make check
make demo
```

The hello demo prints `Hello from PDP-11 Algol 68S!` and `+42`, surrounded by
the historical runtime's start/end messages. The compiler also prints its
own banner and compilation statistics.

Compile and run your own source:

```sh
./alg -su examples/factorial.a68
./ago
./alg -su examples/manorboy.a68
./ago
printf 'BEGIN print(6 * 7) END\n' | ./alg -su
./ago
./alg -lsu examples/hello.a68
```

`-su` selects upper-case keywords; `-l` requests a source listing. Compilation
creates `a68.out` in your current directory. `./ago` runs that file.
Failed compilation removes stale output.
The runtime's exit register is unspecified; the launcher recognizes its normal
completion message and reports failure when that message is absent.

`make check` verifies strings and integer arithmetic, recursive factorial,
the man-or-boy test with K=7 (result `-1`),
basic real arithmetic, source listings, rejected input, stale-output removal,
an exact quine, and completion of all twelve cases in the archived least-squares
example. Logs go into `build/test-results/`. The least-squares check verifies
execution and output structure; Apout floating-point accuracy is limited and
the numerical results are not certified. The quine is adapted to this compiler's
68S dialect, including its enclosing clause, STRING operators and slice indices.

The man-or-boy test with K=8 compiles, but does not fit in the runtime's
available memory: execution reports `ERROR 0046`,
`INSUFFICIENT MEMORY SPACE FOR EXECUTION OF PROGRAM`.

## Downloads and layout

All downloads have pinned SHA256 checksums in [sources.json](sources.json).

| Input | Public source | Use |
| --- | --- | --- |
| `algol68.tar.gz` | [TUHS Algol 68 archive](https://www.tuhs.org/Archive/Applications/Algol_68/) | Original `alg68`, `a68rte`, loader sources, articles and `lsquare.a68` |
| Apout revision `e88a446ace064f5a41e1a47d9ae8278b83b27a20` | [DoctorWkt/Apout](https://github.com/DoctorWkt/Apout/tree/e88a446ace064f5a41e1a47d9ae8278b83b27a20) | Tested emulator source |
| `root.afio.gz` | [TUHS 2.11BSD installation files](https://www.tuhs.org/Archive/Distributions/UCB/2BSD/2.11BSD/) | Only `bin/as` and its distribution README are extracted |

TUHS also carries [Apout releases](https://www.tuhs.org/Archive/Tools/Emulators/Apout/).
This build uses the pinned GitHub revision so the accompanying patch has an
exact source base. No BSD boot, disk image installation or SIMH is required:
Apout executes the assembler and user programs directly. The installed BSD
system is not needed. The resulting runtime loader uses writable combined
instruction/data space, executable magic `0407`.

`make fetch` downloads and verifies inputs without building. For an offline
build, put the three files named in `sources.json` in `downloads/` first;
their checksums are still enforced. `CC` selects the host C compiler.
Apout is compiled with `-w` to suppress warnings from its historical C sources.

Downloads stay in ignored `downloads/`; unpacked originals, emulator sources,
assembler, loader, private runtime root and test output stay in ignored
`build/`. `build/ready.json` records download identities, image hashes, the
patch hash, compiler version and build flags. `make clean` removes build
products and retains the download cache. Neither downloads nor generated
binaries belong in Git.

## Emulator patch and historical materials

[patches/apout-algol68.patch](patches/apout-algol68.patch) implements synchronous
guest EMT delivery, one-shot V7 signal reset and RTI restoration of PC and
condition flags. It also resets EMT state across exec and returns syscall
errno in r0. These emulator fixes allow the original runtime's I/O support to
operate. The compiler runs in V6 mode; the original `ago.s` loader is assembled
using the BSD assembler and runs in V7 mode. `/etc/a68rte` is supplied through
a private `APOUT_ROOT`; no host system files are installed.

The original compiler, runtime and loader source are unchanged. The compiler
image is executed directly through Apout; `a68.s` remains available among the
downloaded originals for historical context.

Apout's upstream license and copyright are retained in `build/Apout/`. Historical
Algol and BSD materials retain their original terms: see the
[Algol archive README](https://www.tuhs.org/Archive/Applications/Algol_68/README.algol68),
downloaded articles and `build/bsd/README`. Availability in an archive does not
establish that the Algol implementation is public domain. The original scripts
and examples added in this repository are provided under the MIT license;
that license does not relicense downloaded historical material or the Apout patch.
