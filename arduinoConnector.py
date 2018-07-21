import serial
from math import floor
import time
import pyvjoy

AXES = 6
BUTTONS = 15
TOTAL_BYTES = AXES + BUTTONS

MinAxisValue = 0
MaxAxisValue = floor(65535 / 2)

verbose = False

while True:
    try:
        s = serial.Serial(
            port='COM3',
            baudrate=9600,
            timeout=None,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
            )
        j = pyvjoy.VJoyDevice(1)

        print("Connected")

        def readByte(ser):
            return int.from_bytes(ser.read(), byteorder='little')

        s.reset_input_buffer()

        def stretchValue(value, minFrom, maxFrom):
            return floor((value - minFrom) * (MinAxisValue - MaxAxisValue) / (minFrom - maxFrom) + MinAxisValue)

        while True:
            try:
                s.flushOutput()
                while not readByte(s) == 255:
                    pass
                total = ""

                # Read state bytes from arduino
                joysticksBytes = [readByte(s),readByte(s),readByte(s),readByte(s)]
                buttonBytes = [readByte(s), readByte(s)]

                # left joystick
                leftJoystickX = joysticksBytes[0] & 0x3f
                leftJoystickStretchedX = stretchValue(leftJoystickX, 0, 63)
                leftJoystickY = joysticksBytes[1] & 0x3f
                leftJoystickStretchedY = stretchValue(leftJoystickY, 63, 0)

                # right joystick
                rightJoystickX = ((joysticksBytes[0] & 0xc0) >> 3) + ((joysticksBytes[1] & 0xc0) >> 5) +  ((joysticksBytes[2] & 0x80) >> 7)
                rightJoystickStretchedX = stretchValue(rightJoystickX, 0, 31)
                rightJoystickY = joysticksBytes[2] & 0x1f
                rightJoystickStretchedY = stretchValue(rightJoystickY, 0, 31)


                # shoulders
                shoulderLeft = ((joysticksBytes[2] & 0x60) >> 2) + ((joysticksBytes[3] & 0xe0) >> 5)
                shoulderStretchedLeft = stretchValue(shoulderLeft, 0, 32)
                shoulderRight = joysticksBytes[3] & 0x1f
                shoulderStretchedRight = stretchValue(shoulderRight, 0, 32)

                total += "" + str(leftJoystickX) + ", " + str(leftJoystickY) + ", " + str(rightJoystickX) + ", " + str(rightJoystickY) + ", " + str(shoulderLeft) + ", " + str(shoulderRight) + ", "

                # Update joystick axes
                if AXES > 0:
                    j.set_axis(pyvjoy.HID_USAGE_X, leftJoystickStretchedX)
                if AXES > 1:
                    j.set_axis(pyvjoy.HID_USAGE_Y, leftJoystickStretchedY)
                if AXES > 2:
                    j.set_axis(pyvjoy.HID_USAGE_Z, rightJoystickStretchedX)
                if AXES > 3:
                    j.set_axis(pyvjoy.HID_USAGE_RX, rightJoystickStretchedY)
                if AXES > 4:
                    j.set_axis(pyvjoy.HID_USAGE_RY, shoulderStretchedLeft)
                else:
                    j.set_axis(pyvjoy.HID_USAGE_RY, 16)
                if AXES > 5:
                    j.set_axis(pyvjoy.HID_USAGE_RZ, shoulderStretchedRight)
                else:
                    j.set_axis(pyvjoy.HID_USAGE_RZ, 16)

                # Update button states
                index = -3
                for x in range(2):
                    for y in range(8):
                        val = 1 - int(bool(buttonBytes[x] & (1 << y)))
                        if index + 1 > 0:
                            j.set_button(index + 1, val)
                        total += "{0}".format(val) + ", "
                        index += 1

                if verbose:
                    print(total)
                #time.sleep(0.01)
            except serial.SerialTimeoutException:
                print("timed out")
    except Exception as e:
        print("SerialException raised, retrying after 1 second...")
        print(e)
        time.sleep(1)
