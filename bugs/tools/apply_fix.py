# apply one NimBoltz fix (by id) to magboltz-11.21.f; asserts every edit matches exactly
#   python3 apply_fix.py MB-nn [magboltz-11.21.f]
import re,sys,os
F=sys.argv[2] if len(sys.argv)>2 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','magboltz-11.21.f')
L=open(F).read().split('\n')
def body(r):
    s=next(i for i,l in enumerate(L) if re.match(r'^      SUBROUTINE %s *(\(|$)'%r,l))
    e=next(i for i in range(s+1,len(L)) if re.match(r'^      SUBROUTINE ',L[i]))
    return s,e
def edit(r,old,new,comment,count=1):
    """replace lines equal to old (rstrip) inside routine r by list new, prefixed by comment lines"""
    global L
    s,e=body(r)
    idx=[i for i in range(s,e) if L[i].rstrip()==old.rstrip()]
    assert len(idx)==count,(r,old,len(idx))
    for i in reversed(idx):
        import textwrap
        txt=' '.join(comment)
        w=textwrap.wrap(txt,72-16)
        c=['C NIMBOLTZ FIX '+w[0]]+['C               '+x for x in w[1:]]
        c=[x[:72] for x in c]
        for x in c+new: assert len(x)<=72,x
        L[i:i+1]=c+new
fx=sys.argv[1]
if fx=='MB-01':
    for g in ('GAS22','GAS48'):
        edit(g,'  424 IF(EN.GT.8.0) GO TO 425',['  424 IF(EN.LT.8.0) GO TO 425'],
             ['MB-01: WAS EN.GT.8.0 (INVERTED; ALL OTHER SUPERELASTIC LEVELS','HERE AND IN GAS21/GAS47 USE EN.LT.8.0)'])
        edit(g,' 1429 IF(EN.GT.8.0) GO TO 430',[' 1429 IF(EN.LT.8.0) GO TO 430'],
             ['MB-01: WAS EN.GT.8.0 (INVERTED, SEE ABOVE)'])
elif fx=='MB-02':
    edit('GAS24','      IF(EN.LE.XEXC(J)) GO TO 620',['      IF(EN.LE.XEXC1(J)) GO TO 620'],
         ['MB-02: SEARCH THE XEXC1 GRID THAT IS INTERPOLATED BELOW (WAS XEXC)'])
elif fx=='MB-03':
    for n in (13,14):
        old='      PEQIN(%d,I)=1.0-ESPRES'%n
        s,e=body('GAS29'); i=[k for k in range(s,e) if L[k].rstrip()==old.rstrip() or L[k].strip()==old.strip()]
        assert len(i)==1,(old,i)
        L[i[0]]=L[i[0]].rstrip()
        edit('GAS29',L[i[0]],['      PEQIN(%d,I)=1.0-EPSRES'%n],
             ['MB-03: WAS ESPRES (UNDEFINED, TYPO OF EPSRES SET ABOVE)'])
elif fx=='MB-04':
    edit('GAS43','       DO 420 L=9',['       DO 420 L=1,9'],
         ['MB-04: WAS "DO 420 L=9" = ASSIGNMENT DO420L=9, NOT A LOOP'])
elif fx=='MB-05':
    edit('MONTEBT','      IMBTP=0',['      IMBPT=0'],
         ['MB-05: WAS IMBTP=0 (TYPO), LEAVING IMBPT UNDEFINED'])
elif fx=='MB-06':
    edit('GAS44','       Q(2,I)=YELM(2)*1.D-16',['       Q(2,I)=YELM(2)*1.D-16','       PQ1=0.5','       PQ2=0.0'],
         ['MB-06: PQ1,PQ2 WERE UNDEFINED HERE; ISOTROPIC = VALUES AT XEN(2)'])
elif fx=='MB-07':
    edit('GAS14','      PEQIN(211,I)=PEQEL(2,(I-IOFFN(211)))',
         ['      IF(EN.GT.DABS(EIN(211))) PEQIN(211,I)=PEQEL(2,(I-IOFFN(211)))'],
         ['MB-07: SUPERELASTIC HAS NO THRESHOLD, I-IOFFN<1 FOR EN<=|EIN|'])
    edit('GAS34','      PEQIN(53,I)=PEQEL(2,(I-IOFFN(53)))',
         ['      IF(EN.GT.DABS(EIN(53))) PEQIN(53,I)=PEQEL(2,(I-IOFFN(53)))'],
         ['MB-07: SUPERELASTIC HAS NO THRESHOLD, I-IOFFN<1 FOR EN<=|EIN|'])
elif fx=='MB-08':
    edit('GAS10','      NIONG=46',['      NIONG=45'],['MB-08: WAS 46, XION/YIONG/YIONC HAVE 45 ENTRIES'])
    s,e=body('GAS10')
    i=[k for k in range(s,e) if L[k].rstrip()=='   41 CONTINUE']; assert len(i)==1
    assert L[i[0]+1].rstrip()=='      J=NION'
    L[i[0]+1:i[0]+2]=['C NIMBOLTZ FIX MB-08: WAS J=NION (UNREACHABLE)','      J=NIONG']
elif fx=='MB-09':
    s,e=body('GAS46')
    i=[k for k in range(s,e) if L[k].rstrip()=='      DO 830 K=1,NION']; assert len(i)==1
    assert L[i[0]+1].rstrip()=='  830 SUMION=SUMION+QION(K,I)'
    L[i[0]:i[0]+2]=['C NIMBOLTZ FIX MB-09: STRAY DEBUG SUM OUTSIDE THE ENERGY',
                    'C               LOOP (READS QION(K,4001)); COMMENTED OUT AS IN GAS34','C     DO 830 K=1,NION','C 830 SUMION=SUMION+QION(K,I)']
elif fx=='MB-10':
    import subprocess
    out=subprocess.run(['python3','-I','/tmp/ub/scan_jm1.py',F],capture_output=True,text=True).stdout.split('\n')
    lines=[int(x.split()[1]) for x in out if x.strip()]
    for ln in lines:
        old=L[ln-1]
        new=re.sub(r'^([ 0-9]{5}.\s*DO\s*\d+\s*[A-Z]\w*\s*=\s*)1(\s*,)',r'\g<1>2\2',old)
        assert new!=old,(ln,old)
        L[ln-1]=new
    print('MB-10 loops changed:',len(lines))
