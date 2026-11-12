# Defects found in Magboltz 11.21

Source: `magboltz-11.21.f` (S. Biagi; the program prints `VERSION 11.20`),
branch `master` of this repository. Line numbers below refer to that file.
Branch `fixes` has one commit per defect (`MB-01` … `MB-61`); every change,
except the 281 loop starts of MB-10, carries a `C NIMBOLTZ FIX MB-nn:` comment.
Cases where the intended behaviour is not clear from the code are not
changed; they are listed as questions in `QUESTIONS.md`.

The defects were found while porting Magboltz to Nim with the requirement
that the port reproduce the Fortran output bit for bit. Nim checks array
bounds, so several gases crashed in the port where the Fortran silently
reads neighbouring memory. A systematic search (below) then found more of
the same kind, and some that are plain typos.

All fixes implement what the surrounding code evidently intends (the same
construction elsewhere in the routine or in a sibling gas); they do not
change any in-bounds, defined evaluation unless stated. Where the intent is
a guess, this is said explicitly ("Interpretation").

## Summary

| ID | Routine(s) | Gas | Kind | Reached | Effect |
|---|---|---|---|---|---|
| MB-01 | GAS22, GAS48 | D2, ortho-D2 | inverted test → index ≤ 0 | always (EN < 8 eV) | 2 superelastic levels: garbage anisotropy < 8 eV, none above |
| MB-02 | GAS24 | methylal | wrong grid searched | always | QIN(5) wrong at all energies, negative above ~100 eV |
| MB-03 | GAS29 | C2F6 | typo, undefined variable | always | PEQIN(13/14) = 1 instead of 0.149 |
| MB-04 | GAS43 | C2H2F4 | `DO 420 L=9` is an assignment | always | 9 vibrational levels isotropic above 20 eV |
| MB-05 | MONTEBT | any, B⊥E, thermal | typo, undefined index | always | RNMX table index from stack contents |
| MB-06 | GAS44 | TMA | undefined variable | EN ≤ 0.001 eV | PEQEL(2) undefined |
| MB-07 | GAS14, GAS34 | H2O, methanol | missing guard → index ≤ 0 | EN ≤ \|EIN\| | superelastic anisotropy from unrelated memory |
| MB-08 | GAS10 | propane | table length 46 vs 45 | EN > EION(1) | XION(46) read |
| MB-09 | GAS46 | n-propanol | stray loop outside energy loop | always | QION(K,4001) read (unused) |
| MB-10 | 281 search loops | CCl4, ethene, SiH4 (reachable) | loop from 1 reads T(0) | EN at/below table start | T(0) from unrelated memory |
| MB-11 | GAS43 | C2H2F4 | undefined variable | EN < 1E-4 eV | PEQEL(2) undefined |
| MB-12 | GAS7 | Xe | wrong jump target | EN ≤ EION(2) | QION(3) = undefined Q456 |
| MB-13 | GAS21/22/47/48 | H2, D2, p-H2, o-D2 | undefined variable QMOM | NANISO=1 | PEQEL(2) undefined |
| MB-14 | GAS22, GAS48 | D2, ortho-D2 | `NANISO.EQ.O` (letter O) | always | isotropic branch from stack contents |
| MB-15 | GAS49 | C4F7N | table without DATA | always | 3-body attachment from undefined table |
| MB-16 | GAS11/15/18/23/25/34 | isobutane, O2, N2O, CO, DME, methanol | undefined sums | always | diagnostics only (Q(1), QTOT) |
| MB-17 | GAS30 | SF6 | typo `PEQIN(2,I)` for `PEQIN(22,I)` | always | V4 anisotropy overwritten with 0 |
| MB-18 | GAS23 | CO | typo `PEQEL(1,` for `PEQEL(2,` | always | level 146 anisotropy = 0 |
| MB-19 | GAS15 (+14/31/34/35/36/46) | O2 (+H2O, NH3, alcohols) | Penning init loop without body / wrong index | always | PENFRA undefined; matters with IPEN=1 |
| MB-20 | GASMIX (≈30 gases) | many | outputs never set, zero assumed | always | PENFRA, Auger data, EI of brems levels from stack |
| MB-21 | GAS49 | C4F7N | NIN copied from GAS45 | always / EFINAL > 1 keV | 3 empty levels; bremsstrahlung in the wrong levels |
| MB-22 | GAS30 | SF6 | `Q(2,I)` for `QIN(2,I)` | always | V4 anisotropy negative → always backward |
| MB-23 | MONTEB, MONTEBT | any, B⊥E | 0/0 | always | error of DIFXX printed as NaN |
| MB-24 | MONTEFTG, MONTEFTH | any, B⊥E / B at angle, high field | typos `DCYS`, `*` for `+` | ionisations | secondary-electron directions from stack contents |
| MB-25 | GAS9, GAS19 | ethane, ethene | undefined loop bound NBRM | EN > 1 keV | bremsstrahlung 20–60× too small (if NBRM=0) |
| MB-26 | GAS23 | CO | undefined loop bound N2XC5 | 6.8–20 eV | A3Π v=4 cross section from wrong interval (×3 at 7.6 eV) |
| MB-27 | GAS43, GAS60 | C2H2F4, SiH4 | undefined names in fall-through | never | none |
| MB-28 | MONTEFTG, MONTEFTGT | any, B⊥E, high field | Penning test `.EQ.` for `.NE.` | IPEN=1 | no Penning transfer at all |
| MB-29 | ELIMITBT | any, B⊥E, thermal | clamp stored in unused DCZ2 | rounding | none in practice |
| MB-30 | MIXER | gas 2 with shells | `EFL1` for `EFL2` | always | none (EFL is never read) |
| MB-31 | MIXER | gas 2 of any 0 K mixture | ENDIF misplaced, KIN=2 test unreachable | always | inelastic scattering of gas 2 isotropic; drift in Ar/H2O ×0.4 |
| MB-32 | MIXERT | gases 2–6 with shells, thermal | `KEL1(3)` for `KELn(3)` | always | shell ionisation takes gas 1's anisotropy kind |
| MB-33 | MIXERT | gas 3 with one attachment process, thermal | `IARRY=0.0` for `=L` | gas 3 attaches | ICOLL written out of bounds (crash with bounds check) |
| MB-34 | MIXER, MIXERT | gas 1 (0 K), all gases (thermal) | factor `1.D-16` for `1.D-6` | IPEN=1, high field | Penning delocalisation length 10⁻¹⁰ of its value |
| MB-35 | MIXER | gas 6 with several attachments | `NATT5`/`QATT5` for 6 | always | none (QATT sums are never read) |
| MB-36 | MIXERT | any, thermal | sums reset inside the gas loop | always | FRIEDLAND ionisation/attachment of the last gas only |
| MB-37 | MONTEBT | any, thermal, B⊥E | arrays of 1000000 for NCOLM=2000000 | long decorrelation length | stored positions overwritten: diffusion garbage (DIFXX 10²¹ cm²/s) |
| MB-38 | MONTE*T, MONTEF*T (9 thermal routines) | HFO-1234ze, C4F7N, CF3Br | lab-frame energy for a rest-frame loss | moderation collision, thermal | residual energy EOK−E+0.025 eV instead of 0.025 eV; 1E-20 eV in MONTEF*T |
| MB-39 | MONTEFT*, MONTEFD, MONTEF*T (10 routines) | all | wrong variable in the azimuth wrap | every ionisation in SST/PT/TOF runs | the secondary electron takes the azimuth of the scattered primary in half of the ionisations instead of the opposite one; no effect resolved |
| MB-40 | TOFG | all | division by zero | B ⊥ E SST/TOF run without ionisation | PT attachment rate and TOF (α−η) printed as NaN |
| MB-41 | ALPCALCT | all, thermal | block missing in one of 8 sibling drivers | thermal B = 0 SST/TOF run with α ≈ η | plane spacing not shortened: up to 30× too long; SF6 near its critical field does not finish (> 75 min instead of 130 s) |
| MB-42 | ALPCLCA/AT/B/BT/C/CT | all | wrong unit / wrong variable / ×100 for /100 | every SST/TOF run with B ≠ 0 | /CTWNER/ errors (read by Garfield++ as percent) absolute 1/cm, stale (ALPCLCB) or 10⁴× too large (ALPCLCBT); not printed by Magboltz |
| MB-43 | MONTEFDT | all, thermal | √ of a rounding-negative number | thermal B = 0 SST run, electron at a turning point | NaN direction; usually absorbed by a null collision, else the run never ends (Ar/HFO-1234ze, Ar/C4F7N at 1 kV/cm) |
| MB-44 | GAS7 | Xe | `QIN(2,I)` for `QIN(23,I)` | EN > 100 eV | the 1S4 resonance (f = 0.26) replaced by the 4D-sum tail (10⁻⁴ of it); level 23 empty |
| MB-45 | GAS61 | CCl4 | `QIN(7,1)` for `QIN(7,I)`; `EN-EIN(8)` for `EN+EIN(8)` | always | V3 superelastic 10⁻³⁵ cm² instead of ~10⁻¹⁷; Ar/CCl4 90/10, 100 V/cm: drift +5.8 %, attachment −7 % when fixed |
| MB-46 | GAS31 | NH3 | wrong population, sign and J in 3 of 28 rotational transitions | always | J 0→1 ×2.7, 2→1 ×1.18 too large, 1→2 ×0.6 too small; mean energy −1.3 % at 0.1–1 kV/cm when fixed |
| MB-47 | GAS49 | C4F7N | mass and table lengths copied from GAS45 | always | mass 114.04 instead of 195.04, resonance tails cut; transport within 0.3 % |
| MB-48 | GAS44 | TMA | correction inside the wrong branch | 285–803 eV | K-shells counted twice in the counting ionisation (≤ 0.7 %) |
| MB-49 | GAS29, GAS43 | C2F6, C2H2F4 | `GO TO` the loop's own end | EN > 285 eV | carbon K-shell extrapolated from the last table interval (constant instead of rising ×20) |
| MB-50 | GAS29, GAS52 | C2F6, C3F8 | `PEQIN(L,I)` for `PEQIN(2*L-1,I)` | always | 3 dipole vibrations isotropic, 3 superelastic levels overwritten; drift +8 … +24 %, attachment ×2 at 10 kV/cm when fixed |
| MB-51 | GAS9/21/22/23/47/48/60/61 | ethane, H2, D2, CO, p-H2, o-D2, SiH4, CCl4 | threshold test of another level | near threshold | 3 levels missing over 0.14–0.5 eV; 6 tests too low, no effect |
| MB-52 | GAS7/11/15/18/23/31/60 | Xe, isobutane, O2, N2O, CO, NH3, SiH4 | anisotropy missing, inverted or stored in another level | always | 10 levels or channels isotropic (or anisotropic) where the others are not |
| MB-53 | GAS15/16/18/22/25/48 | O2, N2, N2O, D2, DME, o-D2 | wrong table or energy in a formula | always / above table | O2 level 72 tail ×0.26; D2 level 105 up to ×2.9; DME level 57 resonance ×0.18; 2 without effect |
| MB-54 | GAS45, GAS49, GAS61 | HFO-1234ze, C4F7N, CCl4 | debug output left on | every run | 4000 lines (GAS45, 49) or one line (GAS61) printed per call |
| MB-55 | GAS4 | He-3 | stray digit `78.27D-5` | 650–750 eV | levels 17, 25 ×10.7 at 700 eV |
| MB-56 | GAS25 | DME | degeneracy `2J-1` for `2J+1` | always | rotational populations wrong (J=1 ×0.4); mean energy −7 % at 0.1–1 kV/cm when fixed (with MB-53) |
| MB-57 | SETUPT | any, thermal | missing `LAST=1` after the input error | invalid gas input with ITHRM=1 | run continues with NMAX, TMAX etc. unset; meaningless results (drift 0, error NaN) instead of a stop |
| MB-58 | MONTE*, MONTEF* (18 routines) | H2S, TMA | moderation test by a tolerance of 1E-4 eV | every collision with the 0.025 eV level | the electron keeps 0.025 eV instead of losing 0.025 eV: drift −25 % (Ar/H2S), +50 % (Ar/TMA) |
| MB-59 | GAS14 | H2O | extra `/EN` in the superelastic tail | EN > 19.8 eV | V2-bend superelastic falls as 1/E² above 20 eV (1/20 of the table at its end); weighted by the 4·10⁻⁴ (010) population, no visible effect |
| MB-60 | GAS22, GAS48 | D2, ortho-D2 | no upper end test | EN > 20 eV | attachment extrapolated linearly, 4·10⁻¹⁹ cm² at 4 keV: attachment coefficient ×4 at 100 kV/cm |
| MB-61 | GAS31 | NH3 | one threshold test also skips two later channels | 23–28 eV | no H⁺ and H2⁺ ionisation below the N⁺ threshold of 28 eV; transport unchanged within errors |

