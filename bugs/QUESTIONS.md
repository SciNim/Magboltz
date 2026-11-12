# Open questions about Magboltz 11.21 (for the author)

Things found while porting the gas routines (and the rest of the program)
where the code looks inconsistent but the intended behaviour cannot be
read off the code. Nothing here is changed in branch `fixes` or in the Nim
port; both reproduce upstream. Line numbers refer to `magboltz-11.21.f` on
branch `master`. Clear defects are in `README.md` (MB-01 … MB-61).

Each entry: what the code does, the possible readings, and what would
change. Mark an entry when answered and move it to README.md if it turns
out to be a defect.

## Values that disagree with their own description

Q-01. **GAS30 SF6, level 23** (line 68020): the comment (68016) and the
description SCRPT(46) (67343) say `F=0.1211`, the code uses
`DIP(0.01211, ...)`. A factor of 10 in a singlet dissociation at 14.5 eV.
Which one is right?

Q-02. **Descriptions vs. code** (only the printed level list is affected
if the code is right):
- GAS1 CF4 level 46: code F=0.00198, description F=0.00189.
- GAS8 CH4 level 33: EIN=20.5, description ELOSS=20.25.
- GAS19 C2H4: H+ channel described with ELOSS=18.46, EION=18.66.
- GAS46 n-propanol: SCRPT(111) ELOSS=13.25, EIN(75)=13.35 (also the
  comment). Its triplet table XTRP4(4)=18.8 where isopropanol (GAS36,
  otherwise identical) has 17.8.
- GAS49 C4F7N: SCRPT(4) double ionisation ELOSS=35.0, EION(2)=38.0.
- GAS61 CCl4: SCRPT(3) CCl3+ ELOSS=13.35, EION(1)=11.35.
- GAS52 C3F8: SCRPT(2) says "CARBON HEXAFLUORIDE" (C3F8 is
  octafluoropropane); GAS38 F2 "FLOURINE", GAS55 H2S "EL0SS" (spelling).

## Physics choices that may or may not be intended

Q-03. **GAS49 C4F7N fitted with which mass?** MB-47 changes the molecular
mass from 114.0416 (C3F4H2, copied from GAS45) to 195.0383. If the 2025
cross-section set was adjusted to swarm data with the wrong mass, the
elastic cross section was fitted to compensate, and the fix makes the
set disagree with that data. Was it fitted with Magboltz as it was?

Q-04. **GAS49 C4F7N, further copies from GAS45?**
- E(3)=11.0 (the ionisation energy of C3F4H2) while EION(1)=12.7. E(3)
  enters the denominator EN+EIN+E(3) of every Born dipole level.
- The nitrogen K-shell is computed into QION(5)/EION(5) but NION=4, so
  it is never used, nor subtracted by CRFAC, and it is set only above the
  fluorine K-edge (685.4 eV). Should NION be 5?

Q-05. **GAS29 C2F6, QION(5) (C2F4+)**: share of the counting ionisation
0.0045 for 900 eV … 3 keV (line 65939), 0.00045 in the Born-Bethe branch
above 3 keV (66032). The ionisation fractions jump by 10 at 3 keV.

Q-06. **GAS52 C3F8 K-shells**: QION(8) (C) and QION(9) (F) are neither
subtracted from the other channels (C2F6 and C2H2F4 do it with CRFAC) nor
multiplied by the number of atoms (C2F6: ×2 C, ×6 F; C2H2F4: ×2, ×4).
Are the C3F8 tables already per molecule, and is the double counting
intended?

Q-07. **GAS29 C2F6, anisotropy of the vibrations above 20 eV**: the
copy `PEQIN(1..14,I)=PEQEL(2,...)` sits inside the VHIGH (level 14)
branch, which ends at XVIBR(NVIBR)=12.5 eV, so it never runs. In GAS43
(after MB-04) the same block applies above 20 eV. Was it meant to?

Q-08. **GAS39 CS2 three-body attachment**: QATT(1) is a 3-body cross
section "normalised at 40 Torr" (comments, SCRPT(4)), multiplied by a
fixed 1.3 and not by TORR/TEMPC, unlike O2, NO and the newer gases.
Is the 40-Torr value meant for all pressures? What is the factor 1.3?

Q-09. **GAS41 CD4**: EOBY(1)=7.3 (fixed) while E(3)=EION=12.99. CH4 uses
EOBY=0.475·EION=6.0, BF3 EOBY=EION. Intended?

Q-10. **GAS1 CF4 superelastic tails** (V4, V1, V3; lines 19051, 19097,
19137): above the table
`QIN=Y(N)*(X(N)/(EN*(EN-EIN)))**2`, i.e. Y·X²/(E²E′²), 1/(50·E) of a
tail that would match the table branch (detailed balance,
(E′/E)·Y·(X/E′)³ with the inelastic tail Y·(X/E)³). The values are tiny
in both forms (above 50 eV, times the thermal population), so the choice
changes nothing measurable; which form was intended?

Q-11. **GAS45 C3F4H2 Penning**: `DO 61 K=61,NIN` with NIN=29: no level
ever gets a Penning fraction. Copied from a gas with more levels? Which
levels should transfer?

Q-12. **GAS54 Hg2**: the density factor of the two-body attachment takes
GFRAC from the last mixture slot with NGASN=54, so a mixture with Hg2 in
two slots counts only one. QELA (XEL/YEL table) is computed in every bin
and never used. Intended?

Q-13. **Total and diagnostic sums** (no effect on transport): Q(1) is not
set in GAS29, 35, 43, 45, 49, 52 and others; Q(4)=0 after the attachment
in GAS30 and GAS53 (the attachment is only in QATT, which MIXER reads);
GAS14 SUMTRP adds QIN(230) (a dipole) instead of QIN(241); GAS25 Q(1)
leaves out the excitations 61-110. MIXER sums Q(1) into QTOT, which no
routine reads. Should Q(1) always be the total?

Q-14. **GAS51 CF3Br level 5**: 11.19 has `EIN(5)=0.1499`, `SCRPT(11)=' VIB3
ELOSS= 0.1499 '`; 11.20/11.21 have `EIN(5)=0.024999` (line 94468) with
the same label, so the level is now a moderation level (the electron keeps
0.024999 eV), while GAS45 and GAS49 label theirs `VIB MODERATION`. The
formula of the cross section (0.750 × Born dipole factor of EIN(5)) is
unchanged, so the level now also has the dipole cross section of a
0.025 eV transition (threshold, magnitude). Is level
5 meant to be a moderation level, or is 0.024999 a stand-in for the VIB3
energy? Magboltz++ keeps 0.1499. The choice matters: Ar/CF3Br 90/10,
1 kV/cm, 20 °C, thermal, 4·10⁷ collisions: drift 64.09 µm/ns and mean
energy 0.107 eV with 0.024999 (Fortran 11.21, and Magboltz++ patched to
0.024999), 53.10 µm/ns and 0.888 eV with 0.1499 (Magboltz++).

Q-15. **GAS24 methylal above 1 keV**: every table (elastic, ionisation,
three vibrations, two excitations) ends at 1000 eV, and the search loops
extrapolate their last interval without an upper end test (from line
62393 on). The vibrations become negative just above 1 keV
(−1.1·10⁻²¹ cm²), the elastic cross section at 1.2 keV, the total at
1.8 keV (−1.4·10⁻¹⁵ cm² at 4 keV). Other gases continue their tables
with 1/E, 1/E² or Born-Bethe tails; Magboltz++ sets 0 above the tables.
Which continuation is intended? (Reached only with EFINAL > 1 keV.)