elif fx=='MB-11':
    edit('GAS43','       QELA=YEL(1)*1.D-16',['       QELA=YEL(1)*1.D-16','       EPSIL=1.0-YEPS(1)'],
         ['MB-11: EPSIL WAS UNDEFINED BELOW XEL(1); USE TABLE VALUE AT XEL(1)'])
elif fx=='MB-12':
    edit('GAS7','      IF(EN.LE.EION(2)) GO TO 3350',['      IF(EN.LE.EION(2)) GO TO 3250'],
         ['MB-12: WAS GO TO 3350, SKIPPING QION(3,I)=0 AND Q456=0;',
          'EVERY OTHER CHARGE STATE JUMPS TO THE NEXT SECTION'])
elif fx=='MB-13':
    for g in ('GAS21','GAS22','GAS47','GAS48'):
        s_,e_=body(g); i=[k for k in range(s_,e_) if L[k].strip()=='PEQEL(2,I)=0.5+(QELA-QMOM)/QELA' and L[k][:1]==' ']
        assert len(i)==1,(g,i)
        ind=L[i[0]][:len(L[i[0]])-len(L[i[0]].lstrip())]
        L[i[0]:i[0]+1]=['C NIMBOLTZ FIX MB-13: WAS QMOM (UNDEFINED); THE MOMENTUM-TRANSFER',
                        'C               CROSS SECTION IS COMPUTED AS QELM ABOVE',
                        ind+'PEQEL(2,I)=0.5+(QELA-QELM)/QELA']
elif fx=='MB-14':
    for g in ('GAS22','GAS48'):
        edit(g,'      IF(NANISO.EQ.O) THEN',['      IF(NANISO.EQ.0) THEN'],
             ['MB-14: WAS NANISO.EQ.O (LETTER O, AN UNDEFINED REAL)'])
elif fx=='MB-15':
    edit('GAS49','      IF(EN.LT.XATT5(1)) GO TO 250',['      GO TO 250','      IF(EN.LT.XATT5(1)) GO TO 250'],
         ['MB-15: XATT5/YATT5 HAVE NO DATA STATEMENT (UNDEFINED);',
          'NO 3-BODY ATTACHMENT UNTIL THE TABLE IS SUPPLIED'])
elif fx=='MB-16':
    # GAS11: total uses QEXCTOT, computed as QTOTEXC
    s_,e_=body('GAS11')
    i=[k for k in range(s_,e_) if L[k].rstrip()=='     /QIN(5,I)+QIN(6,I)+QIN(7,I)+QIN(8,I)+QIN(9,I)+QEXCTOT']; assert len(i)==1
    L[i[0]]='     /QIN(5,I)+QIN(6,I)+QIN(7,I)+QIN(8,I)+QIN(9,I)+QTOTEXC'
    assert L[i[0]-1].startswith('      Q(1,I)=')
    L[i[0]-1:i[0]-1]=['C NIMBOLTZ FIX MB-16: QEXCTOT (UNDEFINED) -> QTOTEXC COMPUTED ABOVE']
    # GAS15: QRSUM never zeroed
    edit('GAS15','      DO 312 K=25,48',['      QRSUM=0.0','      DO 312 K=25,48'],['MB-16: QRSUM WAS NEVER INITIALISED'])
    # GAS18: XSECDUM(61..120) not set on all paths
    edit('GAS18','      DO 130 L=1,60',['      DO 129 L=1,120','  129 XSECDUM(L)=0.0','      DO 130 L=1,60'],
         ['MB-16: XSECDUM NOT SET ON ALL PATHS; ZERO IT PER ENERGY AS IN GAS19'])
    # GAS23: Q(3,I)=QCOUNT, computed as QIONC
    edit('GAS23','      Q(3,I)=QCOUNT',['      Q(3,I)=QIONC'],['MB-16: WAS QCOUNT (UNDEFINED); COUNTING IONISATION IS QIONC'])
    # GAS25: SUMATT commented out but used
    s_,e_=body('GAS25')
    for t in ('C     SUMATT=0.0','C     DO 820 K=1,1','C 820 SUMATT=SUMATT+QATT(K,I)'):
        i=[k for k in range(s_,e_) if L[k].rstrip()==t]; assert len(i)==1,t
        L[i[0]]=' '+L[i[0]][1:]
    k0=[k for k in range(s_,e_) if L[k].rstrip()=='      SUMATT=0.0'][0]
    L[k0:k0]=['C NIMBOLTZ FIX MB-16: SUMATT LOOP WAS COMMENTED OUT BUT SUMATT USED']
    # GAS34: whole sum block commented out but SUMINEL used
    s_,e_=body('GAS34')
    a=[k for k in range(s_,e_) if L[k].rstrip()=='C     SUMR=0.0']; b=[k for k in range(s_,e_) if L[k].rstrip()=='C     SUMINEL=SUMR+SUMSUPR+SUMVIB+SUMATT+SUMION']
    assert len(a)==1 and len(b)==1 and a[0]<b[0]
    n=0
    for k in range(a[0],b[0]+1):
        if re.match(r'^C     \S|^C \d{3} ',L[k]): L[k]=' '+L[k][1:]; n+=1
    assert n==20,n
    L[a[0]:a[0]]=['C NIMBOLTZ FIX MB-16: SUM BLOCK WAS COMMENTED OUT BUT SUMINEL USED']
elif fx=='MB-17':
    edit('GAS30','      PEQIN(2,I)=0.0',['      PEQIN(22,I)=0.0'],
         ['MB-17: WAS PEQIN(2,I)=0.0 (TYPO): LEFT PEQIN(22) UNDEFINED AND',
          'RESET THE V4 DIPOLE ANISOTROPY PEQIN(2) TO 0 = ALWAYS BACKWARD'])
elif fx=='MB-18':
    edit('GAS23','  559 PEQIN(146,I)=PEQEL(1,(I-IOFFN(146)))',['  559 PEQIN(146,I)=PEQEL(2,(I-IOFFN(146)))'],
         ['MB-18: WAS PEQEL(1,...) (UNDEFINED ROW); ALL OTHER LEVELS USE PEQEL(2)'])
elif fx=='MB-19':
    edit('GAS15','      DO 21 L=1,3',['      DO 21 L=1,3','      PENFRA(L,K)=0.0'],
         ['MB-19: LOOP HAD NO BODY, PENFRA(1:3,1:75) WERE UNDEFINED'])
    for g in ('GAS14','GAS31','GAS34','GAS35','GAS36','GAS46'):
        edit(g,'       PENFRA(1,K)=0.0',['       PENFRA(L,K)=0.0'],
             ['MB-19: WAS PENFRA(1,K) INSIDE THE L LOOP, PENFRA(2:3,K) UNDEFINED'])
