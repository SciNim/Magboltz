# Sibling diff: for pairs of near-duplicate routines, align their statements
# and report statement pairs that differ by one or two tokens, where the
# substitution is rare within that routine pair (a consistent rename such as
# DCX2 -> DXCOM occurs many times and is not reported).
#   python3 -I sibdiff.py magboltz.f [minratio]
import re, sys, difflib, collections, itertools
src = open(sys.argv[1]).read().split('\n')
minratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.85

# statements per routine: join continuation lines, drop comments, uppercase, no blanks
units = {}; cur = None; stmts = []
for no, l in enumerate(src, 1):
    if not l or l[0] in 'Cc*': continue
    l = l[:72].ljust(6)
    m = re.match(r'^      (SUBROUTINE|FUNCTION|PROGRAM) +([A-Z0-9_]+)', l)
    if m:
        if cur: units[cur] = stmts
        cur = m.group(2); stmts = []
    if cur is None: continue
    if l[5] not in ' 0' and stmts:
        stmts[-1][1] += l[6:].replace(' ', '')
    else:
        stmts.append([no, l[6:].replace(' ', ''), l[:5].strip()])
if cur: units[cur] = stmts

tok = re.compile(r"[A-Z][A-Z0-9_]*|\d+\.?\d*(?:[ED][+-]?\d+)?|\.\w+\.|\*\*|'[^']*'|\S")
def toks(s): return tok.findall(s)

names = [n for n in units if len(units[n]) > 40]
sigs = {n: [s[1] for s in units[n]] for n in names}
pairs = []
for a, b in itertools.combinations(names, 2):
    la, lb = len(sigs[a]), len(sigs[b])
    if min(la, lb) / max(la, lb) < 0.6: continue
    sm = difflib.SequenceMatcher(None, sigs[a], sigs[b], autojunk=False)
    if sm.quick_ratio() < minratio or sm.ratio() < minratio: continue
    pairs.append((a, b, sm))

for a, b, sm in pairs:
    subs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != 'replace' or i2 - i1 != j2 - j1: continue
        for i, j in zip(range(i1, i2), range(j1, j2)):
            ta, tb = toks(sigs[a][i]), toks(sigs[b][j])
            if len(ta) != len(tb): continue
            d = [(x, y) for x, y in zip(ta, tb) if x != y]
            if 1 <= len(d) <= 2: subs.append((i, j, tuple(d)))
    cnt = collections.Counter(x for s in subs for x in s[2])
    for i, j, d in subs:
        if all(cnt[x] <= 1 for x in d):
            print(f"{a}:{units[a][i][0]} vs {b}:{units[b][j][0]}  " +
                  ", ".join(f"{x}->{y}" for x, y in d))
            print(f"    {sigs[a][i][:110]}\n    {sigs[b][j][:110]}")
print(f"# {len(pairs)} routine pairs with similarity >= {minratio}", file=sys.stderr)