Affected gases (cross sections or angular distributions): Xe (7), propane
(10), isobutane (11, diagnostic only), H2O (14), O2 (15), N2O (18,
diagnostic), ethene (19), H2 (21), D2 (22), CO (23), methylal (24), DME (25,
diagnostic), C2F6 (29), SF6 (30), methanol (34), C2H2F4 (43), TMA (44),
n-propanol (46), para-H2 (47), ortho-D2 (48), C4F7N (49), SiH4 (60), CCl4
(61), ethane (9), plus the ≈30 gases of MB-20, every B⊥E calculation (MB-05,
MB-23, MB-28) and every high-field calculation with a magnetic field not
parallel to E (MB-24), every 0 K mixture of two or more
gases (MB-31) every thermal calculation at high field (MB-34, MB-36) and every thermal
B⊥E calculation with the long decorrelation length (MB-37), and
thermal calculations with HFO-1234ze, C4F7N or CF3Br (MB-38), and
the printed attachment rate of B⊥E SST/TOF runs without ionisation (MB-40),
every calculation with H2S or TMA (MB-58), high-field calculations
with D2, ortho-D2 or NH3 (MB-60, MB-61),
thermal B = 0 SST/TOF runs near the critical field (MB-41, MB-43), and the
Townsend errors left in /CTWNER/ by every SST/TOF run with B ≠ 0 (MB-42).
The gas-routine series MB-44 … MB-56 adds He-3 (4), Xe (7), ethane (9),
isobutane (11), O2 (15), N2 (16, no effect), N2O (18), H2 and p-H2 (21,
47), D2 and o-D2 (22, 48), CO (23), DME (25), C2F6 (29), NH3 (31),
C2H2F4 (43), TMA (44), HFO-1234ze (45, output only), C4F7N (49), C3F8
(52), SiH4 (60) and CCl4 (61).

## Impact on results

**H2S and TMA (MB-58) change transport results by tens of percent.** The
moderation test of 11.20 (`ABS(EI-0.024999).LE.1D-4`) also catches the
ordinary 0.025 eV levels of H2S (rotation R1) and TMA (level 2). An
electron that excites them is left with 0.025 eV. 20 °C, 760 Torr, 0 K
gas, 4·10⁷ collisions, upstream → fixed:

| gas, E | drift (µm/ns) | mean energy (eV) |
|---|---|---|
| Ar/H2S 90/10, 1 kV/cm | 29.62 → 39.51 (+33 %) | 0.1725 → 0.4192 |
| H2S, 10 kV/cm | 36.42 → 59.55 (+64 %) | 0.1984 → 0.5269 |
| Ar/TMA 90/10, 1 kV/cm | 71.63 → 47.82 (−33 %) | 0.3255 → 0.6899 |

The fixed values agree with Magboltz++ 44b54a0, which has an exact test
that never fires (and so also misses the real moderation levels).

**SF6 (MB-17 + MB-22) changes transport results.** Level 2 of GAS30 is the
V4 dipole vibration, marked anisotropic (KIN(2)=1). Its forward-scattering
probability was first computed wrongly (MB-22: about −5 … −30) and then
overwritten with 0 (MB-17). The MONTE routines scatter forward if
R ≤ PSCT, so both make every V4 excitation scatter straight back. Fixed,
PEQIN(2) = FWD/(FWD+BCK) = 0.86 … 0.93 (0.25–3.75 eV). Pure SF6, 20 °C,
760 Torr, 4·10⁷ collisions, upstream → fixed:

| E (kV/cm) | drift (µm/ns) | mean energy (eV) | α (1/cm) | η (1/cm) | α−η (1/cm) |
|---|---|---|---|---|---|
| 20 | 60.25 → 61.63 (±0.1%) | 0.600 → 0.649 | — | 5.007e5 → 4.787e5 | |
| 50 | 111.5 → 112.5 | 6.151 → 6.173 | 185.4 → 182.8 | 6914 → 6600 | −6729 → −6417 |
| 100 | 189.1 → 190.3 | 8.476 → 8.498 | 1213 → 1221 | 1128 → 1104 | 85 → 117 (±6) |
| 200 | 330.1 → 331.3 | 11.577 → 11.598 | 4184 → 4179 | 354.7 → 353.2 | |

Near the critical field the effective ionisation coefficient changes by
about 40%. Ar/SF6 90/10 at 1 kV/cm: drift +0.8%, attachment −0.9%. The
RPC mixture C2H2F4/iC4H10/SF6 95.2/4.5/0.3 at 50 kV/cm is unchanged within
errors.

**Other gases.** Cross-section tables change as follows (upstream →
fixed; printouts from `reproduce.sh`):

- MB-02 methylal QIN(5) at 125 … 375 eV: −1.5e-16 … −6.0e-16 → 2.4e-16 …
  1.0e-16 cm² (negative cross sections upstream).
- MB-03 C2F6 PEQIN(13/14): 1.0 → 0.149.
- MB-04 C2H2F4 PEQIN(1) above 20 eV: 0 (isotropic) → 0.52 … 0.93.
- MB-18 CO PEQIN(146): 0 → 0.49 … 0.91.
- MB-21 C4F7N above 1 keV: bremsstrahlung now in levels 27–29 with EIN=0.
- MB-01/07/10: values read from unrelated memory below the respective
  thresholds; with bounds checking these are crashes.

With 4·10⁶ collisions, MC results upstream vs fixed for 15 affected gases
at 100/1000/10000 V/cm agree within statistical errors except C2F6 at
10 kV/cm (drift −0.4%, ≈3σ; MB-03); C2H2F4 at 1 kV/cm did not finish in
90 min in either version. Most of the other defects act at energies
below about 0.01 eV or at the boundaries of tables, or change angular
distributions of weak channels.

**Gas routines (MB-44 … MB-56).** Before/after runs (fork at MB-43 vs.
MB-56, 4·10⁷ collisions (NH3 8·10⁸, Ar/NH3 4·10⁸, DME 1.6·10⁸), 20 °C,
760 Torr, thermal motion, same random sequence):

| gas, E | drift (µm/ns) | mean energy (eV) | attachment (1/cm) | fixes |
|---|---|---|---|---|
| C2F6, 1 kV/cm | 67.46 → 72.94 (+8.1 %) | 0.0664 → 0.0682 | — | MB-50 |
| C2F6, 10 kV/cm | 109.6 → 123.5 (+12.7 %) | 0.703 → 0.976 | 14.9 → 28.7 | MB-50 |
| C3F8, 1 kV/cm | 44.61 → 48.82 (+9.4 %) | 0.0550 → 0.0565 | — | MB-50 |
| C3F8, 10 kV/cm | 107.2 → 132.7 (+23.8 %) | 0.324 → 0.469 | 17.3 → 37.0 | MB-50 |
| Ar/CCl4 90/10, 100 V/cm | 1.122 → 1.187 (± 1.5 %) | 0.0241 → 0.0256 | 1.039e7 → 9.65e6 | MB-45 |
| CCl4, 1 kV/cm | 1.153 → 1.178 (± 2.5 %) | 0.0242 → 0.0255 | 1.011e8 → 9.73e7 | MB-45 |
| DME, 1 kV/cm | 3.133 → 3.012 (± 0.8 %) | 0.0431 → 0.0400 | — | MB-53, 56 |
| NH3, 1 kV/cm | 1.763 → 1.765 (± 0.45 %) | 0.0387 → 0.0382 | — | MB-46, 52 |
| Ar/NH3 90/10, 1 kV/cm | 30.01 → 30.16 (± 0.09 %) | 0.3754 → 0.3737 | — | MB-46, 52 |
| Ar/C4F7N 90/10, 1 kV/cm | 27.49 → 27.43 (± 0.15 %) | 0.0772 → 0.0770 | 3.825e4 → 3.834e4 | MB-47 |

Unchanged within errors: Xe 50–400 kV/cm (MB-44, α within 0.4 %),
C4F7N 300 kV/cm and CO2/C4F7N 95/5 at 1 and 10 kV/cm (MB-47), CO 1 and
10 kV/cm (MB-52), DME 10 kV/cm. Ethane and SiH4 at 10 kV/cm give
identical output (MB-51: for SiH4 the levels lie above the energy range
of 4 eV; for ethane the change, ≤ 1.5e-19 cm² over 0.14 eV, decided no
collision).
The cross-section changes of the other fixes are listed in their
sections.

