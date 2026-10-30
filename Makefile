# Reference Fortran builds: fixed flags, no FMA / fast-math (see PORTING_NOTES.md)
FC     ?= gfortran
FFLAGS  = -O0 -ffp-contract=off -std=legacy
VERSIONS = 11.19 11.21

all: $(VERSIONS:%=build/magboltz-%)

build/magboltz-%: magboltz-%.f
	@mkdir -p build
	$(FC) $(FFLAGS) $< -o $@

clean:
	rm -rf build
.PHONY: all clean
