# Magboltz 11.21, with its defects fixed

[Magboltz](https://magboltz.web.cern.ch/magboltz/) by S. Biagi computes
electron transport in gas mixtures by Monte Carlo. This repository holds
its Fortran source as the reference for
[NimBoltz](https://github.com/SciNim/NimBoltz), a port to Nim that
reproduces it bit for bit, and the defects found while porting it.

- Branch `master`: the sources of Magboltz 11.19 and 11.21 as published,
  a `Makefile` for a reference build with fixed flags (no FMA, no
  fast-math) and a dumper of its random numbers.
- Branch `fixes`: 61 defects of 11.21 (MB-01 … MB-61) fixed by their
  evident intent, one commit each, every change marked
  `C NIMBOLTZ FIX MB-nn:` in the source.

The report is [`bugs/README.md`](bugs/README.md): for every defect what
and where it is, its effect on results and a reproduction
(`bugs/reproduce.sh`, decks in `bugs/decks/`). Places where the intent is
not clear are not changed; they are questions in
[`bugs/QUESTIONS.md`](bugs/QUESTIONS.md).

```sh
make                                   # build/magboltz-11.19, build/magboltz-11.21
build/magboltz-11.21 < inputs/ar_ibut_E500.in
git show master:magboltz-11.21.f > /tmp/up.f; bugs/reproduce.sh /tmp/up.f   # the defects, upstream
bugs/reproduce.sh magboltz-11.21.f                                            # the same cases, fixed
```