**Undefined values (MB-03, 05, 06, 11–16, 19, 20).** In a normal build
these take whatever value the memory has. Large local arrays are static
and zero, small ones are on the stack. The results are then deterministic
for one binary but can change with compiler, flags or platform. Example: Ar/O2
90/10 with IPEN=1 gives different drift tables with zero- and
NaN-initialised memory (MB-19/20).

## How they were found

1. **Bit-for-bit port.** The Nim translation checks every array index and
   crashed for 10 gases (MB-01, 07, 08, 09, 10).
2. **gfortran `-fcheck=bounds`** on the Fortran: 96 MC decks (every gas,
   B-field angles, thermal motion, Penning, high field) and every gas
   routine called directly at EFINAL = 0.3 eV … 200 keV, NANISO 0/1/2.
3. **Static scan** for interpolation search loops `DO n J=1,N / IF(X.LE.T(J))
   GO TO m` followed by a read of `T(J-1)`: 281 loops; 16 have no explicit
   guard, 3 of these are reachable (MB-10).
4. **Undefined variables:** whole program built with
   `-finit-real=snan -finit-integer=-1234567 -ffpe-trap=invalid` (first
   arithmetic on an undefined real traps) and compared against
   `-finit-local-zero` (any difference = an undefined value reaches the
   output). Repeated after each round of fixes until clean.
5. **Undefined outputs of the gas routines:** each gas called with all
   output arrays pre-filled with NaN / −1234567 vs. 0, comparing exactly
   the elements MIXER reads (MB-17 … MB-21). See
   `NimBoltz/tests/ub/undef.nim`.
6. **Never-written locals** (static, from the translator's symbol tables,
   `f2nim magboltz.f --undef`): a local variable that is read but never
   assigned, read, used as a DO variable or passed to an output argument
   anywhere in its routine. In upstream this lists 33 names: all the
   typo-type defects above (ESPRES, QMOM, O, QEXCTOT, QCOUNT, SUMATT,
   SUMINEL, XATT5/YATT5, DCYS) plus MB-25/26/27. What remains in `fixes`
   is harmless (dummy arguments VIRIAL1–6 and RDUM, the skipped
   XATT5/YATT5). gfortran's `-Wuninitialized` found none of these.
7. **Sibling diff** (`sibdiff.py`): near-duplicate routines (MONTEFT /
   MONTEFTA / MONTEFTG / MONTEFTH and the thermal variants, MIXER/MIXERT,
   ELIMIT*, GAS21/GAS47, …) aligned statement by statement; a token
   substitution that occurs only once between two routines is reported.
   Found MB-24, MB-28, MB-29.
8. **Rewriting the gas routines by hand** (the port has one module per
   gas built on shared helpers; every module must reproduce the Fortran
   bit for bit, so every irregularity has to be coded explicitly and
   stands out), then `tools/idxscan.py`: every threshold test, anisotropy
   copy, table end and formula whose level index differs from the
   level's own (MB-44, 51, 52, 53). The remaining hits of the scan on
   `fixes` are the deliberate ones (superelastic levels use the energy
   of their partner, N2 copies level 121's distribution to 122–127, CO
   level 111 uses the offset of 112, which has the same |EIN|).
   Found MB-44 … MB-56.
9. **Comparison with Magboltz++** (the C++ translation by H. Schindler,
   gitlab.cern.ch/garfield/magboltzpp, 44b54a0, with its own defects
   fixed): the cross-section tables of the 61 gases both have, at EFINAL
   = 1, 40, 400 and 4000 eV, and the 96 MC decks. Every difference was
   traced to one side. Found MB-58 … MB-61 (MB-59: Magboltz++ had
   already corrected it).

**AddressSanitizer / UBSan / valgrind.** Run afterwards for comparison:
upstream built with `-fsanitize=address,undefined` on all decks of
`decks/` finds 5 of the 9 out-of-bounds cases (MB-08, 09, 10×3). It misses
MB-01 and MB-07: the negative index lands inside another large, valid
array, which ASan cannot distinguish from a legal access. ASan does not
check initialisation, so it finds none of the undefined-variable defects.
UBSan's object-size check reports only the propane read (MB-08) again. Valgrind could not be used: its loader
fails to map the 1.7 GB static data segment of Magboltz. `-fcheck=bounds`
knows the declared bounds of every array, including COMMON blocks and dummy
arguments, so it is the stronger tool for Fortran. `-finit-*` with FP traps
plays the role of valgrind's uninitialised-value tracking for reals.

## Reproducing

`bugs/reproduce.sh [magboltz.f]` builds the source with the checks above and
runs one case per defect (`cases.txt`, decks in `decks/`, cross-section
printer `tools/xsec.f`). Upstream:

    git show master:magboltz-11.21.f > /tmp/up.f; bugs/reproduce.sh /tmp/up.f

Upstream, every case reports the error or the value listed below. The
`fixes` branch reports `clean` or the corrected values.

## Details

### MB-01 GAS22 / GAS48 (D2, ortho-D2): inverted 8 eV test

Lines 58249, 58279 (GAS22) and 91450, 91480 (GAS48):
`IF(EN.GT.8.0) GO TO 425` / `GO TO 430` for the superelastic rotational
levels 6→4 and 8→6. The other five superelastic levels, and all seven in
the H2 originals GAS21/GAS47, use `IF(EN.LT.8.0)`. Below 8 eV the lookup
`PEQIN(n,I)=PEQEL(2,I-IOFFN(n))` then runs with `I-IOFFN(n) ≤ 0` (index
−648 in deck `d2`); above 8 eV the anisotropy is never set.
Fix: `EN.LT.8.0`. Repro: deck `d2` / `od2`, bounds check.

### MB-02 GAS24 (methylal): wrong grid in the search loop

Line 62049: the loop for QIN(5,I) runs to NEXC1 (31 points) but compares
`EN.LE.XEXC(J)` (26 points) and then interpolates YEXC1 over XEXC1(J-1:J).
The interval is wrong at all energies (negative cross sections above
≈100 eV) and XEXC(27:31) are read beyond the array. Fix: `XEXC1(J)`.

### MB-03 GAS29 (C2F6): ESPRES for EPSRES

Lines 66342, 66363: `PEQIN(13/14,I)=1.0-ESPRES`. `ESPRES=0.705` exists
only in a commented-out parameter set; the active set defines
`EPSRES=0.851`. Implicit typing made ESPRES an undefined local (zero on
most systems, i.e. PEQIN=1). Fix: EPSRES.

### MB-04 GAS43 (C2H2F4): `DO 420 L=9`

Line 81512. Without a comma fixed-form Fortran reads this as the assignment
`DO420L=9`; the "loop" body runs once with L = NION+1 = 4. Above 20 eV only
level 4 gets the elastic angular distribution instead of the nine
vibrational levels 1–9. Fix: `DO 420 L=1,9`.

### MB-05 MONTEBT: IMBTP for IMBPT

Line 3798: `IMBTP=0`. The other thermal routines (MONTET, MONTEAT, MONTECT,
MONTEF*T) set `IMBPT=0` after `CALL GERJAN`. IMBPT indexes the
pre-generated Maxwell–Boltzmann table RNMX, so MONTEBT (B⊥E, ITHRM=1)
starts at an index taken from the stack (`-finit-integer=-1234567` gives
RNMX(−1234566), line 3844). Fix: `IMBPT=0`.

### MB-06 GAS44 (TMA): PQ1/PQ2 below 0.001 eV

For EN ≤ XEN(2) = 0.001 eV (line 82188) the code jumps past the
computation of PQ1/PQ2 and stores them in PEQEL(2,I). Fix: PQ1=0.5, PQ2=0
(isotropic), which are also the table values at XEN(2).
*Interpretation:* isotropic is the only value consistent with the table.

### MB-07 GAS14 / GAS34 (H2O, methanol): superelastic lookup without guard

Lines 42204 (GAS14, level 211) and 73120 (GAS34, level 53). Superelastic levels have no
threshold, so `PEQEL(2,I-IOFFN(n))` indexes ≤ 0 for EN ≤ |EIN(n)| (index
−1581 / −1024). The same lookup is guarded in the other gases.
Fix: `IF(EN.GT.DABS(EIN(n)))`; in-bounds evaluations unchanged.

### MB-08 GAS10 (propane): NIONG=46

Line 35521. XION, YIONG, YIONC have 45 entries; `IF(EN.GT.XION(NIONG))`
and the search loop read XION(46) at every energy above the threshold. Fix: NIONG=45 (and `J=NIONG` in the
loop fall-through).

### MB-09 GAS46 (n-propanol): stray loop

Line 85425: `DO 830 K=1,NION / SUMION=SUMION+QION(K,I)` sits after the
energy loop (inside the SCRPT block) and reads QION(K,4001). SUMION is not
used; GAS34 has the same lines commented out. Fix: comment out.

### MB-10 Search loops starting at 1

281 loops `DO n J=1,N / IF(X.LE.T(J)) GO TO m / … / m … T(J-1)` read T(0)
when the first comparison succeeds. Reachable in GAS61 (CCl4, every EN ≤
XION(1), line 101040), GAS19 and GAS60 (ethene, SiH4, at EPOINT=ENROT(1),
lines 53483, 100150); the others are protected by an earlier threshold
test. Fix: start every such loop at 2 (no change for in-bounds paths).

### MB-11 GAS43 (C2H2F4): EPSIL below 1E-4 eV

Line 81126: for EN < XEL(1) the code jumps to label 30 without computing
EPSIL, which is stored in PEQEL(2,I) for NANISO=2. Fix: the table value at
XEL(1), 1−YEPS(1) = 0 (isotropic), as is done for QMMT/QELA there.

### MB-12 GAS7 (Xe): wrong jump target

Line 30920: below the threshold of charge state 2 the code jumps to 3350,
past `QION(3,I)=0` and `Q456=0` at 3250, while every other charge state
jumps to the next section. QION(3,I) then keeps the caller's value plus an
undefined Q456. Fix: `GO TO 3250`.

### MB-13 GAS21/22/47/48 (H2, D2, p-H2, o-D2): QMOM

Lines 55148, 57818, 88380, 91019: the NANISO=1 branch uses
`0.5+(QELA-QMOM)/QELA`, but these routines call the momentum-transfer
cross section QELM; QMOM is never set. Fix: QELM.

### MB-14 GAS22 / GAS48: `NANISO.EQ.O`

Lines 57807, 91008: the letter O, an undefined implicit REAL. Fix: `0`.

### MB-15 GAS49 (C4F7N): 3-body attachment without data

