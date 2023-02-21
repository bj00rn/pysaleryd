import logging
import pytest

from pysaleryd.utils import Parser, ParseError

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


_LOGGER = logging.getLogger(__name__)

@pytest.fixture
def parser() -> Parser:
    return Parser()

def test_parse_list_from_str(parser: Parser):
    (key, value) = parser.from_str("#MF: 1+ 0+ 2\r")
    assert key == "MF"
    assert isinstance(value, list)
    assert value[0] == 1
    assert value[1] == 0
    assert value[2] == 2

def test_parse_int_from_list_str(parser: Parser):
    (key, value) = parser.from_str("#MF: 1+ 0+ 2+ 30\r")
    assert key == "MF"
    assert isinstance(value, list)
    assert value[0] == 1
    assert value[1] == 0
    assert value[2] == 2
    assert value[3] == 30

def test_parse_int_from_str(parser: Parser):
    (key, value) = parser.from_str("#*XX:0\r")
    assert key == "*XX"
    assert isinstance(value, int)
    assert value == 0

def test_parse_str_from_str(parser: Parser):
    (key, value) = parser.from_str("#*XX: xxx\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "xxx"

    (key, value) = parser.from_str("#*XX:    1.x.1\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "1.x.1"

def test_parse_error(parser: Parser):
    did_throw = False
    try:
        parser.from_str("wer")
    except ParseError:
        did_throw = True
    assert did_throw
