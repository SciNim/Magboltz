# Magboltz → Nim port: notes to future self

Written 2026-10-30 after a short feasibility survey (no code written yet).
The user (Basti / Vindaar, author of `unchained`, `measuremancer` and a Nim→GPU compiler)
wants a port that is *bitwise equivalent* to the Fortran when fed the identical RNG
stream, but written as idiomatic multi-file Nim with physical units. A GPU backend
is a later, separate goal — do not let it shape the first port.

## Goal, in priority order
1. Bit-for-bit identical results vs. a reference Fortran build (same input → same output).
2. Readable, multi-file Nim; deduplicate the copy-pasted Fortran routines *after*
   a bitwise regression test exists.
3. Physical units via `unchained` (`~/CastData/ExternCode/units`), uncertainties
   on outputs via `measuremancer` (`~/CastData/ExternCode/measuremancer`).

## Facts about the source (verified on magboltz-11.19.f)
- Files: `magboltz-11.{1..19}.f` (no 11.8). Latest = 11.19, 99,558 lines.
  The prebuilt `./magboltz` binary is **11.17** (has debug info, not stripped).
  → Decide which version is the reference; probably 11.19, rebuilt ourselves.
- ~157 subroutines/functions. **80 `GASn` subroutines = ~81.5k lines (82%)**;
  everything else ≈ 18k lines.
- GAS routines: big `DATA` tables (energies `XEN`, cross sections `YEL`, `YSEC`, …)
  followed by interpolation/scaling logic that is largely copy-pasted between gases.
  Largest: GAS15 (3245 lines), GAS6, GAS31, GAS22, GAS48 (~2.8k each).
- Core routines come in many near-duplicate variants:
  `MONTE`, `MONTEA`, `MONTEB`, `MONTEC`, `ELIMIT`, `ELIMITB`, `ELIMITC`,
  `MONTEFT`, `MONTEFD`, `MONTEFTG`, `MONTEFTH`, `MONTEFTA`, `MIXER`, `SETUP`,
  and a full thermal-motion copy of each with a `T` suffix (`MONTET`, `MIXERT`, …).
  (A/B/C ≈ different E/B field configurations; FT/FD ≈ SST/time-of-flight variants —
  confirm by reading.) Estimated truly distinct physics: 3–5k lines.
- 154× `IMPLICIT REAL*8 (A-H,O-Z)`; no `REAL*4` declarations; **no `EQUIVALENCE`**;
  921 `COMMON` lines (global state → becomes Nim object(s) passed around).
- ~2600 GOTO/COMMON-ish lines; spaghetti control flow in the MC loops.
- Input: free-format, `READIN(LAST)` at line ~2466; main loop calls it at line 475.