elif fx=='MB-20':
    z=['      DO 9006 I=1,4000','      DO 9001 J=1,250','      QIN(J,I)=0.0D0',' 9001 PEQIN(J,I)=0.0D0',
       '      DO 9002 J=1,30','      QION(J,I)=0.0D0',' 9002 PEQION(J,I)=0.0D0',
       '      DO 9003 J=1,6','      Q(J,I)=0.0D0',' 9003 PEQEL(J,I)=0.0D0',
       '      DO 9004 J=1,8',' 9004 QATT(J,I)=0.0D0','      DO 9005 J=1,10',' 9005 QNULL(J,I)=0.0D0',
       ' 9006 CONTINUE',
       '      DO 9007 J=1,250','      EI(J)=0.0D0','      KIN(J)=0','      PENFRA(1,J)=0.0D0',
       '      PENFRA(2,J)=0.0D0',' 9007 PENFRA(3,J)=0.0D0',
       '      DO 9008 J=1,30','      EION(J)=0.0D0','      EB(J)=0.0D0','      NC0(J)=0',
       '      EC0(J)=0.0D0','      WK(J)=0.0D0','      EFL(J)=0.0D0','      NG1(J)=0',
       '      EG1(J)=0.0D0','      NG2(J)=0',' 9008 EG2(J)=0.0D0',
       '      DO 9009 J=1,6','      E(J)=0.0D0',' 9009 KEL(J)=0',
       '      DO 9010 J=1,10',' 9010 SCLN(J)=0.0D0']
    edit('GASMIX','      DIMENSION QATT(8,4000),QNULL(10,4000),SCLN(10)',
         ['      DIMENSION QATT(8,4000),QNULL(10,4000),SCLN(10)']+z,
         ['MB-20: THE GAS ROUTINES LEAVE OUTPUTS UNSET THAT THE MIXERS READ',
          '(PENFRA, AUGER DATA NC0..EG2 OF SINGLE IONISATION, EI OF',
          'BREMSSTRAHLUNG LEVELS, Q(1,*)) AND RELY ON THEM BEING ZERO.',
          'DEFINE EVERY OUTPUT AS ZERO BEFORE CALLING THE GAS ROUTINE.'])
elif fx=='MB-21':
    edit('GAS49','      NIN=29 ',['      NIN=26'],
         ['MB-21: WAS 29 (COPIED FROM GAS45); 26 LEVELS, THEN THE 3',
          'BREMSSTRAHLUNG LEVELS 27-29 (SCRPT 40-42) WHEN EFINAL>1000'])
    for a,b in ((30,27),(31,28),(32,29)):
        edit('GAS49','      QIN(%d,I)=0.0'%a,['      QIN(%d,I)=0.0'%b],['MB-21: BREMSSTRAHLUNG LEVEL %d, WAS %d'%(b,a)])
    edit('GAS49','      QIN(30,I)=DEXP(A*EN+B)*1.D-24',['      QIN(27,I)=DEXP(A*EN+B)*1.D-24'],['MB-21: WAS QIN(30,I)'])
    edit('GAS49','      QIN(31,I)=DEXP(A1*EN+B1)*4.D-24',['      QIN(28,I)=DEXP(A1*EN+B1)*4.D-24'],['MB-21: WAS QIN(31,I)'])
    edit('GAS49','      QIN(32,I)=DEXP(A2*EN+B2)*7.D-24',['      QIN(29,I)=DEXP(A2*EN+B2)*7.D-24'],['MB-21: WAS QIN(32,I)'])
elif fx=='MB-22':
    edit('GAS30','      XMT=(1.5-FWD/(FWD+BCK))*Q(2,I)',['      XMT=(1.5-FWD/(FWD+BCK))*QIN(2,I)'],
         ['MB-22: WAS *Q(2,I), THE ELASTIC CROSS SECTION; GIVES PEQIN(2)<0.',
          'WITH QIN(2,I) PEQIN(2)=FWD/(FWD+BCK) AS FOR THE DIPOLE PART',
          'ADIP OF V3 (LEVEL 6) AND IN GAS1/GAS8'])
elif fx=='MB-23':
    for r in ('MONTEB','MONTEBT'):
        edit(r,'      DFXXST(J1)=5.0D+15*(SUMXX-SXXOLD)/(ST2-ST2OLD)',
             ['      DFXXST(J1)=0.0D0',
              '      IF(ST2.NE.0.0D0) DFXXST(J1)=5.0D+15*(SUMXX-SXXOLD)/(ST2-ST2OLD)'],
             ['MB-23: ST2=ST2OLD=0 IN THE FIRST SEGMENTS GAVE 0/0, I.E. DXXER=NaN;',
              'GUARD AS IN MONTE/MONTEA'])
elif fx=='MB-24':
    edit('MONTEFTG','       DCY(NCLTMP)=DCY2*F6S+(F5S/ARGZ)*(DCX2*F9S-DCYS*DCZ2*F8S)',
         ['       DCY(NCLTMP)=DCY2*F6S+(F5S/ARGZ)*(DCX2*F9S-DCY2*DCZ2*F8S)'],
         ['MB-24: WAS DCYS (UNDEFINED SCALAR), AS IN MONTEFT/MONTEFTA: DCY2'])
    edit('MONTEFTH','       DCZ(NCLTMP)=DCZ2*F6S*ARGZ*F5S*F8S',
         ['       DCZ(NCLTMP)=DCZ2*F6S+ARGZ*F5S*F8S'],
         ['MB-24: WAS DCZ2*F6S*ARGZ*... (* FOR +), AS IN MONTEFT/MONTEFTA'])
    edit('MONTEFTH','       DCX(NCLTMP)=DCX2*F6S-(F5S/ARGZ)*(DCYS*F9S+DCX2*DCZ2*F8S)',
         ['       DCX(NCLTMP)=DCX2*F6S-(F5S/ARGZ)*(DCY2*F9S+DCX2*DCZ2*F8S)'],
         ['MB-24: WAS DCYS (UNDEFINED SCALAR), AS IN MONTEFT/MONTEFTA: DCY2'])
elif fx=='MB-25':
    for g in ('GAS9','GAS19'):
        edit(g,'      DO 780 J=2,NBRM',['      DO 780 J=2,NBREM'],
             ['MB-25: WAS NBRM (UNDEFINED); THE TABLE LENGTH IS NBREM'])
