#!/bin/bash
# Reproduces every bug in README.md against a Magboltz source file.
#   bugs/reproduce.sh [magboltz.f]      (default: ../magboltz-11.21.f)
# Upstream 11.21:  git show master:magboltz-11.21.f > /tmp/up.f; bugs/reproduce.sh /tmp/up.f
# Builds (gfortran, NSCALE reduced 10x so that clean runs finish quickly):
#   B   -fcheck=bounds                          out-of-bounds array reads
#   BI  -fcheck=bounds -finit-integer=-1234567  undefined integer used as index
#   T   -finit-real=snan -ffpe-trap=invalid     first arithmetic on an undefined real
#   P   plain                                   (cross-section printouts; decks: drift velocity)
# For each case of cases.txt one line: the first runtime error, a NaN in the
# printout, "clean" (decks), or the printed values (cross-section cases). The full outputs are kept in $WORK (default /tmp/mbrepro).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src=$(realpath "${1:-$here/../magboltz-11.21.f}")
work=${WORK:-/tmp/mbrepro}
mkdir -p "$work/out"; cd "$work"
sed 's/NSCALE=40000000/NSCALE=4000000/' "$src" > magboltz.f
start=$(grep -n '^      PROGRAM MAGBOLTZ' magboltz.f | cut -d: -f1)
end=$(awk -v s="$start" 'NR>s && /^      SUBROUTINE ANGCUT/{print NR-1; exit}' magboltz.f)
awk -v s="$start" -v e="$end" 'NR<s || NR>e' magboltz.f > mblib.f
F="gfortran -O0 -g -fbacktrace -std=legacy -w"
T="-finit-real=snan -finit-integer=-1234567 -ffpe-trap=invalid"
$F -fcheck=bounds magboltz.f -o mb-B &
$F magboltz.f -o mb-P &
$F -fcheck=bounds -finit-integer=-1234567 magboltz.f -o mb-BI &
$F $T magboltz.f -o mb-T &
$F "$here/tools/xsec.f" mblib.f -o xs-P &
$F $T "$here/tools/xsec.f" mblib.f -o xs-T &
wait
n=0
grep -v '^#' "$here/cases.txt" | while read -r id build kind rest; do
  n=$((n+1)); o=out/$n
  if [ "$kind" = deck ]; then
    deck=$(echo "$rest" | awk '{print $1}')
    ( set +e; timeout "${TIMEOUT:-3600}" ./mb-$build < "$here/decks/$deck.in" > $o.out 2> $o.err; true ) 2>/dev/null
    what=$deck
  else
    args=$(echo "$rest" | sed -E "s/^(([^ ]+ +){2}[^ ]+ +'[A-Z]+' +[0-9]+ +[0-9]+).*/\1/")
    ( set +e; echo "$args" | timeout 600 ./xs-$build > $o.out 2> $o.err; true ) 2>/dev/null
    what="xsec $args"
  fi
  err=$(grep -m1 -E 'Fortran runtime error|Floating-point exception|SIGFPE' $o.err || true)
  loc=$(grep -m1 -oE 'magboltz.f:[0-9]+|mblib.f:[0-9]+|At line [0-9]+ of file [a-z.]+' $o.err || true)
  if [ -n "$err" ]; then res="$err ${loc}"
  elif grep -q -w -E 'NaN|Infinity' $o.out; then res="NaN in printout"
  elif [ "$kind" = xsec ]; then res=$(awk '/ EV /{printf "%s ", $NF}' $o.out)
  elif [ "$build" = P ]; then res=$(awk '/Z DRIFT VELOCITY/{printf "vz %s +- %s ", $5, $8}' $o.out)
  else res=clean; fi
  printf '%-6s %-3s %-28s %s\n' "$id" "$build" "$what" "$res"
done
