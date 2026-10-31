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
        w=textwrap.wrap(txt,72-15)
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
else: sys.exit('unknown fix')
open(F,'w').write('\n'.join(L))
