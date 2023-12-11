import logging

import pytest

from pysaleryd.utils import ParseError, Parser

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


_LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="parser")
def _parser() -> Parser:
    return Parser


def test_parse_int_from_list_str(parser: Parser):
    """Test parsing int list"""
    (key, value, _) = parser.from_str("#MF: 1+ 0+ 2+30\r")
    assert key == "MF"
    assert isinstance(value, list)
    assert value[0] == 1
    assert value[1] == 0
    assert value[2] == 2
    assert value[3] == 30


def test_parse_int_from_str(parser: Parser):
    """Test parsing int"""
    (key, value, _) = parser.from_str("#*XX:0\r")
    assert key == "*XX"
    assert isinstance(value, int)
    assert value == 0


def test_parse_str_from_str(parser: Parser):
    """Test parsing str"""
    (key, value, _) = parser.from_str("#*XX:xxx\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "xxx"

    (key, value, _) = parser.from_str("#*XX:    1.x.1\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "1.x.1"


def test_parse_error(parser: Parser):
    """Test parse error"""
    with pytest.raises(ParseError):
        parser.from_str("wer")
