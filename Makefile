# Copyright (C) 2009 Gabriel Falcão <gabriel@nacaolivre.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

green :=
blue :=
red :=
yellow :=
white :=
normal :=
ifeq ($(shell echo $$TERM),xterm)
blue   := "\e[1;34m"
red    := "\e[1;31m"
green  := "\e[1;32m"
yellow := "\e[1;33m"
white  := "\e[1;37m"
normal := "\e[0m"
endif

clean:
	@echo "Cleaning up build and *.pyc files..."
	@find . -name '*.pyc' -exec rm -rf {} \;
	@rm -rf build

unit:
	@echo "Running unit tests..."
	@nosetests -s --with-coverage --cover-package tests/unit

functional:
	@echo "Running functional tests..."
	@nosetests -s --with-coverage --cover-package tests/functional

doctest:
	@echo -ne $(blue)
	@echo "Running doctests..."
	@echo -ne $(red)
	@python -c "import doctest;doctest.testfile('./README.rst', verbose=False, report=True)"
	@echo -ne $(green)
	@echo "tests passed!"
	@echo -ne $(normal)

test: unit functional doctest

build: clean test
	@echo -ne $(yellow)
	@echo "Buiding dead-parrot..."
	@echo -r $(red)
	@python setup.py build
	@echo -ne $(white)
	@echo "Built successfully."
	@echo -ne $(green)
	@echo "Get it in `pwd`/build/lib/"
	@echo -ne $(normal)