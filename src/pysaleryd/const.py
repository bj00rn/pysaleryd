"""Constants"""

from __future__ import annotations

from enum import StrEnum


class MessageSeparator(StrEnum):
    """Message payload separator"""

    ACK_OK = "$"
    ACK_ERROR = "!"
    MESSAGE_START = "#"
    PAYLOAD_START = ":"
    MESSAGE_END = "\r"


class MessageContext(StrEnum):
    """Message context"""

    ACK_OK = "ACK_OK"
    ACK_ERROR = "ACK_ERROR"
    NONE = "NONE"

    @classmethod
    def from_str(cls, message: str) -> MessageContext:
        """Decode message context from string"""
        pos1 = message[0]
        pos2 = message[1]
        if pos1 == MessageSeparator.MESSAGE_START:
            if pos2 == MessageSeparator.ACK_OK:
                return MessageContext.ACK_OK
            elif pos2 == MessageSeparator.ACK_ERROR:
                return MessageContext.ACK_ERROR
            else:
                return MessageContext.NONE
        else:
            raise ValueError(f"Invalid message context: {message}")

    def _encode(self) -> str:
        """Encode message context to string"""
        if self == MessageContext.ACK_OK:
            return MessageSeparator.ACK_OK
        elif self == MessageContext.ACK_ERROR:
            return MessageSeparator.ACK_ERROR
        elif self == MessageContext.NONE:
            return ""
        else:
            raise ValueError(f"Invalid message context: {self}")


class DataKey(StrEnum):
    """Data key enumerator"""

    # Scalars
    AIR_TEMPERATURE_AT_HEATER = "*TK"
    AIR_TEMPERATURE_SUPPLY = "*TC"
    CONTROL_SYSTEM_VERSION = "*SC"
    ERROR_FRAME_END = "*EZ"
    ERROR_MESSAGE = "*EB"
    ERROR_FRAME_START = "*EA"
    FAN_SPEED_EXHAUST = "*DB"
    FAN_SPEED_SUPPLY = "*DA"
    FILTER_MONTHS_LEFT = "*FL"
    HEAT_EXCHANGER_ROTOR_PERCENT = "*XA"
    HEAT_EXCHANGER_ROTOR_RPM = "*XB"
    HEATER_POWER_PERCENT = "*MJ"
    MINUTES_LEFT_BOOST_MODE = "*FI"
    MINUTES_LEFT_FIREPLACE_MODE = "*ME"
    MODEL_NAME = "*SB"
    PRODUCT_NUMBER = "*SA"
    INSTALLER_EMAIL = "IB"
    INSTALLER_NAME = "IA"
    INSTALLER_PASSWORD = "IP"
    INSTALLER_PHONE = "IC"
    INSTALLER_WEBSITE = "IE"

    # Vectors x+ x+ x+x
    BOOST_MODE_MINUTES = "FH"
    CONTROL_SYSTEM_STATE = "MP"
    COOLING_MODE = "MK"
    FIREPLACE_MODE = "MB"
    FIREPLACE_MODE_MINUTES = "MC"
    MODE_FAN = "MF"
    MODE_HEATER = "MH"
    MODE_HEATER_POWER_RATING = "MG"
    MODE_TEMPERATURE = "MT"
    TARGET_TEMPERATURE_COOL = "TF"
    TARGET_TEMPERATURE_ECONOMY = "TE"
    TARGET_TEMPERATURE_NORMAL = "TD"

    NONE = ""