elif fx=='MB-26':
    edit('GAS23','      DO 509 J=2,N2XC5',['      DO 509 J=2,NEXC5'],
         ['MB-26: WAS N2XC5 (UNDEFINED); THE TABLE LENGTH IS NEXC5'])
elif fx=='MB-27':
    edit('GAS43','      J=NVIBR1',['      J=NVIBR'],['MB-27: WAS NVIBR1 (UNDEFINED, UNREACHABLE)'],count=2)
    edit('GAS60','      J=NNVIBR',['      J=NVIBR'],['MB-27: WAS NNVIBR (UNDEFINED, UNREACHABLE)'],count=3)
elif fx=='MB-28':
    edit('MONTEFTG','      IF(PENFRA(1,I).EQ.0.0) THEN',['      IF(PENFRA(1,I).NE.0.0) THEN'],
         ['MB-28: WAS .EQ.0.0 (INVERTED; ALL OTHER MONTE ROUTINES USE .NE.)'])
    edit('MONTEFTGT','      IF(PENFRA(KGAS,1,I).EQ.0.0) THEN',['      IF(PENFRA(KGAS,1,I).NE.0.0) THEN'],
         ['MB-28: WAS .EQ.0.0 (INVERTED; ALL OTHER MONTE ROUTINES USE .NE.)'])
elif fx=='MB-29':
    edit('ELIMITBT','      DCZ2=DMIN1(DZCOM,1.0D0)',['      DZCOM=DMIN1(DZCOM,1.0D0)'],
         ['MB-29: WAS DCZ2= (UNUSED), AS IN ELIMITT/ELIMITCT: DZCOM='])
elif fx=='MB-30':
    s,e=body('MIXER')
    idx=[i for i in range(s,e) if L[i].rstrip()=='      EFL(NP)=EFL1(KION)']
    assert len(idx)==2 and L[idx[1]-1].rstrip()=='      WKLM(NP)=WK2(KION)',idx
    L[idx[1]]='      EFL(NP)=EFL2(KION)'
    L[idx[1]:idx[1]]=['C NIMBOLTZ FIX MB-30: WAS EFL1(KION) (FLUORESCENCE ENERGY OF GAS 1)']
elif fx=='MB-31':
    s,e=body('MIXER')
    idx=[i for i in range(s,e) if L[i].rstrip()=='      IF(KIN2(J).EQ.2) THEN']
    assert len(idx)==1,idx
    i=idx[0]
    assert [x.rstrip() for x in L[i+3:i+6]]==['      ENDIF','C','      ENDIF'],L[i+3:i+6]
    del L[i+5]
    L[i:i]=['C NIMBOLTZ FIX MB-31: ENDIF MOVED UP. THE KIN2(J).EQ.2 TEST WAS',
            'C               INSIDE THE KIN2(J).EQ.1 BLOCK (UNREACHABLE), AS',
            'C               FOR THE OTHER FIVE GASES',
            '      ENDIF']
elif fx=='MB-32':
    s,e=body('MIXERT')
    for k in (1,2):
        idx=[i for i in range(s,e) if L[i].rstrip()=='       IF(KEL1(3).EQ.%d) THEN'%k]
        assert len(idx)==7,(k,idx)
        for n,i in zip((2,3,4,5,6),idx[2:]):
            assert 'PEQION%d(KION'%n in L[i+1],(n,L[i+1])
            L[i]='       IF(KEL%d(3).EQ.%d) THEN'%(n,k)
    for i in reversed([i for i in range(s,e) if re.match(r'^       IF\(KEL([2-6])\(3\)\.EQ\.1\) THEN$',L[i]) and 'PEQION' in L[i+1]]):
        L[i:i]=['C NIMBOLTZ FIX MB-32: WAS KEL1(3) (IONISATION ANISOTROPY OF GAS 1)']
elif fx=='MB-33':
    edit('MIXERT','       IARRY(KGAS,NP)=0.0',['       IARRY(KGAS,NP)=L'],
         ['MB-33: WAS 0.0; MONTE* COUNT ICOLL(KGAS,IARRY) OUT OF BOUNDS'])
elif fx=='MB-34':
    edit('MIXER','      PENFRA(2,NP)=PENFRA1(2,J)*1.D-16/DSQRT(3.0D0)',
         ['      PENFRA(2,NP)=PENFRA1(2,J)*1.D-6/DSQRT(3.0D0)'],
         ['MB-34: WAS 1.D-16. MICRONS TO METRES AS FOR GASES 2-6'])
    for n in range(1,7):
        edit('MIXERT','       PENFRA(KGAS,2,NP)=PENFRA%d(2,J)*1.D-16/DSQRT(3.0D0)'%n,
             ['       PENFRA(KGAS,2,NP)=PENFRA%d(2,J)*1.D-6/DSQRT(3.0D0)'%n],
             ['MB-34: WAS 1.D-16. MICRONS TO METRES AS IN MIXER'])
elif fx=='MB-35':
    edit('MIXER','       DO 822 KATT=1,NATT5',['       DO 822 KATT=1,NATT6'],
         ['MB-35: WAS NATT5 AND QATT(5)/QATT5 BELOW (GAS 6 ATTACHMENT)'])
    edit('MIXER','  822  QATT(5,I)=QATT(5,I)+QATT5(KATT,I)*AN6',
         ['  822  QATT(6,I)=QATT(6,I)+QATT6(KATT,I)*AN6'],['MB-35: SEE ABOVE'])
elif fx=='MB-36':
    s,e=body('MIXERT')
    i=next(k for k in range(s,e) if L[k].rstrip()=='      DO 700 IE=1,N4000')
    assert [x.rstrip() for x in L[i+1:i+4]]==['      DO 700 KGAS=1,NGAS','      FCION(IE)=0.0D0','      FCATT(IE)=0.0D0'],L[i:i+4]
    j=next(k for k in range(i,e) if L[k].rstrip()==' 700  CONTINUE')
    assert [x.rstrip() for x in L[j-3:j]]==['      FCATT(IE)=FCATT(IE)*EROOT(IE)','      FCION(IE)=FCION(IE)*EROOT(IE)','      TCF(KGAS,IE)=TCF(KGAS,IE)*EROOT(IE)'],L[j-3:j]
    L[j-3:j+1]=['      TCF(KGAS,IE)=TCF(KGAS,IE)*EROOT(IE)',' 699  CONTINUE',
                '      FCATT(IE)=FCATT(IE)*EROOT(IE)','      FCION(IE)=FCION(IE)*EROOT(IE)',' 700  CONTINUE']
    L[i+1:i+4]=['C NIMBOLTZ FIX MB-36: FCION/FCATT WERE ZEROED AND SCALED BY EROOT',
                'C               INSIDE THE KGAS LOOP, SO ONLY THE LAST GAS COUNTED',
                'C               (FRIEDLANDT). NOW SUMMED OVER ALL GASES AS IN MIXER',
                '      FCION(IE)=0.0D0','      FCATT(IE)=0.0D0','      DO 699 KGAS=1,NGAS']
