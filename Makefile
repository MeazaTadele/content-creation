# One command: make film. Each target runs `python -m pipeline <command>`.
PY ?= python3
RUN = $(PY) -m pipeline

.PHONY: film plan radio validate narration timing refsheet keyframes shots music smoke check test

film:       ; $(RUN) film
plan:       ; $(RUN) plan
radio:      ; $(RUN) radio
validate:   ; $(RUN) validate
narration:  ; $(RUN) narration
timing:     ; $(RUN) timing
refsheet:   ; $(RUN) refsheet
keyframes:  ; $(RUN) keyframes
shots:      ; $(RUN) shots
music:      ; $(RUN) music
smoke:      ; $(RUN) smoke

test:
	$(PY) -m pytest -q tests

# Schema check, unit tests, and a scan of tracked files for anything that looks like a key.
check: validate test
	@! git grep -nIE 'AIza[0-9A-Za-z_-]{20,}|xi-api-key:\s*[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9._-]{30,}|"key"\s*:\s*"[0-9a-f]{32}"' -- . ':!Makefile' \
	  || (echo "possible secret found in tracked files" && exit 1)
	@echo "check passed"
