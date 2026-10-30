# Reference Fortran builds: fixed flags, no FMA / fast-math (see PORTING_NOTES.md)
ifeq ($(origin FC),default)
FC = gfortran
endif
FFLAGS  = -O0 -ffp-contract=off -std=legacy
VERSIONS = 11.19 11.21

all: $(VERSIONS:%=build/magboltz-%) build/rngdump

build:
	mkdir -p build

build/magboltz-%: magboltz-%.f | build
	$(FC) $(FFLAGS) $< -o $@

clean:
	rm -rf build
.PHONY: all clean

# RNG dumper: drand48/RM48 extracted verbatim from the reference source
build/rngdump: harness/rng/rngdump.f magboltz-11.21.f | build
	awk 'NR>=17865 && NR<=18040' magboltz-11.21.f > harness/rng/rng_extract.f
	$(FC) $(FFLAGS) harness/rng/rngdump.f harness/rng/rng_extract.f -o $@