elif fx=='MB-37':
    edit('MONTEBT','      DIMENSION XST(1000000),YST(1000000),ZST(1000000),STO(1000000)',
         ['      DIMENSION XST(2000000),YST(2000000),ZST(2000000),STO(2000000)'],
         ['MB-37: WAS 1000000; SETUP SETS NCOLM UP TO 2000000 (ALL OTHER','MONTE* USE 2000000)'])
elif fx=='MB-38':
    for r in ['MONTET','MONTEAT','MONTEBT','MONTECT','MONTEFTT','MONTEFDT',
              'MONTEFTGT','MONTEFTHT','MONTEFTAT']:
        edit(r,'       EI=E-0.024999',['       EI=EOK-0.024999'],
             ['MB-38: WAS E (LAB FRAME); THE INCIDENT ENERGY OF THE',
              'COLLISION IS EOK (REST FRAME OF THE GAS MOLECULE)'])
elif fx=='MB-39':
    for r in ['MONTEFTT','MONTEFDT','MONTEFTGT','MONTEFTHT','MONTEFTAT',
              'MONTEFT','MONTEFD','MONTEFTG','MONTEFTH','MONTEFTA']:
        for ind in ('        ','       '):
            edit(r,ind+'IF(PHIS.GT.F4) PHIS=PHI0-F4',[ind+'IF(PHIS.GT.F4) PHIS=PHIS-F4'],
                 ['MB-39: WAS PHI0-F4, WHICH GIVES THE SECONDARY THE AZIMUTH OF',
                  'THE PRIMARY (PHIS-F4 IS PHI0-API, THE OPPOSITE AZIMUTH)'])
elif fx=='MB-40':
    edit('TOFG','      ATTOINT=FRATT/FRION',['      IF(FRION.GT.0.0D0) ATTOINT=FRATT/FRION'],
         ['MB-40: WITHOUT IONISATION FRATT/FRION IS INFINITE (NAN IN THE',
          'RESULTS); KEEP ATTOINT=-1 FROM MONTEFTG, HANDLED BELOW'])
elif fx=='MB-41':
    edit('ALPCALCT','      ALPHAST=0.85D0*DABS(ALPHA-ATT)',
         ['      ALPHAST=0.85D0*DABS(ALPHA-ATT)',
          '      CORR=760.0*(TEMPC+273.15)/(TORR*293.15)',
          '      IF(ALPHA.GT.(10.0*ALPHAST).OR.ATT.GT.(10.0*ALPHAST)) THEN',
          '       IF(ALPHA.GT.100.0*CORR) THEN',
          '        ALPHAST=ALPHAST*30.0',
          '       ELSE IF(ALPHA.GT.50.0*CORR) THEN',
          '        ALPHAST=ALPHAST*15.0',
          '       ELSE',
          '        ALPHAST=ALPHAST*8.0',
          '       ENDIF',
          '      ENDIF'],
         ['MB-41: THE REDUCED PLANE SPACING FOR ALPHA CLOSE TO ATT, ADDED',
          'IN 11.12 TO ALPCALC AND THE SIX ALPCLC* ROUTINES, WAS MISSING HERE'])
elif fx=='MB-42':
    pc=['MB-42: /CTWNER/ HOLDS PERCENT (MONTE*, ALPCALC, ALPCALCT,',
        'GARFIELD++); WAS RALPER*ALPHA/100., AN ABSOLUTE ERROR']
    ac=['MB-42: /CTWNER/ HOLDS PERCENT (MONTE*, ALPCALC, ALPCALCT,',
        'GARFIELD++); WAS RATOFER*ATT/100., AN ABSOLUTE ERROR']
    for r in ('ALPCLCA','ALPCLCAT','ALPCLCC','ALPCLCCT'):
        edit(r,'      ALPER=RALPER*ALPHA/100.',['      ALPER=RALPER'],pc)
        edit(r,'      ATTER=RATOFER*ATT/100.',['      ATTER=RATOFER'],ac)
    edit('ALPCLCBT','      ALPER=RALPER*ALPHA/100.',['      ALPER=RALPER'],pc)
    edit('ALPCLCBT','      ATTER=RATOFER*ATT*100.',['      ATTER=RATOFER'],
         ['MB-42: /CTWNER/ HOLDS PERCENT (MONTE*, ALPCALC, ALPCALCT,',
          'GARFIELD++); WAS RATOFER*ATT*100.'])
    edit('ALPCLCB','      ALP1ER=RALPER*ALPHA/100.',['      ALPER=RALPER'],
         ['MB-42: WAS ALP1ER=RALPER*ALPHA/100., A LOCAL NEVER READ, SO',
          '/CTWNER/ KEPT THE ERRORS OF MONTEB; /CTWNER/ HOLDS PERCENT'])
    edit('ALPCLCB','      ATT1ET=RATOFER*ATT/100.',['      ATTER=RATOFER'],
         ['MB-42: WAS ATT1ET=RATOFER*ATT/100., A LOCAL (SEE ABOVE)'])
elif fx=='MB-43':
    edit('MONTEFDT','      DCZ2=AIS*DSQRT(1.0D0-DCX2*DCX2-DCY2*DCY2)',
         ['      DCZ2=AIS*DSQRT(DMAX1(0.0D0,1.0D0-DCX2*DCX2-DCY2*DCY2))'],
         ['MB-43: NEAR A TURNING POINT ROUNDING CAN MAKE THE ARGUMENT',
          '-1E-16; DCZ2 WAS NAN AND THE AVALANCHE COULD NOT END'])
elif fx=='MB-44':
    edit('GAS7',' 3710 QIN(2,I)=Y4DSUM(N4DSUM)*(X4DSUM(N4DSUM)/EN)**3*1.0D-18',
         [' 3710 QIN(23,I)=Y4DSUM(N4DSUM)*(X4DSUM(N4DSUM)/EN)**3*1.0D-18'],
         ['MB-44: WAS QIN(2,I): THE 4D-SUM TAIL OVERWROTE LEVEL 2 (1S4)',
          'ABOVE 100 EV AND LEFT LEVEL 23 EMPTY'])
