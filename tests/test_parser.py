import logging

import pytest

from pysaleryd.const import DataKey, MessageContext, MessageSeparator
from pysaleryd.data import Message, SystemProperty, UnsupportedMessageType

__author__ = "Björn Dalfors"
__copyright__ = "Björn Dalfors"
__license__ = "MIT"


_LOGGER = logging.getLogger(__name__)


def test_parse_int_from_list_str():
    """Test parsing int list"""
    m = Message.decode("#MF: 1+ 0+ 2+30\r")
    assert m.key == DataKey.MODE_FAN
    assert isinstance(m.payload, str)
    assert m.message_context == MessageContext.NONE


def test_parse_ack():
    m = Message.decode("#$MF: 1\r")
    assert m.key == DataKey.MODE_FAN
    assert isinstance(m.payload, str)
    assert m.message_context == MessageContext.ACK_OK


def test_parse_ack_error():
    message = Message.decode("#!MF:\r")
    assert message.key == "MF"
    assert isinstance(message.payload, str)
    assert message.message_context == MessageContext.ACK_ERROR


def test_parse_int_from_str():
    """Test parsing int"""
    message = Message.decode("#*SC:0\r")
    assert message.key == DataKey.CONTROL_SYSTEM_VERSION
    assert isinstance(message.payload, str)
    assert message.payload == "0"
    assert message.message_context == MessageContext.NONE


def test_parse_str_from_str():
    """Test parsing str"""
    om = Message(DataKey.MODEL_NAME, "TestModel")
    message = Message.decode(om.encode())
    assert message.key == DataKey.MODEL_NAME
    assert isinstance(message.payload, str)
    assert message.payload == "TestModel"
    assert message.message_context == MessageContext.NONE

    message = Message.decode(
        f"{MessageSeparator.MESSAGE_START}{DataKey.CONTROL_SYSTEM_VERSION}{MessageSeparator.PAYLOAD_START}    1.x.1{MessageSeparator.MESSAGE_END}"  # noqa: E501
    )
    assert message.key == DataKey.CONTROL_SYSTEM_VERSION
    assert message.payload == "1.x.1"
    assert message.message_context == MessageContext.NONE


def test_parse_error():
    """Test parse error"""
    with pytest.raises(UnsupportedMessageType):
        Message.decode("wer")


def test_parse_system_property():
    """Test parse SystemProperty"""
    m = Message(DataKey.INSTALLER_PASSWORD, "1")
    parsed = SystemProperty.from_message(m)
    assert parsed.key == DataKey.INSTALLER_PASSWORD
    assert parsed.value == 1

    m.payload = "1+ 2+ 3+0"
    parsed = SystemProperty.from_str(m.key, m.payload)
    assert parsed.value == 1
    assert parsed.min_value == 2
    assert parsed.max_value == 3

    m.payload = "test"
    parsed = SystemProperty.from_str(m.key, m.payload)
    assert parsed.value == "test"


def test_parse_system_property_with_extra():
    """Test parse SystemProperty with extra value"""
    m = Message(DataKey.INSTALLER_PASSWORD, "1+ 2+ 3+ 4+")
    parsed = SystemProperty.from_str(m.key, m.payload)
    assert parsed.key == DataKey.INSTALLER_PASSWORD
    assert parsed.value == 1
    assert parsed.min_value == 2
    assert parsed.max_value == 3
    assert parsed.extra == 4
