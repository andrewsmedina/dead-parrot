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

unitandfunctionaltest:
	@nosetests --with-coverage --cover-package tests
doctest:
	@echo -ne "\e[1;34mRunning doctests...\e[0m\n"
	@python -c "import doctest;doctest.testfile('./README.rst', verbose=False, report=True)"

test: unitandfunctionaltest doctest

build: test
	@echo -ne "\e[1;33mBuiding dead-parrot...\e[0m\n"
	@python setup.py build
	@echo -ne "\e[1;37mBuilt sucessfully. \e[1;32mGet it in `pwd`/build/lib/\e[0m\n"