elif fx=='MB-45':
    edit('GAS61','      QIN(7,I)=QIN(7,1)*APOPV3/DEGV3*1.D-16',
         ['      QIN(7,I)=QIN(7,I)*APOPV3/DEGV3*1.D-16'],
         ['MB-45: WAS QIN(7,1), I.E. THE FINAL VALUE OF THE FIRST BIN',
          'TIMES 1E-16 AGAIN (V3 SUPERELASTIC ABOUT 1E-33 CM2)'])
    edit('GAS61','  465 QIN(7,I)=YVBV3(NVIBV3)*(XVBV3(NVIBV3)/(EN-EIN(8)))**2',
         ['  465 QIN(7,I)=YVBV3(NVIBV3)*(XVBV3(NVIBV3)/(EN+EIN(8)))**2'],
         ['MB-45: WAS (EN-EIN(8)); THE SUPERELASTIC ENERGY IS EN+EIN(8)',
          'AS IN THE TABLE BRANCH AND IN V2, V4, V1'])
elif fx=='MB-46':
    s,e=body('GAS31')
    i=next(k for k in range(s,e) if L[k].startswith('      QIN(2,I)=DBK*DLOG('))
    assert L[i+1].rstrip()=='     /*PJ(2)*AJG2/(AJG*(2.0*AJ+1.0)*EN)',L[i+1]
    L[i:i+2]=['C NIMBOLTZ FIX MB-46: WAS PJ(2) (POPULATION OF J=1); THE INITIAL',
              'C               STATE OF 00-->10 IS THE GROUND STATE PJ(1)',
              L[i],'     /*PJ(1)*AJG2/(AJG*(2.0*AJ+1.0)*EN)']
    edit('GAS31','     /*(PJ(4)*AJG2+PJ(5)*(AJG2+1.0))/(AJG*(2.0*AJ+1.0)*EN)',
         ['     /*(PJ(4)*AJG2+PJ(5)*(AJG2-1.0))/(AJG*(2.0*AJ+1.0)*EN)'],
         ['MB-46: WAS (AJG2+1.0); THE K=1 WEIGHT IS AJG**2-K**2 AS IN ALL',
          'OTHER TRANSITIONS (QIN(3) IS IN THE STATEMENT ABOVE)'])
    s,e=body('GAS31')
    i=next(k for k in range(s,e-1) if L[k].rstrip()=='      AJG=1.0' and L[k+1].rstrip()=='      AJG=2.0')
    L[i:i+1]=['C NIMBOLTZ FIX MB-46: WAS AJG=1.0 (OVERWRITTEN BELOW), SO AJ KEPT',
              'C               2.0 FROM 20-->10; THE INITIAL J OF 10-->20 IS 1',
              '      AJ=1.0']
elif fx=='MB-47':
    edit('GAS49','      E(2)=2.0*EMASS/(114.0416*AMU)',['      E(2)=2.0*EMASS/(195.0383*AMU)'],
         ['MB-47: WAS 114.0416, THE MASS OF C3F4H2 (GAS45); C4F7N IS 195.0383'])
    edit('GAS49','      NVIBL=19',['      NVIBL=21'],
         ['MB-47: WAS 19 AS IN GAS45; XVIBL/YVIBL HERE HAVE 21 POINTS'])
    edit('GAS49','      NVIBH=19',['      NVIBH=20'],
         ['MB-47: WAS 19 AS IN GAS45; XVIBH/YVIBH HERE HAVE 20 POINTS'])
elif fx=='MB-48':
    s,e=body('GAS44')
    i=next(k for k in range(s,e) if L[k].rstrip()=='C CORRECT THE IONISATION FOR SPLIT INTO KSHELLS')
    assert [x.rstrip() for x in L[i-2:i+4]]==['      IF(EN.LE.(2.0*EION(3))) GO TO 41',
        '      PEQION(3,I)=PEQEL(2,(I-IOFFION(3)))',
        'C CORRECT THE IONISATION FOR SPLIT INTO KSHELLS',
        '      QION(1,I)=QION(1,I)-AUGKC*QION(2,I)-AUGKN*QION(3,I)',
        'C ATTACHMENT','   41 Q(4,I)=0.0'],L[i-2:i+4]
    L[i:i+4]=['C CORRECT THE IONISATION FOR SPLIT INTO KSHELLS',
              'C NIMBOLTZ FIX MB-48: LABEL 41 MOVED HERE FROM THE ATTACHMENT.',
              'C               THE CORRECTION WAS SKIPPED BELOW 2*EION(3) =',
              'C               803 EV (K-SHELLS COUNTED TWICE ABOVE 285 EV)',
              '   41 QION(1,I)=QION(1,I)-AUGKC*QION(2,I)-AUGKN*QION(3,I)',
              'C ATTACHMENT','      Q(4,I)=0.0']
elif fx=='MB-49':
    c=['MB-49: WAS GO TO 151, THE LOOP\'S OWN END, SO J=NION ALWAYS AND',
       'THE K-SHELL WAS EXTRAPOLATED FROM THE LAST TABLE INTERVAL']
    edit('GAS29','      IF(EN.LE.XION11(J)) GO TO 151',['      IF(EN.LE.XION11(J)) GO TO 152'],c)
    edit('GAS43','      IF(EN.LE.XION1(J)) GO TO 151',['      IF(EN.LE.XION1(J)) GO TO 152'],c)
elif fx=='MB-50':
    for g in ('GAS29','GAS52'):
        edit(g,'      PEQIN(L,I)=1.0-EPSIL',['      PEQIN((2*L-1),I)=1.0-EPSIL'],
             ['MB-50: WAS PEQIN(L,I) (LEVELS 4-6); THE DIPOLE INELASTICS OF',
              'THIS LOOP ARE 2L-1 = 7, 9, 11 (CF. XSECDUM AND LOOP 385)'])
