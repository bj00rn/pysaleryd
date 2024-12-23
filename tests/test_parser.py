import logging

import pytest

from pysaleryd.const import DataKey, MessageType
from pysaleryd.data import IncomingMessage, ParseError, SystemProperty

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


_LOGGER = logging.getLogger(__name__)


def test_parse_int_from_list_str():
    """Test parsing int list"""
    (key, value, message_type) = IncomingMessage.from_str("#MF: 1+ 0+ 2+30\r")
    assert key == DataKey.MODE_FAN
    assert isinstance(value, str)
    assert message_type == MessageType.MESSAGE


def test_parse_ack():
    (key, value, message_type) = IncomingMessage.from_str("#$MF:  1+  0+  2+0\r")
    assert key == "MF"
    assert isinstance(value, str)
    assert message_type == MessageType.ACK_OK


def test_parse_ack_error():
    (key, value, message_type) = IncomingMessage.from_str("#!MF:\r")
    assert key == "MF"
    assert isinstance(value, str)
    assert message_type == MessageType.ACK_ERROR


def test_parse_int_from_str():
    """Test parsing int"""
    (key, value, message_type) = IncomingMessage.from_str("#*XX:0\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "0"
    assert message_type == MessageType.MESSAGE


def test_parse_str_from_str():
    """Test parsing str"""
    (key, value, message_type) = IncomingMessage.from_str("#*XX:xxx\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "xxx"
    assert message_type == MessageType.MESSAGE

    (key, value, message_type) = IncomingMessage.from_str("#*XX:    1.x.1\r")
    assert key == "*XX"
    assert isinstance(value, str)
    assert value == "1.x.1"
    assert message_type == MessageType.MESSAGE


def test_parse_error():
    """Test parse error"""
    with pytest.raises(ParseError):
        IncomingMessage.from_str("wer")


def test_parse_system_property():
    """Test parse SystemProperty"""
    key = DataKey.INSTALLER_PASSWORD
    value_str = "1"
    parsed = SystemProperty.from_str(key, value_str)
    assert parsed.key == DataKey.INSTALLER_PASSWORD
    assert parsed.value == 1

    value_str = "1+ 2+ 3+0"
    parsed = SystemProperty.from_str(key, value_str)
    assert parsed.value == 1
    assert parsed.min_value == 2
    assert parsed.max_value == 3

    value_str = "test"
    parsed = SystemProperty.from_str(key, value_str)
    assert parsed.value == "test"