Line 93298. XATT5/YATT5(14) are declared and used (QATT(5,I)), but there
is no DATA statement for them. Fix: skip the channel (QATT(5,I)=0).
*Interpretation:* the data are probably missing by mistake; the author
should supply the table. GAS45 has a 3-body table with the same names.

### MB-16 Diagnostic sums read while undefined

GAS11 `QEXCTOT` (computed as QTOTEXC), GAS15 `QRSUM` (never zeroed), GAS18
`XSECDUM(61:120)` (not set on all paths), GAS23 `QCOUNT` (computed as
QIONC), GAS25 `SUMATT` and GAS34 `SUMINEL` (sum loops commented out). These
feed Q(1,I) → QTOT, which nothing reads, or Q(3,I) for NION>1. They do
not change results.

### MB-17 GAS30 (SF6): `PEQIN(2,I)=0.0` for `PEQIN(22,I)=0.0`

Line 68001, at label 719 (start of triplet dissociation level 22). This
leaves PEQIN(22,I) undefined between threshold and 3·EIN(22), and
overwrites the V4 anisotropy PEQIN(2,I) computed earlier with 0. Fix:
PEQIN(22,I). See "Impact".

### MB-18 GAS23 (CO): `PEQEL(1,` for `PEQEL(2,`

Line 61334: `PEQIN(146,I)=PEQEL(1,(I-IOFFN(146)))`. Row 1 of PEQEL is not
set by any gas routine; every other level of every gas uses row 2.
Fix: `PEQEL(2,`.

### MB-19 Penning fraction initialisation

GAS15 (O2), line 44168: `DO 21 K=1,76 / DO 21 L=1,3 / 21 CONTINUE` has no
body, so PENFRA(1:3,1:75) are undefined. With IPEN=1 a nonzero PENFRA(1,K)
turns excitations of these levels into Penning ionisations. GAS14/31/34/35/36/46 set PENFRA(1,K)
inside the loop over L instead of PENFRA(L,K); PENFRA(2:3,K) are only read
when PENFRA(1,K) ≠ 0, so this has no effect. Fix: `PENFRA(L,K)=0.0`.

### MB-20 Outputs of the gas routines that are never set

Calling each gas routine with NaN-filled output arrays shows outputs that
MIXER/MIXERT read but the routine never sets, i.e. the routines assume
zeroed arrays:

- PENFRA(1:3, levels): GAS13, 15, 17, 20, 24, 26, 28, 32, 33, 37–43, 45,
  49–51, 53–59, 61 (all or most levels);
- NC0, EC0, WK, EFL, NG1, EG1, NG2, EG2 of the single ionisation channel
  (NION=1): GAS13, 17, 20, 24, 26–28, 32, 33, 37–42, 50, 51, 53–59. NC0
  is added to the ionisation count (`IEXTRA=IEXTRA+NC0(I)`, ANCION);
- EI and KIN of the bremsstrahlung levels NIN+1…NIN+3 used for EFINAL >
  1 keV: GAS43, 45, 49, 61 (GAS1 sets them to 0 explicitly);
- Q(1,·) (total cross section): 20 gases; it only feeds QTOT, which is
  not read.

In MIXER the per-gas arrays are partly small local arrays on the stack.
Fix: GASMIX zeroes every output before calling the gas routine, which
is what the routines assume. Output is unchanged where memory was zero.

### MB-21 GAS49 (C4F7N): NIN=29

Line 92789. The routine defines 26 levels; levels 27–29 have no EIN, QIN
or KIN. The bremsstrahlung block (copied from GAS45, which has 29 levels)
fills QIN(30:32), which are used, with undefined EIN, only after
`NIN=NIN+3` for EFINAL > 1000 eV. The level descriptions SCRPT(40:42),
i.e. levels 27–29, are the three bremsstrahlung channels. Fix: NIN=26,
bremsstrahlung in QIN(27:29).

### MB-22 GAS30 (SF6): `Q(2,I)` for `QIN(2,I)`

Line 67734: `XMT=(1.5-FWD/(FWD+BCK))*Q(2,I)` multiplies the dipole angular
factor by the *elastic* cross section instead of the V4 cross section, so
`PEQIN(2,I)=0.5+(QIN-XMT)/QIN` is −5 … −30. With QIN(2,I) it is
FWD/(FWD+BCK), the same construction as for the dipole part ADIP of V3
(level 6, line 67810) and in GAS1/GAS8. Fix: QIN(2,I). See "Impact".

### MB-23 MONTEB / MONTEBT (B⊥E): DIFXX error is NaN

`DFXXST(J1)=5D15*(SUMXX-SXXOLD)/(ST2-ST2OLD)` is evaluated in the first
segments, where ST2 = ST2OLD = 0, giving NaN. The printed error of the
transverse diffusion parallel to B is therefore `NaN%` in every B⊥E run
with anisotropic scattering. MONTE and MONTEA guard the same expression with
`IF(ST2.NE.0.0D0) … ELSE DFXXST(J1)=0`. Fix: the same guard. DIFXX itself
is unchanged.

### MB-24 MONTEFTG / MONTEFTH: secondary-electron direction

The direction of the secondary electron after an ionisation is computed by
the same three statements in all MONTEFT* routines (lines 14528–14530 in
MONTEFT). MONTEFTG (line 16255) uses `DCYS` instead of `DCY2` in
DCY(NCLTMP); MONTEFTH uses `DCYS` in DCX(NCLTMP) (16998) and
`DCZ2*F6S*ARGZ*F5S*F8S` instead of `DCZ2*F6S+ARGZ*F5S*F8S` in DCZ(NCLTMP)
(16996). DCYS is an implicit, never-set scalar there, so the secondaries
start in a direction that is not even a unit vector and depends on stack
contents. These routines are used by the non-thermal high-field
calculation (ALPCLCB/ALPCLCC) for B⊥E and B at a general angle; the
thermal variants are correct. Found because zero- and NaN-initialised
builds of the high-field B decks gave different output. Effect in Ar/CO2
90/10 at 30 kV/cm, B = 5 T (4·10⁷ collisions): the main MC results are
unchanged (they do not use these routines); the pulsed-Townsend
attachment coefficient changes by +10% (B⊥E) and −8% (45°), about 1.5σ,
and α−η from the time-of-flight analysis by less than its error. The
secondaries forget their initial direction quickly at this field.

### MB-25 GAS9 / GAS19 (ethane, ethene): NBRM

Lines 34844 and 53503: `DO 780 J=2,NBRM`. The bremsstrahlung table has
NBREM=25 points (used in the fall-through `J=NBREM`); NBRM is undefined.
With NBRM=0 the loop never runs and every energy above 1 keV uses the last
interval: QIN(56) of ethane is a constant 7.1e-24 cm² instead of
4.6e-22 … 1.3e-22 cm² (1.5–7.5 keV). With a large garbage value the result
happens to be correct, so the outcome depends on the stack. Fix: NBREM.

### MB-26 GAS23 (CO): N2XC5

Line 61156: `DO 509 J=2,N2XC5` for the A³Π v=4 level (QIN(127)); the
table XEXC5/YEXC5 has NEXC5=9 points. With N2XC5 undefined (0) the last
interval (17.5–20 eV) is extrapolated down to the threshold: QIN(127) at
7.55 eV is 1.32e-18 instead of 4.29e-18 cm², at 12.55 eV 1.15e-18 instead
of 2.11e-18. Fix: NEXC5.

### MB-27 GAS43 / GAS60: names in unreachable fall-throughs

`J=NVIBR1` (GAS43, lines 81418, 81442) and `J=NNVIBR` (GAS60, 99767,
99783, 99799) after search loops over XVIBR(NVIBR); the fall-through
cannot be reached because EN.GT.XVIBR(NVIBR) is excluded before the loop.
No numerical effect; renamed to NVIBR.

### MB-28 MONTEFTG / MONTEFTGT: Penning test inverted

Lines 16128 and 7739: `IF(PENFRA(1,I).EQ.0.0) THEN` guards the Penning
transfer block, which then draws R and skips if R.GT.PENFRA(1,I). With
`.EQ.` the block only runs for levels without Penning transfer and then
always skips, so for B⊥E at high field there is never a Penning
transfer, whatever IPEN and PENFRA say. All other MONTE routines use
`.NE.0.0`. Fix: `.NE.`.

### MB-29 ELIMITBT: clamp stored in the wrong variable

Line 4976: `DCZ2=DMIN1(DZCOM,1.0D0)`; ELIMITT and ELIMITCT have
`DZCOM=DMIN1(DZCOM,1.0D0)`. DCZ2 is not used afterwards, so DZCOM is not
clamped. Only matters if rounding makes DZCOM exceed 1. Fix: `DZCOM=`.

MB-30 to MB-36 were found when the six pasted per-gas blocks of MIXER and
MIXERT were merged into one loop over the gases in the port: blocks that
differ from their siblings by more than the gas number.

### MB-30 MIXER: fluorescence energy of gas 1 for gas 2

Line 10476: `EFL(NP)=EFL1(KION)` in the shell loop of gas 2; gases 1, 3–6
and MIXERT use their own `EFLn`. No effect on results: no routine reads
EFL (nor NG1, EG1, NG2, EG2, WKLM; only NC0 and EC0 of /IONFL1/ are used).
Fix: `EFL2`.

### MB-31 MIXER: anisotropic inelastic scattering of gas 2 unreachable

Line 10536: the `ENDIF` that closes `IF(KIN2(J).EQ.1) THEN` comes after
the `IF(KIN2(J).EQ.2) THEN ... ENDIF` block, so the KIN=2 test sits inside
the KIN=1 block and can never succeed. NANISO=2 is fixed in SETUP and most
gas routines set KIN(J)=NANISO, so in every calculation at 0 K the inelastic
levels of the second gas of the mixture are scattered isotropically
(INDEX=0) instead of with their PEQIN; with the same gases in another
order the result changes. Gases 1, 3–6 and MIXERT are correct. Fix: move
the `ENDIF` up.

The effect is large for polar molecules, whose rotational excitation is
strongly forward-peaked. Ar/H2O and Ar/methanol 90/10, 20 °C, 760 Torr,
1 kV/cm, B=0 (NMAX reduced 10×, drift velocity in µm/ns):

| mixture | upstream, Ar first | upstream, Ar second | fixed, Ar first |
|---|---|---|---|
| Ar/H2O | 4.52 ± 1.2% | 10.56 ± 1.3% | 10.59 ± 1.2% |
| Ar/methanol | 7.30 ± 1.3% | 26.91 ± 1.0% | 27.23 ± 1.0% |