elif fx=='MB-51':
    c=lambda n,m:['MB-51: WAS EIN(%d), THE THRESHOLD OF ANOTHER LEVEL; THIS IS'%m,
                  'LEVEL %d'%n]
    edit('GAS9','  417 IF(EN.LE.(EIN(21))) GO TO 418',['  417 IF(EN.LE.(EIN(20))) GO TO 418'],c(20,21))
    for g in ('GAS21','GAS47'):
        edit(g,'  727 IF(EN.LE.EIN(91)) GO TO 728',['  727 IF(EN.LE.EIN(98)) GO TO 728'],c(98,91))
    for g in ('GAS22','GAS48'):
        edit(g,'  744 IF(EN.LE.EIN(114)) GO TO 745',['  744 IF(EN.LE.EIN(115)) GO TO 745'],c(115,114))
        edit(g,'  761 IF(EN.LE.EIN(131)) GO TO 762',['  761 IF(EN.LE.EIN(132)) GO TO 762'],c(132,131))
    edit('GAS23','      IF(EN.LE.EIN(194)) GO TO 825',['      IF(EN.LE.EIN(199)) GO TO 825'],c(199,194))
    edit('GAS60','  450 IF(EN.LE.(EIN(26))) GO TO 451',['  450 IF(EN.LE.(EIN(25))) GO TO 451'],c(25,26))
    edit('GAS60','  452 IF(EN.LE.(EIN(28))) GO TO 453',['  452 IF(EN.LE.(EIN(27))) GO TO 453'],c(27,28))
    edit('GAS61','  632 IF(EN.LE.EIN(18)) GO TO 633',['  632 IF(EN.LE.EIN(19)) GO TO 633'],c(19,18))
elif fx=='MB-52':
    for n,nxt in ((25,376),(26,379),(27,382)):
        lab={25:3751,26:3781,27:3811}[n]
        edit('GAS7',' %d IF(EN.LE.(2.0*EIN(%d))) GO TO %d'%(lab,n,nxt),
             [' %d IF(EN.LE.(2.0*EIN(%d))) GO TO %d'%(lab,n,nxt),
              '      PEQIN(%d,I)=PEQEL(2,(I-IOFFN(%d)))'%(n,n)],
             ['MB-52: THE COPY OF THE ELASTIC ANGULAR DISTRIBUTION WAS',
              'MISSING AFTER THIS TEST (ALL OTHER 47 LEVELS HAVE IT)'])
    s,e=body('GAS11')
    i=next(k for k in range(s,e) if L[k].rstrip()=='      PEQION(2,I)=0.5D0')
    assert L[i+1].rstrip()=='      IF(NANISO.EQ.2) PEQIN(2,I)=0.0',L[i+1]
    L[i+1:i+2]=['C NIMBOLTZ FIX MB-52: WAS PEQIN(2,I) (LEVEL 2, RESET LATER ANYWAY)',
                '      IF(NANISO.EQ.2) PEQION(2,I)=0.0']
    edit('GAS15','  629 IF(EN.GT.(3.0*EIN(59))) PEQIN(61,I)=PEQEL(2,(I-IOFFN(59)))',
         ['  629 IF(EN.GT.(3.0*EIN(59))) PEQIN(59,I)=PEQEL(2,(I-IOFFN(59)))'],
         ['MB-52: WAS PEQIN(61,I); THIS IS LEVEL 59 (B1 SIGMA)'])
    edit('GAS18',' 1776 IF(EN.LE.(2.0*EIN(147))) GO TO 776',
         [' 1776 IF(EN.LE.(2.0*EIN(156))) GO TO 776'],
         ['MB-52: WAS 2.0*EIN(147), ANOTHER LEVEL; THIS IS LEVEL 156'])
    edit('GAS23','      IF(EN.GT.4.0) GO TO 425',['      IF(EN.LT.4.0) GO TO 425'],
         ['MB-52: WAS EN.GT.4.0 (INVERTED): VIBRATIONS ARE ISOTROPIC BELOW',
          '4 EV, SEE THE NOTE AT LEVEL 111 AND THE OTHER VIBRATIONS'])
    s,e=body('GAS23')
    i=next(k for k in range(s,e) if L[k].rstrip()=='      QIN(128,I)=(A*EN+B)*1.D-18')
    assert L[i+1].rstrip()=='      GO TO 515' and L[i+2].startswith(' 5121 QIN(128,I)=') and L[i+3].rstrip()=='  515 CONTINUE',L[i:i+4]
    assert not any(re.match(r'^ *5122 ',x) or 'GO TO 5122' in x for x in L[s:e])
    L[i+1:i+3]=['      GO TO 5122',L[i+2],
                'C NIMBOLTZ FIX MB-52: THE COPY OF THE ELASTIC ANGULAR DISTRIBUTION',
                'C               WAS MISSING FOR LEVEL 128 (LEVELS 123-127 AND 129',
                'C               HAVE IT)',
                ' 5122 PEQIN(128,I)=PEQEL(2,(I-IOFFN(128)))']
    edit('GAS31','      IF(EN.GT.2.0*EIN(32)) PEQIN(32,I)=PEQIN(32,(I-IOFFN(32)))',
         ['      IF(EN.GT.2.0*EIN(32)) PEQIN(32,I)=PEQEL(2,(I-IOFFN(32)))'],
         ['MB-52: WAS PEQIN(32,...), WHICH IS 0; ALL OTHER LEVELS COPY PEQEL'])
    edit('GAS60','      PEQIN(24,I)=PEQEL(2,(I-IOFFN(25)))',['      PEQIN(24,I)=PEQEL(2,(I-IOFFN(24)))'],
         ['MB-52: WAS IOFFN(25), THE OFFSET OF ANOTHER LEVEL'])
elif fx=='MB-53':
    edit('GAS15','  693 QIN(72,I)=YVIB20(NVIB)*(XVIB(NVIB)/EN)*1.D-16',
         ['  693 QIN(72,I)=YVIB21(NVIB)*(XVIB(NVIB)/EN)*1.D-16'],
         ['MB-53: WAS YVIB20 (LEVEL 71); LEVEL 72 IS INTERPOLATED IN YVIB21'])
    for g in ('GAS22','GAS48'):
        s,e=body(g)
        i=next(k for k in range(s,e) if L[k].startswith('      QIN(105,I)=.003391/(EIN(105)*BETA2)'))
        assert L[i+1].rstrip()=='     /(4.0*EIN(104)))-BETA2-DEN(I)/2.0)*BBCONST*EN/(EN+EIN(104)+BEF(4))',L[i+1]
        L[i:i+2]=['C NIMBOLTZ FIX MB-53: WAS EIN(104) (LEVEL 104, COPIED) IN THE',
                  'C               LOGARITHM AND THE DENOMINATOR',
                  L[i],'     /(4.0*EIN(105)))-BETA2-DEN(I)/2.0)*BBCONST*EN/(EN+EIN(105)+BEF(4))']
    edit('GAS25','      ARES=AMPV3R*(EN*EIN(58))*(A*(EN+EIN(58))+B)/EN',
         ['      ARES=AMPV3R*(EN+EIN(58))*(A*(EN+EIN(58))+B)/EN'],
         ['MB-53: WAS (EN*EIN(58)); DETAILED BALANCE NEEDS EN+EIN(58) AS',
          'IN LEVEL 55'])
    edit('GAS16','      RAT=YSG13M(NSNG13)*(XSNG12(NSNG13)/EN)',
         ['      RAT=YSG13M(NSNG13)*(XSNG13(NSNG13)/EN)'],
         ['MB-53: WAS XSNG12 (SAME LAST VALUE, NO EFFECT)'])
    edit('GAS18','      IF(EN.GT.XV101(NV300)) GO TO 293',['      IF(EN.GT.XV300(NV300)) GO TO 293'],
         ['MB-53: WAS XV101 (SAME LAST VALUE, NO EFFECT)'])
