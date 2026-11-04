PYTHON ?= python3
SCRIPT = dynasty_draft_lottery.py

.PHONY: run-dynasty-lottery-odds demo-dynasty-lottery-odds test

# Run the script as-is; you type in the teams and points.
run-dynasty-lottery-odds:
	$(PYTHON) $(SCRIPT)

# Run with dummy teams and points (name, points, name, points, ...).
demo-dynasty-lottery-odds:
	@printf '%s\n' \
		Gamma 700 Alpha 100 Hotel 800 Beta 200 \
		Echo 500 Delta 400 Foxtrot 600 Charlie 300 \
		| $(PYTHON) $(SCRIPT)

test:
	$(PYTHON) -m unittest discover -v -p "test_*.py"