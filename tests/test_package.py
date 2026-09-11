"""Tests for the package as a whole: its public surface, its version, and how it imports."""

import subprocess
import sys

import pytest

import pymidiinstrumentdefs
import pymidiinstrumentdefs.midnam


class TestPackageSurface:

	def test_every_public_name_resolves (self) -> None:
		"""A name in __all__ that is not there is a promise the package breaks on import."""
		missing = [name for name in pymidiinstrumentdefs.__all__ if not hasattr(pymidiinstrumentdefs, name)]

		assert missing == []

	def test_public_names_are_the_real_objects (self) -> None:
		"""Re-exported by assignment, so each is the object itself and cannot drift."""
		assert pymidiinstrumentdefs.load is pymidiinstrumentdefs.loading.load
		assert pymidiinstrumentdefs.Definition is pymidiinstrumentdefs.definition.Definition
		assert pymidiinstrumentdefs.DefinitionError is pymidiinstrumentdefs.validation.DefinitionError
		assert pymidiinstrumentdefs.DefinitionNotFound is pymidiinstrumentdefs.loading.DefinitionNotFound

	def test_version_is_a_string (self) -> None:
		"""__version__ resolves whether or not the package was pip-installed."""
		assert isinstance(pymidiinstrumentdefs.__version__, str)
		assert pymidiinstrumentdefs.__version__


class TestImports:

	@pytest.mark.parametrize("module", [
		"pymidiinstrumentdefs",
		"pymidiinstrumentdefs.definition",
		"pymidiinstrumentdefs.loading",
		"pymidiinstrumentdefs.midnam",
		"pymidiinstrumentdefs.validation",
	])
	def test_each_module_imports_first_in_a_fresh_interpreter (self, module: str) -> None:
		"""Annotations that name a sibling module by its full path are evaluated on import.

		When this code was a subpackage of PyMidiDefs, that failed with an error
		blaming a circular import, and every module needed a workaround. As a
		top-level package it must work without one, whichever module is imported
		first. In-process this would prove nothing, because by now every module
		has already been imported.
		"""
		finished = subprocess.run(
			[sys.executable, "-c", f"import {module}"], capture_output = True, text = True, check = False)

		assert finished.returncode == 0, finished.stderr
