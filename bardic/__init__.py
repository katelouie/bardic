"""Bardic: Python-first interactive fiction engine"""

__version__ = "0.9.0"

from .compiler.compiler import BardCompiler
from .compiler.parser import parse, parse_file
from .runtime.engine import BardEngine
from .runtime.types import PassageOutput, GameSnapshot

__all__ = [
    "BardCompiler",
    "parse",
    "parse_file",
    "BardEngine",
    "PassageOutput",
    "GameSnapshot",
]
