from enum import IntEnum, StrEnum


class ConnectionState(StrEnum):
    """State of connection."""

    NONE = ""
    RETRYING = "retrying"
    RUNNING = "running"
    STOPPED = "stopped"


class MessageType(IntEnum):
    """Message type"""

    ACK_OK = 0
    ACK_ERROR = 1
    MESSAGE = 2
    RAW = 3


class PayloadSeparator(StrEnum):
    """Message payload separator"""

    ACK_OK = "$"
    ACK_ERROR = "!"
    MESSAGE_START = "#"
    PAYLOAD_START = ":"


class DataKey(StrEnum):
    """Data key enumerator"""

    # Scalar
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

    # Vecto x+ x+ x+x
    CONTROL_SYSTEM_STATE = "MP"
    MODE_HEATER_POWER_RATING = "MG"
    COOLING_MODE = "MK"
    FIREPLACE_MODE = "MB"
    MODE_FAN = "MF"
    MODE_TEMPERATURE = "MT"
    TARGET_TEMPERATURE_COOL = "TF"
    TARGET_TEMPERATURE_ECONOMY = "TE"
    TARGET_TEMPERATURE_NORMAL = "TD"
    MODE_HEATER = "MH"