Upstream depends on the order of the gases in the input; the fixed program
gives the "polar gas first" result either way. Ar/iso-propanol and
Ar/n-propanol move from 6.98 to 23.6, Ar/N2O 10% from 56.5 to 58.3.

### MB-32 MIXERT: anisotropy kind of gas 1 for the shells of gases 2–6

Lines 1143, 1184, 1225, 1266, 1306 (and the `.EQ.2` tests below them):
the shell ionisation loops of gases 2–6 test `KEL1(3)`; their single
ionisation branches and MIXER use `KELn(3)`. 37 gas routines set
KEL(J)=NANISO or 2 (anisotropic, PEQION from the shifted elastic PEQEL), 41
set KEL(J)=0 and GAS41/GAS58 set KEL(3)=1. When gas 1 and a gas with shells
come from different groups (Ar/CO2 and Ar/CH4 do not, Ar with any of the
41 does), the shells of that gas are scattered with the wrong angular
distribution in thermal runs. Fix: `KELn(3)`.

### MB-33 MIXERT: gas 3 attachment has process kind 0

Line 1680: `IARRY(KGAS,NP)=0.0` where the other gases have `IARRY=L`
(L=3). Only the branch for one attachment process (NATT ≤ 1) of gas 3 has
it. The thermal MONTE routines count `ICOLL(KGAS,IARRY(KGAS,I))`, so every
attachment to gas 3 increments `ICOLL(3,0)`, which lies before the array
in COMMON /OUTPTT/ (in TIME). Reproducer: Ar/CO2/CF4 80/10/10, thermal,
5 kV/cm (`decks/arco2cf4_thermal.in`; CF4 has one attachment process):
with `-fcheck=bounds` upstream stops at line 3042 of MONTET, `Index '0' of
dimension 2 of array 'icoll' below lower bound of 1`. Fix: `IARRY=L`.

### MB-34 MIXER, MIXERT: Penning delocalisation length times 1e-16

Lines 10368 (MIXER, gas 1) and 1852, 1884, 1916, 1948, 1980, 2012
(MIXERT, all gases): `PENFRA(2,NP)=PENFRA1(2,J)*1.D-16/DSQRT(3.0D0)`.
MIXER uses `1.D-6` for gases 2–6. PENFRA(2) is the delocalisation length
in microns (comment in the main program, lines 291–297) and the MONTEFT*
routines that use it work in metres (CONST9=CONST3*0.01D0 is in m/ps), so
1.D-6 converts it; 1.D-16 looks copied from the cross-section factors.
About 30 gas routines set PENFRA(2)=1.0 (µm) for their Penning levels; with
1.D-16 the Penning electron starts where the excited molecule was formed.
Affects high-field (TOF/SST) runs with IPEN=1: gas 1 at 0 K, every gas when
thermal. Fix: `1.D-6`.

### MB-35 MIXER: gas 6 attachment sum

Lines 11440–11441: `DO 822 KATT=1,NATT5` / `QATT(5,I)=QATT(5,I)+QATT5(KATT,
I)*AN6` in the block for gas 6. No effect on results: QATT, QSUM, QSATT,
QREL ("cross section data for integrals in OUTPUT") are not read outside
MIXER and MIXERT. Fix: NATT6, QATT(6,I), QATT6.

### MB-36 MIXERT: ionisation and attachment frequencies of the last gas

Lines 931–934 and 2061–2064: `DO 700 IE` and `DO 700 KGAS` share one
loop end, and `FCION(IE)=0`, `FCATT(IE)=0` stand inside the KGAS loop, as
do the scalings by EROOT(IE). After the loop FCION and FCATT hold the
ionisation and attachment frequencies of the last gas only (MIXER sums
over the gases). FRIEDLANDT prints their averages ("ESTIMATE USING
FRIEDLAND") for thermal runs at high field. Example: Ar/CO2 90/10,
thermal, 30 kV/cm: "AVERAGE IONISATION" 0.378E-03 (CO2 only) instead of
0.229E-02 ×10¹²/s. Fix: zero once per energy before the gas loop, scale
once after it.

### MB-37 MONTEBT: decorrelation arrays too short

Line 3801: `DIMENSION XST(1000000),YST(1000000),ZST(1000000),STO(1000000)`.
SETUP sets NCOLM, the length of this ring of stored positions, to 2000000
unless the field is high or the mixture has more than 3% molecular gas;
all other MONTE routines dimension the arrays 2000000. From the
1000001st collision on MONTEBT writes past XST, YST and ZST into the
neighbouring arrays, so the positions that the diffusion sums subtract
are wrong. With bounds checking: "Index '1000001' of dimension 1 of array
'xst' above upper bound of 1000000" at line 3967. Example (deck
`ar_bperp_thermal`: pure Ar, thermal, 1 kV/cm, 1 T at 90°, NSCALE/10):
DIFXX 0.2263D+22 instead of 0.1627D+04 cm²/s, DIFYY 0.3587D+05 instead of
0.1223D+04, DIFZZ 0.2231D+05 instead of 0.2076D+03; drift velocity and mean
energy are unchanged. Fix: dimension 2000000.

### MB-38 Thermal MONTE routines: moderation loss from the lab-frame energy

Since 11.20 a collision with the energy loss EIN = 0.024999 eV (vibration
moderation: GAS45 HFO-1234ze level 13, line 83344; GAS49 C4F7N level 13,
line 92906; GAS51 CF3Br level 5, line 94468) takes all of the incident
energy but 0.024999 eV: `IF(ABS(EI-0.024999).LE.1D-4) EI=E-0.024999`.
In the nine thermal routines the collision is computed in the rest frame
of the gas molecule, where the incident energy is EOK; E is the energy in
the lab frame (MONTET 3027, MONTEAT 3527, MONTEBT 3929, MONTECT 4382,
MONTEFTT 5566, MONTEFDT 6422, MONTEFTGT 7634, MONTEFTHT 8577, MONTEFTAT
9545). The residual energy is then EOK − E + 0.025 eV instead of 0.025 eV.
When E exceeds EOK by more than 0.025 eV the loss exceeds the collision
energy: MONTE*T clamp it afterwards (`EOK.LT.EI`), leaving 0.0001 eV;
MONTEF*T test `EOK.LT.EI` before the catch, so the electron leaves with
SMALL = 1E-20 eV. Fix: `EI=EOK-0.024999`.

The effect on transport results is small in the cases tried (thermal,
20 °C, 760 Torr, NSCALE/100): in pure HFO-1234ze and C4F7N at 100 and
1000 V/cm the results are identical (the moderation level is not
reached); pure CF3Br, drift 0.5613 → 0.5628 µm/ns (±20%) at 100 V/cm and
5.371 → 5.431 µm/ns (±2.5%) at 1 kV/cm, mean energy unchanged. Ar/CF3Br
90/10 at 1 kV/cm (NSCALE/10, with SST and TOF): drift 64.23 µm/ns in both,
attachment 4673 → 4671 /cm (±0.18%), TOF drift 87.87 → 88.06 µm/ns
(±0.2–0.3%).

### MB-39 MONTEF* routines: azimuth of the ionisation secondary

At an ionisation the ten avalanche routines give the secondary electron
"free kinematics" angles: the polar angle from transverse momentum balance
and the azimuth opposite to that of the scattered primary, PHIS = PHI0 + π,
wrapped into [0, 2π]:

    PHIS=PHI0+API
    IF(PHIS.GT.F4) PHIS=PHI0-F4

(F4 = 2π; MONTEFTT 5776/5798, MONTEFDT 6637/6659, MONTEFTGT 7840/7862,
MONTEFTHT 8785/8807, MONTEFTAT 9752/9774, MONTEFT 14503/14525, MONTEFD
15175/15197, MONTEFTG 16229/16251, MONTEFTH 16971/16993, MONTEFTA
17695/17717.) The wrap subtracts 2π from PHI0 instead of PHIS, so for
PHI0 > π the secondary gets the azimuth of the primary itself. Fix:
`PHIS=PHIS-F4`.

No effect is resolved at the statistics tried. Ar/CO2 90/10 at 30 kV/cm,
0 K (NSCALE/10, 16 seeds each, with NimBoltz, which reproduces both
versions bit for bit): all SST, PT and TOF results agree within 2.2σ;
the largest relative change is the TOF transverse diffusion,
2009 ± 36 → 2075 ± 26 cm²/s (+3.3%, 1.5σ). Single Fortran runs of six
decks (Ar/CO2 with B at 0°, 45° and 90°, SF6, a three-gas chain) change
by the scatter of the fast runs; a deck without ionisation is identical.

### MB-40 TOFG: NaN attachment rate without ionisation

