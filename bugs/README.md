# Defects found in Magboltz 11.21

Source: `magboltz-11.21.f` (S. Biagi; the program prints `VERSION 11.20`),
branch `master` of this repository. Line numbers below refer to that file.
Branch `fixes` has one commit per defect (`MB-01` … `MB-29`); every change,
except the 281 loop starts of MB-10, carries a `C NIMBOLTZ FIX MB-nn:` comment.

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

Affected gases (cross sections or angular distributions): Xe (7), propane
(10), isobutane (11, diagnostic only), H2O (14), O2 (15), N2O (18,
diagnostic), ethene (19), H2 (21), D2 (22), CO (23), methylal (24), DME (25,
diagnostic), C2F6 (29), SF6 (30), methanol (34), C2H2F4 (43), TMA (44),
n-propanol (46), para-H2 (47), ortho-D2 (48), C4F7N (49), SiH4 (60), CCl4
(61), ethane (9), plus the ≈30 gases of MB-20, every B⊥E calculation (MB-05,
MB-23, MB-28) and every high-field calculation with a magnetic field not
parallel to E (MB-24).

## Impact on results

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

## Inconsistencies left unchanged

- When the energy loss exceeds the energy (`E.LT.EI`) just before the
  scattering angle is computed, MONTEFT, MONTEFD, MONTEFTG and MONTEFTH
  set `EI=0.0D0`, while MONTEFTA has that statement commented out and
  sets `EI=E` (line 17666). This looks like a revision applied to one
  routine only; which one is intended is for the author to say.
- FORMAT widths differ between sibling routines (`I5`/`I4`, `F9.5`/`F9.4`).

## Not defects

- `NaN%` errors and log(0) in the SST analysis when all electrons attach
  (e.g. pure C4F7N at 1 kV/cm), or zero diffusion in very short runs: these
  are numerical consequences of the input, not of the code.
- The four non-comment lines longer than 72 columns (93915–93960) carry
  only trailing spaces beyond column 72.