## RNG (verified, line ~17849 in 11.19)
- `DOUBLE PRECISION FUNCTION drand48(DUMMY)` is a shim over CERNLIB `RM48`
  (RANMAR, `rm48.F` v1.2 1996) included in the same file. Port RM48 exactly
  (+ its seeding routine `RM48IN`, check how/where it's seeded).
- Buffer quirk to replicate: `NVEC=1000`, refill when `IVEC.EQ.0 .OR. IVEC.GE.NVEC`,
  so after the first fill element `RVEC(1000)` is **never returned**
  (indices 1..999 used, then refill). Easiest: port the shim literally.

## Bitwise-equivalence pitfalls (the real work)
1. **Single-precision literals.** Under `IMPLICIT REAL*8`, a literal like `1.2`
   (in `DATA` or in expressions like `X*1.1`) is REAL(4), widened to double:
   1.2 → 1.2000000476837158. Any literal without `D` exponent must become
   `float64(1.2'f32)` in Nim. Literals with `D0` are real doubles. Exactly
   representable ones (0.5, 2.0) don't matter but handle uniformly anyway.
   **Do this with a translator script, never by hand.** Also watch integer
   division and mixed INTEGER/REAL expressions (Fortran promotion rules).
   Double-check gfortran's exact semantics for DATA conversion with a tiny test program.
2. **Compiler flags.** Build the reference Fortran with `-O0 -ffp-contract=off`
   (or another fixed set, but no FMA / fast-math). Build Nim with
   `--passC:"-ffp-contract=off"` and no `-ffast-math`. Both use the same libm
   for exp/log/sqrt/sin, so those match. Beware Fortran intrinsics that gfortran
   inlines differently (e.g. `**` with integer vs real exponent → `pow` vs repeated multiply;
   `X**2` is `X*X`, `X**0.5` is `pow`). Replicate exactly.
3. **No algebraic "cleanups"** during the faithful port: keep evaluation order,
   parenthesization, and temporaries identical. Refactor only under the regression test.
4. **Divergence is invisible until it's huge.** Need an instrumented Fortran build that
   dumps state every N collisions (RNG call count, energy, position, direction,
   collision type/level index) and a differ that reports the first mismatch.
5. **Units must not insert conversions.** `unchained` is compile-time only, BUT it
   auto-converts when mixing prefixes/units (e.g. `kg + lbs`, comparisons across prefixes),
   and `to` multiplies by factors. Inside the hot path, type everything in Magboltz's own
   working units (eV, cm, ns, ps, Td, cm², …) so no factor is ever applied; convert only
   at I/O. `eV` exists in unchained; Townsend (Td) probably needs `defUnit`/a custom
   unit — not checked. If a quantity's Fortran value isn't in a clean unit, keep it a
   plain float rather than introduce a conversion.

## Plan
1. **Harness first**
   - git init, build reference Fortran(s) with fixed flags, keep inputs + golden outputs.
   - Instrumented Fortran (state dumps; also a routine to dump each gas's filled
     cross-section arrays for given energy grid/settings).
   - Port RANMAR + shim, verify the first ~10⁶ numbers against Fortran.
2. **Gas tables (biggest, least risky)**
   - Script extracts `DATA` blocks → Nim consts / data files with correct f32 widening.
   - Hand-port per-gas logic (look for shared patterns → generic helpers, but keep
     arithmetic order). Validate each gas bitwise against dumped arrays (deterministic, no MC).
   - Start with common gases: Ar, CO₂, CH₄, iC₄H₁₀, Ne, Xe, He, N₂ (find their GASn numbers).
3. **Core MC**: faithful port of SETUP/MIXER/ELIMIT/MONTE (+variants), match outputs,
   then deduplicate variants (and T copies) under the regression test.
4. Units + measuremancer at the edges; nice CLI/input format last.

Effort guess given to the user: core + handful of gases bitwise in a few focused days;
all 80 gases ~1–2 weeks, mostly verification grind. Main risk: divergence hunting in step 3.

## GPU note (later)
Magboltz tracks one electron serially through ~10⁸ collisions. A GPU version means many
independent chains with per-thread RNG streams → no longer bitwise vs. Fortran by design.
The bitwise CPU port is the reference for validating it statistically.

## Previous attempt: ~/CastData/ExternCode/NimBoltz (Opus 4.5, Jan/Feb 2026)
Reviewed 2026-10-30. Summary: **useful as a lesson, not as a base for the bitwise port.**
- Repo has git history (12 commits), but most of the Jan 2026 work is **uncommitted/untracked**
  (`src/`, `examples/`, debug `.f` files, `DEBUGGING_STATUS.md`). Don't lose it; commit or
  archive before restructuring.
- Older parts (2023, by the user): `nimboltz.nim` = wrapper that *runs* the Fortran binary,
  writes input files, and parses its output with npeg (`parseMagboltz`, `runMagboltz`,
  `genOutfile`). Still useful for generating reference inputs/outputs and comparing results.
- `tools/extract_gas_data.nim` (876 lines) → `gas_data/gas01..80.json`. It only extracts
  `DATA` arrays + some metadata. **Problems for a bitwise port:**
  (a) it parses every literal with `parseFloat` after turning `D`→`e`, so the REAL(4)-vs-REAL(8)
  distinction is **lost** (JSON `1.2` ≠ Fortran's widened-f32 1.2);
  (b) the per-gas *code* (scaling, interpolation, Born–Bethe extrapolation above the table,
  values set in code rather than in DATA, version-dependent branches) is not captured at all.
  The parser itself (continuation lines, D notation) can be reused if it also records
  each literal's kind (or emits the original text).
- `src/nimboltz/` (~2.3k lines): a *loose re-derivation* of the physics ("clean
  architecture" first: mixer/collision/scattering/monte modules). It never worked: Ar at
  500 V/cm gave drift velocity 0.23 µm/ns vs Magboltz 3.38 (15× low), mean energy
  3.82 eV vs 3.26 (and still rising). The debug log shows it guessing (VAN factor tried as
  1e15 → 1e-1 → 1e11, sqrt(E) in TCF added/removed/re-added) and replacing Magboltz's
  energy-loss formula `E1 = EOK*(1 - EI/(S1*EOK) - 2*D/S2)` with a textbook one.
  `random.nim` implements a POSIX drand48 LCG — **wrong**: Magboltz's `drand48` is the
  RANMAR/RM48 shim.
  **Lesson: transliterate first, refactor later. Don't re-derive physics from memory, and
  don't design the architecture before having a bitwise-matching translation.**
- `magboltz-debug{,2,3,4}.f`, `magboltz-f1debug.f`: 11.19 with single `WRITE` lines
  (VAN, CONST3/4, BP/F1/F2, TCF). Ad-hoc; replace with a systematic state-dump harness.
- Reference values recorded there (Ar 100%, 500 V/cm, 760 Torr, 20 °C, Magboltz 11.19):
  WZ = 3.38 µm/ns, mean energy 3.26 eV, TCFMAX ≈ 1.1e13 Hz, VAN = 1.48e15.
- `unchained_bug_repro.nim`, `bug_repro_{main,units}.nim`: a cross-module `defUnit(V•cm⁻¹)`
  type mismatch. **Both compile and run fine with unchained 0.4.8 (426d72a, Nov 2025)** —
  fixed, no workaround needed.
- `docs/PROJECT_VISION.md`: phases (data → core → CPU parallel → GPU). Fine as a roadmap,
  but phase 2 should be "faithful port + bitwise harness".
- Suggested approach: keep the NimBoltz repo (it's the user's project name and has the
  wrapper/parser), but start the core again on a new branch/directory using the plan above;
  move the old `src/nimboltz` aside instead of building on it. Ask the user if unsure.

## Environment hints
- Host had GNU Fortran 14.2.1 and Nim 2.3.1. The work directory was **not** a git repo.
- `.claude/settings.local.json` here allows `./extract_gas_data` — that's from the previous
  attempt in `~/CastData/ExternCode/NimBoltz` (see above).