TOFG (B ⊥ E, line 8063) replaces the attachment/ionisation ratio that
MONTEFTG counted in the avalanche by the ratio of the collision
frequencies, `ATTOINT=FRATT/FRION`. Without ionisation FRION = 0, so
ATTOINT is infinite, and the branch below for this case
(`IF(ATTOINT.EQ.-1.0D0)`, MONTEFTG's mark for "no ionisation") is never
taken: the attachment rate becomes ∞/(1−∞) = NaN. TOF and TOFH keep
MONTEFT's ratio and are not affected. Fix: `IF(FRION.GT.0.0D0)
ATTOINT=FRATT/FRION`.

Pure SF6 at 5 kV/cm, B = 1 T ⊥ E (`decks/sf6_bperp.in`): upstream prints
`ATT= NaN` (PT rates) and `ALPHA-ATT /CM.= NaN`; fixed, ATT = 4.86 and
(α−η) = −5.4·10⁵ /cm.

### MB-41 ALPCALCT: no reduced plane spacing when α and η nearly cancel

The drivers of the SST/PT/TOF runs place the sampling planes for a net
gain of 3 between neighbours, from ALPHAST = 0.85·|α − η| of MONTE. When
α and η nearly cancel, this spacing is long compared with 1/α and 1/η.
Version 11.12 added a shorter spacing for that case to ALPCALC and to the
six ALPCLC* drivers (`IF(ALPHA.GT.(10.0*ALPHAST).OR.ATT.GT.(10.0*ALPHAST))`:
ALPHAST × 30, 15 or 8 depending on α relative to the density-corrected
100 and 50 /cm). ALPCALCT (thermal, B = 0; line 5217) kept the 11.11 code;
all 19 versions 11.1–11.21 in this repository show the block appearing in
11.12 in seven drivers and never in ALPCALCT. Fix: the same block, with its
CORR, after line 5217.

Pure SF6, thermal, 760 Torr, 20 °C (fast mode, NSCALE = 4·10⁶): at 95 and
100 kV/cm MONTE gives α = 1097 / 1205 /cm and η = 1240 / 1131 /cm, and the
block would set the spacing to 3.0 and 5.8 µm; ALPCALCT uses 30 times
that, 90 and 174 µm. Upstream the SST avalanches had not finished after
4500 s (the program stays in MONTEFDT); with the fix the whole run takes
130 s (95 kV/cm: SST α = 916 ± 7 %, η = 704 ± 7 % /cm; VD = 177.4 µm/ns).
At 110 kV/cm (α = 1476, η = 938 /cm) the condition is false and the
output is identical.

### MB-42 ALPCLC*: /CTWNER/ errors in the wrong unit

After an SST/TOF run every driver replaces α and η in /CTOWNS/ and their
errors in /CTWNER/. The errors are percentages everywhere else: MONTE*
store `100·√N/N` (e.g. line 12249), ALPCALC and ALPCALCT store the SST
errors, which are printed as `+- … %` (lines 14015, 5250), and Garfield++
(`MediumMagboltz::RunMagboltz`, current master) prints `ctwner_.alper` and
`ctwner_.atter` as `+/- %5.2f%%`. The six TOF drivers store an absolute
error instead, `ALPER=RALPER*ALPHA/100.` and `ATTER=RATOFER*ATT/100.`
(RALPER and RATOFER are in percent): ALPCLCA 17227/17229, ALPCLCAT
9253/9255, ALPCLCC 16470/16471, ALPCLCCT 8259/8261. Two of them go further
wrong:

- ALPCLCB (lines 15760/15761) assigns the two errors to `ALP1ER` and
  `ATT1ET`, locals that are never read, so /CTWNER/ keeps the errors MONTEB
  computed for its own α and η, which the TOF values have replaced;
- ALPCLCBT (line 7342) has `ATTER=RATOFER*ATT*100.`, 10⁴ times its
  siblings.

Fix: `ALPER=RALPER`, `ATTER=RATOFER` in all six. Interpretation: the
percent unit is taken from the majority of the stores and from the main
caller; if the absolute error was intended for the TOF drivers, MONTE*,
ALPCALC, ALPCALCT and Garfield++ are wrong instead.

Magboltz itself never prints /CTWNER/ (OUTPUT2 does not read it), so the
effect is limited to programs that call Magboltz and read /CTWNER/ after
it returns. With the same runs as the printed values (`/CTWNER/` printed
by a probe WRITE after each driver), Ar/CO2 90/10 at 30 kV/cm, B = 1 T ⊥ E:

| | α (1/cm) | ALPER upstream | ALPER fixed | η (1/cm) | ATTER upstream | ATTER fixed |
|---|---|---|---|---|---|---|
| ALPCLCB (0 K) | 208.49 | 2.362 (MONTEB) | 2.71 | 2.019 | 24.25 (MONTEB) | 6.20 |
| ALPCLCBT (thermal) | 208.36 | 2.287 | 1.10 | 2.076 | 1306.1 | 6.29 |

The fixed values equal the errors printed with the PT/TOF rates. All
printed output is unchanged.

### MB-43 MONTEFDT: NaN direction at a turning point

MONTEFDT (thermal SST) recomputes the z direction cosine from the other
two before the velocity of the electron relative to the gas molecule,
`DCZ2=AIS*DSQRT(1.0D0-DCX2*DCX2-DCY2*DCY2)` (line 6361; none of the other
nine avalanche routines does this). Near a turning point of the flight
along z (DCZ2 ≈ 0) rounding makes the argument −1·10⁻¹⁶ … −4·10⁻¹⁶ and
DCZ2 becomes NaN. The energy bin of the collision is then 1. If the
collision is null (most likely), the next flight starts again from the
previous, finite direction and the run recovers, having used one wrong
null-collision test. If the collision is real, the NaN propagates into
the scattered direction, energy and position; no plane is ever crossed,
and since the limit ITER > NMAX is only tested when a new primary starts
(the test in the flight loop, line 6264, is commented out), MONTEFDT
never returns. Fix: `DSQRT(DMAX1(0.0D0,...))`.

Found as a hang of the regression deck `hi_arco2_nob_t1` (Ar/CO2 90/10,
30 kV/cm, thermal) after MB-39 changed the random sequence; a probe WRITE
shows the negative argument upstream in that deck (2 times, recovered),
in pure SF6 at 50 kV/cm (4 times, recovered) and at 95 and 110 kV/cm.
Unmodified 11.21 never finishes two thermal mixtures at 1 kV/cm,
Ar/HFO-1234ze and Ar/C4F7N 90/10 (regression decks gas45 and gas49, cut
at one hour in every run since the port began; NSCALE reduced to 4·10⁶):
with only this fix they finish in 380 s and 280 s, after 7 and 2 negative
arguments. Where upstream recovers, the fix only changes the random
sequence: pure SF6 at 50 kV/cm, thermal, SST α = 171.8 / 175.5 /cm
(± 2.2 %), η = 1576 / 1595 /cm (± 2.0 %), upstream / fixed.

### MB-44 GAS7 (Xe): 4D-sum tail written into level 2

Line 31470: above the end of the 4D-sum table (100 eV), the tail
`3710 QIN(2,I)=Y4DSUM(N4DSUM)*(X4DSUM(N4DSUM)/EN)**3*1.0D-18` is stored in
level 2 instead of level 23, the level the table above it fills. Level 2 is
the 1S4 resonance (Born dipole, f = 0.260), computed earlier in the loop and
overwritten here; level 23 stays 0. Above 100 eV one of the strongest
optically allowed excitations of Xe is therefore 10⁻⁴ of its value: QIN(2) at 150/400 eV is 3.3e-21/1.7e-22
instead of 3.4e-17/1.8e-17 cm². Fix: `QIN(23,I)`.
Swarm results in pure Xe (20 °C, 760 Torr, 50–400 kV/cm) do not change
within errors (α within 0.4 %): few electrons of a swarm pass 100 eV.
The level matters for fast electrons (primary ionisation tracks).

### MB-45 GAS61 (CCl4): V3 superelastic from the first energy bin

Line 101446: `QIN(7,I)=QIN(7,1)*APOPV3/DEGV3*1.D-16`. For I=1 this is the
intended scaling of the value just computed; for every later bin it takes
the final value of bin 1 (already ×1e-16) and scales it by 1e-16 again.
The V3 superelastic cross section (de-excitation of the asymmetric stretch,
0.0922 eV, populated at a few per cent at room temperature) is 9.6e-35 cm²
at every energy instead of 2e-17 … 4e-19 cm². The other three
superelastic vibrations (V2, V4, V1) use `QIN(n,I)`. In the same block the
tail above the table (line 101443) uses `(EN-EIN(8))` where the table
branch and the other vibrations use the superelastic energy `EN+EIN(8)`.
Fix: `QIN(7,I)` and `EN+EIN(8)`. Effect (upstream → fixed): Ar/CCl4 90/10
at 100 V/cm drift 1.122 → 1.187 µm/ns (+5.8 % ± 1.5 %), mean energy
+6.2 %, attachment rate −7.1 %; pure CCl4 at 1 kV/cm mean energy +5.4 %,
attachment −3.7 %; at 10 kV/cm attachment −1.2 %.

### MB-46 GAS31 (NH3): rotational weights of the transitions 0→1, 2→1, 1→2

NH3 is treated as a symmetric top; each rotational transition J→J±1 sums
the Born dipole cross section over K with the state populations PJ(J,K)
and the factor (J′² − K²)/(J′(2J+1)) (J′ the larger J). Three of the 28
transitions break this pattern:
- level 2 (00→10, line 69296): weighted with PJ(2), the population of
  J=1, K=0, instead of the initial state PJ(1) (J=0). Level 1 (10→00)
  correctly uses PJ(2).
- level 3 (20→10 + 21→11, line 69303): `PJ(5)*(AJG2+1.0)` for K=1; every
  other transition has `AJG2-K²`, here `AJG2-1.0`.
- level 4 (10→20 + 11→21, line 69305): `AJG=1.0` followed by `AJG=2.0`;
  the first is evidently meant as `AJ=1.0`. AJ keeps 2.0 from level 3, so
  2J+1 = 5 instead of 3.

Cross sections upstream vs fixed: level 2 is ×2.7 too large, level 3 ×1.18
too large, level 4 ×0.6 too small (all energies). Fix: PJ(1), `AJG2-1.0`,
`AJ=1.0`. Effect (8·10⁸ collisions; Ar/NH3 4·10⁸): pure NH3 at 100 V/cm
and 1 kV/cm mean energy 0.0384 → 0.0379 and 0.0387 → 0.0382 eV (−1.3 %,
± 0.03 %), drift
unchanged within errors (± 0.45 % at 1 kV/cm); Ar/NH3 90/10 at 1 kV/cm
drift 30.01 → 30.16 µm/ns (+0.5 % ± 0.09 %).

### MB-47 GAS49 (C4F7N): mass and table lengths of GAS45

GAS49 was built from GAS45 (C3F4H2, HFO-1234ze). Line 92826 keeps its
molecular mass, `E(2)=2.0*EMASS/(114.0416*AMU)`; C4F7N has 195.0383 (C
12.0107, F 18.9984, N 14.0067, the atomic masses behind 114.0416). The
elastic energy loss per collision, 2m/M, is 1.7× too large. Lines
92804/92805 keep NVIBL=NVIBH=19, the lengths of the GAS45 resonance
tables; the GAS49 tables XVIBL/YVIBL and XVIBH/YVIBH have 21 and 20 points,
so the low resonance is cut at 2.725 instead of 3.025 eV and the high one
at 12.0 instead of 12.7 eV (the tails are small). Fix: 195.0383, 21, 20.
Effect: Ar/C4F7N 90/10 at 1 kV/cm drift −0.22 % (± 0.15 %), mean
energy −0.26 % (± 0.09 %), attachment +0.24 % (± 0.07 %);
CO2/C4F7N 95/5 at 1 and 10 kV/cm and pure C4F7N at 300 kV/cm unchanged
within errors. *Interpretation:* if the 2025 cross sections were fitted
with this mass, the fit absorbed it; see QUESTIONS.md Q-03, Q-04 (E(3)
and the nitrogen K-shell look copied as well).

### MB-48 GAS44 (TMA): K-shell correction only above 803 eV

Line 82272: `QION(1,I)=QION(1,I)-AUGKC*QION(2,I)-AUGKN*QION(3,I)` takes
the carbon and nitrogen K-shells out of the counting ionisation, but it
sits after `IF(EN.LE.(2.0*EION(3))) GO TO 41`, the start of the angular
distribution of the nitrogen K-shell. It is skipped below 2·401.6 =
803 eV, so between the carbon K-edge (285 eV) and 803 eV the K-shell
ionisation is counted twice. O2 and N2 apply the same correction after
their K-shell, unconditionally. Fix: label 41 moved to the correction.
QION(1) changes by −0.2 % (400 eV) … −0.7 % (800 eV).

### MB-49 GAS29, GAS43 (C2F6, C2H2F4): K-shell search loop jumps to its own end

Lines 66042 (GAS29), 81212 (GAS43): `DO 151 J=2,N / IF(EN.LE.X(J)) GO TO
151 / 151 CONTINUE / J=N / 152 A=...`. The jump goes to the loop's own
CONTINUE instead of 152, so the loop always runs to the end and J=N: the
carbon K-shell is extrapolated from the last table interval at every
energy, a constant 3.7e-20 cm² (fixed: 1.2e-20 at 290 eV rising to 7.5e-19
at 1 keV). Through CRFAC this also changes the other ionisation channels
above 285 eV. Fix: `GO TO 152` (the fluorine K-shell next to it has it).

### MB-50 GAS29, GAS52 (C2F6, C3F8): vibrational anisotropy stored in the wrong levels

Lines 66308 (GAS29), 95746 (GAS52). The vibrational levels come in groups
(superelastic dipole / superelastic resonance = 1–6, inelastic dipole /
resonance = 7–12, for V6, V5, V7 at 0.065, 0.100, 0.155 eV). Loop
`DO 385 L=1,3` stores the dipole angular distribution of the superelastic
levels in `PEQIN((2*L-1),I)` (1, 3, 5); loop `DO 395 L=4,6` computes the
same for the inelastic levels 2L−1 = 7, 9, 11 — `XSECDUM(2*L-1)` and
`QIN((2*L-1),I)` in the same loop — but stores it in `PEQIN(L,I)`, i.e.
levels 4, 5, 6. So the three dipole vibrations scatter isotropically, and
levels 4 and 6 (resonances; C2F6 1−EPSRES, C3F8 isotropic) and 5 lose
their own distributions. Fix:
`PEQIN((2*L-1),I)`. PEQIN(7) at 0.5/2 eV: 0 → 0.82/0.91.
This is the largest effect of this series (upstream → fixed, 20 °C,
760 Torr):

| gas, E | drift (µm/ns) | mean energy (eV) | attachment (1/cm) |
|---|---|---|---|
| C2F6, 1 kV/cm | 67.46 → 72.94 (+8.1 %) | 0.0664 → 0.0682 | — |
| C2F6, 10 kV/cm | 109.6 → 123.5 (+12.7 %) | 0.703 → 0.976 (+39 %) | 14.9 → 28.7 |
| C3F8, 1 kV/cm | 44.61 → 48.82 (+9.4 %) | 0.0550 → 0.0565 | — |
| C3F8, 10 kV/cm | 107.2 → 132.7 (+23.8 %) | 0.324 → 0.469 (+45 %) | 17.3 → 37.0 |

(statistical errors of the drift velocities ≤ 0.04 %; same random
sequence in both runs).

### MB-51 Threshold test of another level

A level's cross section is computed after `IF(EN.LE.EIN(n)) GO TO …` with
n its own index everywhere except:

| gas | level | test on | lines |
|---|---|---|---|
| GAS9 ethane | 20 (9.291 eV) | EIN(21) = 9.433 | 34578 |
| GAS60 SiH4 | 25 (10.575 eV) | EIN(26) = 10.85 | 99958 |
| GAS60 SiH4 | 27 (11.25 eV) | EIN(28) = 11.75 | 99972 |
| GAS21, GAS47 H2, p-H2 | 98 (15.602 eV) | EIN(91) = 13.994 | 56159, 89391 |
| GAS22, GAS48 D2, o-D2 | 115 (14.747 eV) | EIN(114) = 14.741 | 58949, 92150 |
| GAS22, GAS48 D2, o-D2 | 132 (16.207 eV) | EIN(131) = 16.115 | 59018, 92219 |
| GAS23 CO | 199 (27.5 eV) | EIN(194) = 22.75 | 61785 |
| GAS61 CCl4 | 19 (8.868 eV) | EIN(18) = 8.365 | 101551 |

With the higher threshold (first three) the level is missing over 0.14–
0.5 eV above its threshold (SiH4 QIN(27) at 11.7 eV: 0 instead of
3.1e-18 cm²). With the lower one the Born formula is evaluated below the
level's own threshold; there `DLOG(BETA2*GAMMA2*EMASS2/(4*EIN))` ≈
ln(EN/EIN) is negative and the result is clamped to 0, so these five have
no effect (checked in the printouts). Fix: the level's own EIN.

### MB-52 Anisotropy missing, inverted or stored in another level

The inelastic levels take the elastic angular distribution at the energy
after the loss, `PEQIN(n,I)=PEQEL(2,(I-IOFFN(n)))`, above a multiple of
their threshold. Exceptions:
- GAS7 Xe levels 25–27 (2P3, 2P2, 2P1; lines 31492, 31505, 31518): the
  test `IF(EN.LE.(2.0*EIN(n))) GO TO` is there, the copy after it is
  missing; the other 47 levels have it. Isotropic → 0.80–0.89.
- GAS11 isobutane (line 37555): `IF(NANISO.EQ.2) PEQIN(2,I)=0.0` in the
  initialisation of ionisation channel 2 (should be PEQION(2,I), as
  for channel 1); with NANISO=2 the channel keeps 0.5 (anisotropic) below
  2·EION(2) = 34 eV instead of 0 (isotropic). PEQIN(2) is reset later.
- GAS15 O2 line 45688: level 59 (b1Σg+) stores its distribution in
  PEQIN(61,I): level 59 isotropic, level 61 gets level 59's between
  3·EIN(59) and 6 eV.
- GAS18 N2O line 51138: level 156 (triplets) tested on 2·EIN(147) instead
  of 2·EIN(156): anisotropic from 17.7 eV instead of 22.8 eV.
- GAS23 CO line 60973: vibration 115 has `IF(EN.GT.4.0) GO TO 425`, all
  other vibrations `IF(EN.LT.4.0)` ("vibrations set to isotropic below
  4.0 eV"): anisotropic below 4 eV, isotropic above. Line 61175: level
  128 (a3Π v=5–10) jumps past the copy that levels 123–127 and 129 have.
- GAS31 NH3 line 69683: `PEQIN(32,I)=PEQIN(32,(I-IOFFN(32)))` copies
  PEQIN, which is 0, instead of PEQEL: V1+V3 isotropic.
- GAS60 SiH4 line 99956: level 24 uses IOFFN(25), the offset of the next
  level (0.25 eV higher).
Fix: as the other levels. Effect on transport: CO at 1 and 10 kV/cm
unchanged within errors; the others were not run.

### MB-53 Wrong table or energy in a cross-section formula

- GAS15 O2 line 45869: the tail of level 72 above the table uses YVIB20
  (level 71), the table branch YVIB21: ×0.26.
- GAS22, GAS48 D2, o-D2 lines 58910, 92111: level 105 (B′1Σ v=1) has
  EIN(104), the energy of v=0, in the logarithm and the denominator of the
  Born formula (copied from level 104): +190 % at 14 eV, +1…9 % above
  16 eV. H2 (GAS21) has EIN(105).
- GAS25 DME line 63750: resonance part of the superelastic level 57,
  `AMPV3R*(EN*EIN(58))*(...)/EN` where detailed balance (and level 55)
  has `(EN+EIN(58))`: the resonance part is EN·0.18 instead of EN+0.18
  (×0.17–0.18), the level ×0.3–0.6 between 3 and 10 eV.
- No effect (same last value): GAS16 N2 line 48657 XSNG12(NSNG13) for
  XSNG13; GAS18 N2O line 50720 XV101(NV300) for XV300.

### MB-54 GAS45, GAS49, GAS61: debug output

GAS45 (line 84496) and GAS49 (94059) print a CSV line
`EN,QELA,QMMT,QSUP,…` with `WRITE(6,9011)` in every one of the 4000
energy bins, GAS49 then two header lines (94101); GAS61 prints
`ATRP=` (100644). This goes into the Magboltz output of every run with
these gases (4000 lines before the results). Commented out.

### MB-55 GAS4 (He-3): stray digit in the 4 1F table

Line 23710: `DATA Y41F/…,8.55D-5,7.86D-5,78.27D-5,6.78D-5,…`; the He-4
table (GAS3) has `7.27D-5` at the same place (700 eV). Upstream QIN(17)
(4 1F) and QIN(25), which scales the same table, are ×10.7 too large at
700 eV and ×6 at 725 eV. Fix: 7.27D-5.

### MB-56 GAS25 (DME): rotational populations weighted 2J−1

Line 62751: `PJ(K)=(2.0*AK-1.0)*DEXP(-AK*(AK+1.0)*B0/AKT)`. The degeneracy
of a rotational level J is 2J+1; the sum below starts with 1 for J=0, as
2J+1 gives; CO, methanol, ethanol and the propanols (same model) use
`(2.0*AK+1.0)`. Fix: `2.0*AK+1.0`. The J=1 population is ×0.4 too small
(QIN(1) at 0.1 eV: 1.5e-16 → 3.7e-16 cm²), high J slightly too large.
Effect with MB-53 (DME, upstream → fixed): mean energy −7.2 % (± 0.2 %)
at 100 V/cm and 1 kV/cm, drift −3.9 % (± 0.8 %) at 1 kV/cm, unchanged at
10 kV/cm.

### MB-57 SETUPT: thermal runs go on after an input error

SETUPT (line 2762) prints `ERROR IN GAS INPUT` for NGAS outside 1–6, a
missing gas or share, or shares that do not add up to 100 %, and returns
with LAST still 0 (READIN set it), so MAGBOLTZ continues the thermal run:
NMAX is not scaled, TMAX, NSTEP and the start values are not set, and the
run prints a full output of zeros and NaN (drift velocity 0, error NaN for
Ar 50 % / CO2 40 %, deck `decks/badfrac_thermal.in`). SETUP (gas at 0 K)
sets `99 LAST=1` there and the program stops. Fix: `LAST=1` before the
RETURN, as in SETUP.

### MB-58 MONTE routines: moderation test catches other 0.025 eV levels

Since 11.20 a collision with the energy loss 0.024999 eV (vibration
moderation: GAS45 HFO-1234ze level 13, line 83344; GAS49 C4F7N level 13,
line 92906; GAS51 CF3Br level 5, line 94468) takes all of the energy
but 0.024999 eV. The 18 MONTE and MONTEF routines (MONTE 11933, MONTEA
12405, MONTEB 12792, MONTEC 13223, MONTEFT 14298, MONTEFD 14959,
MONTEFTG 16022, MONTEFTH 16762, MONTEFTA 17489 and the thermal versions
MONTET 3026, MONTEAT 3526, MONTEBT 3928, MONTECT 4381, MONTEFTT 5565,
MONTEFDT 6421, MONTEFTGT 7633, MONTEFTHT 8576, MONTEFTAT 9544) recognise
the level by its energy:

    IF(ABS(EI-0.024999).LE.1D-4) EI=E-0.024999

The tolerance also matches the 0.025 eV levels of GAS44 (TMA, level 2,
`EIN(2)=0.025`, line 82062) and GAS55 (H2S rotation R1, level 2, line
96779): every such excitation leaves the electron with 0.025 eV instead
of removing 0.025 eV. (A scan of all 80 gases at EFINAL = 10⁵ eV finds
no other level within 1E-4 eV; the nearest, H2O level 107 at 0.0251 eV,
misses by 1E-6 eV.) In 11.19 the test was `IF(EI.EQ.AKT)`, which no
level met. For the effect see "Impact on results": H2S and TMA mixtures
change drift velocity by about a third, pure H2S at 10 kV/cm by 64 %.

Fix: MIXER and MIXERT mark the levels whose energy loss is exactly
0.024999 (the value written in the gas routine) in new COMMON blocks
/MODLV/ and /MODLVT/, and the 18 routines test the mark instead of the
energy. With the fix the three cases above give output identical to a
build with the tolerance reduced to 3E-7. GAS45/49/51 are unchanged.

### MB-59 GAS14 (H2O): superelastic bend tail falls as 1/E²

Line 42202, the V2 bend superelastic (level 211) above its table, i.e.
for EN+EIN(212) > XVIB1(NVIB1) = 20 eV:

    173 QIN(211,I)=YVIB1(NVIB1)*(XVIB1(NVIB1)/(EN+EIN(212)))/EN

The comment above the block reads "DIPOLE 1/E FALL OFF ABOVE ENERGY OF
XVIB1(NVIB1) EV", the table branch is the detailed-balance form
(E′/E)·σ(E′) with E′ = EN+EIN(212), and the inelastic partner QIN(212)
falls as Y·X/EN (line 42219). Detailed balance with that tail gives
(E′/E)·Y·X/E′ = Y·X/E; the extra division by EN makes it Y·X/(E′·E):
1/20 of the table branch at the table end, and 1/E². Fix:
`QIN(211,I)=YVIB1(NVIB1)*XVIB1(NVIB1)/EN`, continuous at 20 eV. The
level is weighted by the population of the (010) state, APOPV1 ≈ 4·10⁻⁴
at 20 °C, so the H2O decks of the regression give identical output.
Magboltz++ made the same change (its commit b30a1e6).

### MB-60 GAS22, GAS48 (D2, ortho-D2): attachment extrapolated above the table

Lines 58151 and 91352 test only the lower end of the attachment table
(`IF(EN.LT.XATT(1)) GO TO 290`); above XATT(NATT1) = 20 eV the search
loop ends with J=NATT1 and the last interval (18–20 eV, rising from
1.6 to 1.8·10⁻²¹ cm²) is extrapolated: 3.8·10⁻²¹ cm² at 40 eV,
1.0·10⁻¹⁹ at 1 keV, 4.0·10⁻¹⁹ at 4 keV, far above the 6·10⁻²¹ cm² peak
of the table. GAS21 and GAS47 (H2, para-H2), with the same table, test
`IF(EN.GT.XATT(NATT1)) GO TO 250` (lines 55423, 88655) and add only
their separate high-energy (2Σu) term. Fix: the same test, to 290.
Pure D2, 20 °C, 760 Torr, 8·10⁷ collisions: at 100 kV/cm the
attachment coefficient goes from 0.126 to 0.030 /cm (±15 %;
ionisation 1883 /cm, drift 784.9 µm/ns, unchanged); at 30 kV/cm
0.087 → 0.080 /cm, within the error. Magboltz++ stops at the table end.

### MB-61 GAS31 (NH3): H⁺ and H2⁺ ionisation start at 28 eV

Lines 69130–69237 compute the ionisation channels in table order; each
starts with `IF(EN.LE.XIONn(1)) GO TO 90`, which also leaves all later
channels. That presumes ascending thresholds, but channel 4 (N⁺,
XION4(1) = 28.0 eV, line 69166) comes before channels 5 (H⁺, 23.0 eV)
and 6 (H2⁺, 26.0 eV): from 23 to 28 eV the test of channel 4 skips both.
Fix: channel 4 jumps to the H⁺ section (label 55); the later channels
all start higher. A scan of all gas routines for such chains (a
threshold below an earlier one, same jump target) finds only this one
and the nitrogen K-shell of GAS49, which is not used at all (Q-04).
The two channels are small below 28 eV (H⁺ 6.3·10⁻¹⁹ cm² at 27.5 eV):
pure NH3, 20 °C, 760 Torr, 8·10⁷ collisions gives identical output at
30 kV/cm and agrees within errors at 100 kV/cm (χ²/n = 0.12 over 18
quantities). Magboltz++ tests each channel on its own table.

## Inconsistencies left unchanged

- When the energy loss exceeds the energy (`E.LT.EI`) just before the
  scattering angle is computed, MONTEFT, MONTEFD, MONTEFTG and MONTEFTH
  set `EI=0.0D0`, while MONTEFTA has that statement commented out and
  sets `EI=E` (line 17666). This looks like a revision applied to one
  routine only; which one is intended is for the author to say. The
  thermal versions differ again: MONTEFTT sets `EI=EOK-0.0001D0`,
  MONTEFDT `EI=0.0D0`, MONTEFTAT, MONTEFTGT and MONTEFTHT have no such
  test (ARG1 is floored at SMALL instead).
- In the thermal avalanche routines the ionisation secondary gets its
  energy and direction in the rest frame of the molecule hit and is put on
  the stack without the transformation back to the lab frame that the
  primary gets. The error is of order v_gas/v_electron (about 1e-3).
- MONTEFDT alone renormalises the direction at the end of the flight
  through its z component, `DCZ2=±SQRT(1-DCX2**2-DCY2**2)`, before
  computing the velocity relative to the gas; the other routines use the
  direction as it comes out of the flight formulas. Only rounding differs.
- A Penning electron starts in the direction the exciting electron had at
  the start of its flight, not the direction after the collision.
- FORMAT widths differ between sibling routines (`I5`/`I4`, `F9.5`/`F9.4`).
- The relative errors of the TOF results are half the difference between
  two planes, except in TOFG for a growing avalanche (the full
  difference).
- For the cut angular distribution (INDEX=1) MONTE draws R31 before R3,
  the other 17 MONTE routines and the ELIMITs draw R3 first. Both are
  uniform random numbers, so only the random stream differs.
- Only MONTE and MONTET (B=0) stop with "ENERGY OUT OF RANGE" when more
  than 1000·J1 collisions fall into the last energy bin; with a magnetic
  field the run goes on with an energy range that is too small.
- The ELIMIT routines have no moderation catch (MB-38): there a level with
  EIN = 0.024999 eV loses 0.025 eV, so the search for EFINAL sees hotter
  electrons than MONTE and may choose a larger energy range. Harmless.
- B ∥ E at BTHETA = −180°: ELIMIT tests `DABS(BTHETA).EQ.180` and runs
  ELIMIT (B = 0), MONTE tests `BTHETA.EQ.180` and runs MONTEC (any angle)
  instead of MONTEA. Both give the B ∥ E motion; only the rounding differs.

- Gas routines: thresholds tested with `.LT.` in some places, `.LE.` in
  others (GAS20, GAS54 NIN cut; GAS30 PEQION; GAS61 ionisation; GAS25
  level 58), which differs only when EN equals the threshold exactly; N2
  (GAS16) leaves QION(9), QION(10) at 0 at exactly EN = EION(10) and
  QION(10) at exactly 120 eV.
- Gas routines compute some quantities nobody reads: bremsstrahlung
  levels beyond NIN (GAS44, GAS45 above 1 keV with EIN = 0, GAS60, GAS61),
  QIONC/QIONG in GAS45, QELA in GAS54. GAS44 sets no NAME for NANISO=1
  and uses DEN(1) for DEN(I) in its Born-Bethe term (DEN is 0). These and
  the totals Q(1) (see QUESTIONS.md Q-13) have no effect.

## Not defects

- With NSCALE reduced (reproduce.sh divides it by 10), a run with the long
  decorrelation length NCOLM=2000000 has no decorrelated pairs yet in
  segments 3–5. MONTEB/MONTEBT then divide 0/0 in those segments'
  diffusion estimates and print `NaN%` errors (e.g. the fixed run of
  MB-37), and MONTEC/MONTECT, which lack the `ID.NE.0` test, subtract
  positions not yet stored. With NSCALE=4·10⁷ every segment has at least
  4·10⁶ collisions, so this cannot happen.
- `NaN%` errors and log(0) in the SST analysis when all electrons attach
  (e.g. pure C4F7N at 1 kV/cm), or zero diffusion in very short runs: these
  are numerical consequences of the input, not of the code.
- The ten avalanche routines compute `EAVAUG=EC0(I)/DFLOAT(NAUG)`
  (MONTEF*T: `EC0(KGAS,I)`) for every ionisation level above 30 eV before
  the loop over its NAUG Auger electrons (e.g. line 15034 in MONTEFD,
  6496 in MONTEFDT). For a level without Auger emission (NC0 = EC0 = 0,
  e.g. SF6) this is 0/0, but the loop is empty and the NaN unused. It shows
  only as gfortran's `IEEE_INVALID_FLAG` note at the end of the run, or as
  a stop under `-ffpe-trap=invalid` (pure SF6, thermal, 95 kV/cm, with
  MB-41..43 fixed), so a trap build cannot be used on such decks.
- GAS30 SF6 normalises the ground-state population APOPGS and then
  resets it to 1.0; the comment says this is meant ("renormalise ground
  state to allow for excitation x-sec from excited vibrational state").
- GAS55 H2S subtracts the rotations QIN(1..4) from Q(2): the elastic table
  is "elastic + effective rotation" (comment at its DATA).
- GAS31 NH3: the harmonics (level 33) are not tested on EIN(33); the
  resonance table they use starts at 4.5 eV, above it. Rotations and their
  angular distributions are switched off above 1 keV in NH3 (and other
  gases), by design.
- The four non-comment lines longer than 72 columns (93915–93960) carry
  only trailing spaces beyond column 72.
