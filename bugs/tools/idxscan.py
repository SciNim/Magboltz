# Index-consistency scan of the GAS routines (review aid, prints candidates):
#  pass 1: QIN(n)/PEQIN(n) right after a test on EIN(m), m != n; a QIN(n)
#          formula that uses EIN(m) (superelastic levels using the EN+EIN of
#          their partner are skipped; the H2/D2 rotations pair n with n+7)
#  pass 2: PEQIN(n)=PEQEL(2,I-IOFFN(m)) with m != n (also in logical IFs),
#          PEQIN copied from PEQIN
#  pass 3: X..(N..) with the count of another table; a tail above the
#          table taken from another table than the interpolation
#   python3 idxscan.py magboltz.f
# Found MB-44, MB-51, MB-52 (GAS15/18/31/60), MB-53. See README.md.
import re,sys
src=open(sys.argv[1]).read().split('\n')
def stmts(lines):   # join continuation lines; yield (lineno, text) of statements
    cur=None
    for n,l in enumerate(lines,1):
        if not l or l[0] in 'Cc*!': continue
        if len(l)>5 and l[5] not in ' 0' and cur: cur[1]+=l[6:72].strip(); continue
        if cur: yield cur
        cur=[n,l[:72]]
    if cur: yield cur
gas=None; out=[]; prev=None
for n,s in stmts(src):
    m=re.match(r'^      SUBROUTINE (\w+)',s)
    if m: gas=m.group(1); prev=None; continue
    if not gas or not re.match(r'GAS\d+$',gas): continue
    t=s[6:].replace(' ','')
    if t.startswith('IF(EN') and not t.startswith('IF(ENRT'):
        prev=(n,t); continue
    mq=re.match(r'QIN\((\d+),I\)=',t)
    mp=re.match(r'PEQIN\((\d+),I\)=PEQEL\(2,\(?I-IOFFN\((\d+)\)',t)
    if mp and mp.group(1)!=mp.group(2):
        out.append((gas,n,'PEQIN(%s) copies with IOFFN(%s)'%mp.groups(),t))
    lvl=(mq or mp) and (mq or mp).group(1)
    if lvl and prev and prev[0]>=n-3 and not t.endswith('=0.0'):
        g=re.findall(r'EIN\((\d+)\)',prev[1])
        if g and lvl not in g:
            out.append((gas,n,'QIN/PEQIN(%s) gated on EIN(%s)'%(lvl,','.join(g)),prev[1]+' | '+t))
    if mq:
        ks=set(re.findall(r'EIN\((\d+)\)',t))
        superel=ks=={str(int(lvl)+1)} and ('EN+EIN(%d)'%(int(lvl)+1)) in t
        if ks and ks!={lvl} and not superel:
            out.append((gas,n,'QIN(%s) formula uses EIN(%s)'%(lvl,','.join(sorted(ks))),t))
    prev=None if not t.startswith('IF(') else prev
for o in out: print('%-6s %6d  %-40s %s'%(o[0],o[1],o[2],o[3][:150]))
# second pass: anywhere in a statement (logical IF forms), and PEQIN copied from PEQIN
print('--- pass 2')
gas=None
for n,s in stmts(src):
    m=re.match(r'^      SUBROUTINE (\w+)',s)
    if m: gas=m.group(1); continue
    if not gas or not re.match(r'GAS\d+$',gas): continue
    t=s[6:].replace(' ','')
    for a,b in re.findall(r'PEQIN\((\d+),I\)=PEQEL\(2,\(?I-IOFFN\((\d+)\)',t):
        g=re.findall(r'^IF\(.*?EIN\((\d+)\)',t)
        if a!=b or (g and g[0]!=a): print('%-6s %6d  PEQIN(%s)/IOFFN(%s)/gate %s  %s'%(gas,n,a,b,g,t[:120]))
    if re.search(r'PEQIN\(\d+,I\)=PEQIN\(',t): print('%-6s %6d  PEQIN from PEQIN  %s'%(gas,n,t[:120]))
print('--- pass 3: table end index of another table / tail from another table')
gas=None; interp={}
for n,s in stmts(src):
    m=re.match(r'^      SUBROUTINE (\w+)',s)
    if m: gas=m.group(1); interp={}; ya=None; continue
    if not gas or not re.match(r'GAS\d+$',gas): continue
    t=s[6:].replace(' ','')
    for arr,cnt in re.findall(r'\b([XY][A-Z]*\d+[A-Z]*)\(N([A-Z]*\d+[A-Z]*)\)',t):
        da=re.findall(r'\d+',arr); dc=re.findall(r'\d+',cnt)
        if da and dc and da!=dc: print('%-6s %6d  %s(N%s)  %s'%(gas,n,arr,cnt,t[:110]))
    m=re.match(r'^\d*A=\(([A-Z0-9]+)\(J\)-',s[1:].replace(' ','')) or re.match(r'A=\(([A-Z0-9]+)\(J\)-',t)
    if m: ya=m.group(1)
    mq=re.match(r'(?:\d+)?QIN\((\d+),I\)=.*?\b(Y[A-Z0-9]+)\(N',t)
    if re.match(r'QIN\((\d+),I\)=\(?A\*',t) and ya:
        k=re.match(r'QIN\((\d+),I\)',t).group(1); interp[k]=ya; ya=None
    if mq and mq.group(1) in interp and interp[mq.group(1)]!=mq.group(2):
        print('%-6s %6d  QIN(%s) table %s, tail %s  %s'%(gas,n,mq.group(1),interp[mq.group(1)],mq.group(2),t[:100]))