elif fx=='MB-54':
    def off(g,first,n):
        s,e=body(g)
        idx=[k for k in range(s,e) if L[k].rstrip()==first.rstrip()]
        assert len(idx)==1,(g,first,idx)
        i=idx[0]
        L[i:i+n]=['C NIMBOLTZ FIX MB-54: DEBUG OUTPUT SWITCHED OFF']+['C'+x[1:] for x in L[i:i+n]]
    for g in ('GAS45','GAS49'):
        off(g,'      WRITE(6,9011) EN,QELA,QMMT,QSUP,QVIB,QIN(13,I),QTRIP,',2)
    off('GAS49',"      WRITE(6, *)'--------------XSEC--------------'",3)
    off('GAS61','      WRITE(6,392) ATRP',1)
elif fx=='MB-55':
    edit('GAS4','     /8.55D-5,7.86D-5,78.27D-5,6.78D-5,6.35D-5,5.63D-5,5.07D-5/',
         ['     /8.55D-5,7.86D-5,7.27D-5,6.78D-5,6.35D-5,5.63D-5,5.07D-5/'],
         ['MB-55: WAS 78.27D-5 (STRAY DIGIT); GAS3 (HELIUM 4) HAS 7.27D-5'])
elif fx=='MB-56':
    edit('GAS25','    4 PJ(K)=(2.0*AK-1.0)*DEXP(-AK*(AK+1.0)*B0/AKT)',
         ['    4 PJ(K)=(2.0*AK+1.0)*DEXP(-AK*(AK+1.0)*B0/AKT)'],
         ['MB-56: WAS (2.0*AK-1.0); THE DEGENERACY OF J IS 2J+1 (J=0 ENTERS',
          'THE SUM BELOW AS 1; CO, METHANOL, ETHANOL, PROPANOLS USE 2J+1)'])
elif fx=='MB-57':
    s,e=body('SETUPT')
    i=next(k for k in range(s,e) if L[k].startswith('  999 WRITE(6,87)'))
    assert L[i+3].rstrip()=='      RETURN',L[i+1:i+4]
    c=['C NIMBOLTZ FIX MB-57: STOP ON AN INPUT ERROR AS SETUP DOES (LAST',
       'C               STAYED 0 AND THE RUN WENT ON WITH NMAX, TMAX ETC. UNSET)']
    L[i+3:i+3]=c+['      LAST=1']
elif fx=='MB-58':
    # the gas routines mark a moderation level by EIN=0.024999 (REAL*4, as
    # written in GAS45, GAS49, GAS51); MIXER/MIXERT flag it before EIN is
    # divided by RGAS, MONTE* test the flag instead of |EI-0.024999|<=1D-4
    for r,com,zero in (('MIXER','      COMMON/MODLV/MODLVL(960)',
                        ['      DO 9580 I=1,960',' 9580 MODLVL(I)=0']),
                       ('MIXERT','      COMMON/MODLVT/MODLVT(6,300)',
                        ['      DO 9580 I=1,300','      DO 9580 K=1,6',' 9580 MODLVT(K,I)=0'])):
        edit(r,'      IMPLICIT INTEGER*8 (I-N)',['      IMPLICIT INTEGER*8 (I-N)',com],
             ['MB-58: 1 FOR A MODERATION LEVEL (ENERGY LOSS = E - 0.024999)'])
        edit(r,'      NISO=0',zero+['      NISO=0'],['MB-58: NO LEVEL IS A MODERATION LEVEL UNLESS MARKED BELOW'])
        for n in range(1,7):
            if r=='MIXER':
                old='      EIN(NP)=EI%d(J)/RGAS%d'%(n,n)
                flag='      IF(EI%d(J).EQ.0.024999) MODLVL(NP)=1'%n
            else:
                old='       EIN(KGAS,NP)=EI%d(J)/RGAS%d'%(n,n)
                flag='       IF(EI%d(J).EQ.0.024999) MODLVT(KGAS,NP)=1'%n
            edit(r,old,[old,flag],
                 ['MB-58: THE GAS ROUTINE GIVES A MODERATION LEVEL THE ENERGY','LOSS 0.024999 (EXACTLY, IN SINGLE PRECISION)'])
    old='      IF(ABS(EI-0.024999).LE.1D-4) THEN'
    for r in ('MONTE','MONTEA','MONTEB','MONTEC','MONTEFT','MONTEFD','MONTEFTG','MONTEFTH','MONTEFTA'):
        edit(r,'      IMPLICIT INTEGER*8 (I-N)',['      IMPLICIT INTEGER*8 (I-N)','      COMMON/MODLV/MODLVL(960)'],
             ['MB-58: MODERATION LEVELS, SET IN MIXER'])
        edit(r,old,['      IF(MODLVL(I).EQ.1) THEN'],
             ['MB-58: WAS IF(ABS(EI-0.024999).LE.1D-4), WHICH ALSO CAUGHT THE','ORDINARY 0.025 EV LEVELS OF H2S AND TMA'])
    for r in ('MONTET','MONTEAT','MONTEBT','MONTECT','MONTEFTT','MONTEFDT','MONTEFTGT','MONTEFTHT','MONTEFTAT'):
        edit(r,'      IMPLICIT INTEGER*8 (I-N)',['      IMPLICIT INTEGER*8 (I-N)','      COMMON/MODLVT/MODLVT(6,300)'],
             ['MB-58: MODERATION LEVELS, SET IN MIXERT'])
        edit(r,old,['      IF(MODLVT(KGAS,I).EQ.1) THEN'],
             ['MB-58: WAS IF(ABS(EI-0.024999).LE.1D-4), WHICH ALSO CAUGHT THE','ORDINARY 0.025 EV LEVELS OF H2S AND TMA'])
else: sys.exit('unknown fix')
open(F,'w').write('\n'.join(L))
