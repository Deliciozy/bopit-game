# Minimal CircuitPython implementation of I2CDisplayBus
# Enough to support SSD1306 display on XIAO ESP32C3

import displayio


class I2CDisplayBus(displayio.I2CDisplay):
    """
    Thin wrapper around displayio.I2CDisplay so that code written for the
    older "i2cdisplaybus" library still works on newer CircuitPython.
    """

    def __init__(self, i2c, device_address=0x3C, reset=None, **kwargs):
        # 在旧版库里参数名是 i2c；在 displayio.I2CDisplay 里是 i2c_bus
        super().__init__(i2c_bus=i2c, device_address=device_address, reset=reset, **kwargs)
