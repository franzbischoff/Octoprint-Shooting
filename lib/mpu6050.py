"""This program handles the communication over I2C
between a Raspberry Pi and a MPU-6050 Gyroscope / Accelerometer combo.

Code based on:

1) Python module
    by MrTijn/Tijndagamer (Tijndagamer/mpu6050 on github)
    Released under the MIT License
    Copyright (c) 2015, 2016, 2017 MrTijn/Tijndagamer

2) MPU6050 Python I2C Class
    by Geir Istad (thisisG/MPU6050-I2C-Python-Class on github)
    which is based on
2.1) I2Cdev library collection - MPU6050 I2C device class
     by Jeff Rowberg <jeff@rowberg.net>
     Released under the MIT license
     Copyright (c) 2012 Jeff Rowberg

"""

import csv
import ctypes
import threading
import time

import smbus


class mpu6050(threading.Thread):
    # Global Variables
    GRAVITIY_MS2 = 9.80665
    address = None
    bus = None
    capturingData = False
    logger=None
    basefolder="."

    # Scale Modifiers
    ACCEL_SCALE_MODIFIER_2G = 16384.0
    ACCEL_SCALE_MODIFIER_4G = 8192.0
    ACCEL_SCALE_MODIFIER_8G = 4096.0
    ACCEL_SCALE_MODIFIER_16G = 2048.0

    GYRO_SCALE_MODIFIER_250DEG = 131.0
    GYRO_SCALE_MODIFIER_500DEG = 65.5
    GYRO_SCALE_MODIFIER_1000DEG = 32.8
    GYRO_SCALE_MODIFIER_2000DEG = 16.4

    # Registers defines
    INT_ENABLE_DATA_RDY_EN = 0x01
    INT_ENABLE_I2C_MST_EN = 0x08
    INT_ENABLE_FIFO_OFLOW_INT = 0x10

    USER_CTRL_FIFO_RESET_BIT = 2
    USER_CTRL_I2C_MST_RESET_BIT = 1
    USER_CTRL_I2C_MST_EN_BIT = 5
    USER_CTRL_FIFO_EN_BIT = 6

    INT_PIN_CFG_I2C_BYPASS = 0x02
    INT_PIN_CFG_FSYNC_INT = 0x04  # enables the FSYNC pin to be used as an interrupt to the host application processor
    INT_PIN_CFG_FSYNC_LEVEL = 0x08  # A transition to the active level specified in FSYNC_INT_LEVEL will trigger an interrupt.
    INT_PIN_CFG_INT_RD_CLEAR = 0x10  # When this bit is equal to 0, interrupt status bits are cleared only by reading INT_STATUS. 1 cleared on any read operation.
    INT_PIN_CFG_LATCH_INT = 0x20  # When this bit is equal to 0, the INT pin emits a 50us long pulse. 1 held high until interrupt is cleared.
    INT_PIN_CFG_INT_OPEN = 0x40  # When this bit is equal to 0, the INT pin is configured as push-pull. 1 to open drain.
    INT_PIN_CFG_INT_LEVEL = 0x80  # When this bit is equal to 0, the logic level for the INT pin is active high. 1 to low.

    CFG_DLPF_CFG_BIT = 2
    CFG_DLPF_CFG_LENGTH = 3

    DLPF_BW_260 = 0x00  # 256 for gyro
    DLPF_BW_184 = 0x01  # 188 for gyro
    DLPF_BW_94 = 0x02  # 98 for gyro
    DLPF_BW_44 = 0x03  # 42 for gyro
    DLPF_BW_21 = 0x04  # 20 for gyro
    DLPF_BW_10 = 0x05  # 10 for gyro
    DLPF_BW_5 = 0x06  # 5 for gyro

    PWR_MGMT1_DEVICE_RESET_BIT = 7
    PWR_MGMT1_SLEEP_BIT = 6
    PWR_MGMT1_CYCLE_BIT = 5
    PWR_MGMT1_TEMP_DIS_BIT = 3
    PWR_MGMT1_CLKSEL_BIT = 2
    PWR_MGMT1_CLKSEL_LENGTH = 3

    FIFO_EN_ACCEL_BIT = 3
    FIFO_EN_ZG_BIT = 4
    FIFO_EN_YG_BIT = 5
    FIFO_EN_XG_BIT = 6
    FIFO_EN_TEMP_BIT = 7

    ACCEL_CONFIG_XA_ST_BIT = 7  # self-test
    ACCEL_CONFIG_YA_ST_BIT = 6  # self-test
    ACCEL_CONFIG_ZA_ST_BIT = 5  # self-test
    ACCEL_CONFIG_AFS_SEL_BIT = 4
    ACCEL_CONFIG_AFS_SEL_LENGTH = 2

    GYRO_CONFIG_FS_SEL_BIT = 4
    GYRO_CONFIG_FS_SEL_LENGTH = 2

    # Pre-defined ranges
    ACCEL_RANGE_2G = 0x00
    ACCEL_RANGE_4G = 0x01
    ACCEL_RANGE_8G = 0x02
    ACCEL_RANGE_16G = 0x03

    GYRO_RANGE_250DEG = 0x00
    GYRO_RANGE_500DEG = 0x01
    GYRO_RANGE_1000DEG = 0x02
    GYRO_RANGE_2000DEG = 0x03

    # MPU-6050 Registers

    XA_OFFS_H = 0x06
    XA_OFFS_L_TC = 0x07
    YA_OFFS_H = 0x08
    YA_OFFS_L_TC = 0x09
    ZA_OFFS_H = 0x0A
    ZA_OFFS_L_TC = 0x0B
    XG_OFFS_USRH = 0x13
    XG_OFFS_USRL = 0x14
    YG_OFFS_USRH = 0x15
    YG_OFFS_USRL = 0x16
    ZG_OFFS_USRH = 0x17
    ZG_OFFS_USRL = 0x18

    SMPLRT_DIV = 0x19

    CONFIG = 0x1A

    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C

    ACCEL_XOUT0 = 0x3B
    ACCEL_YOUT0 = 0x3D
    ACCEL_ZOUT0 = 0x3F

    TEMP_OUT0 = 0x41

    GYRO_XOUT0 = 0x43
    GYRO_YOUT0 = 0x45
    GYRO_ZOUT0 = 0x47

    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C

    # FIFO related registers
    FIFO_EN = 0x23  # configures sensors output to FIFO buffer
    INT_PIN_CFG = 0x37  # configures the behavior of the interrupt signals at the INT pins.
    INT_ENABLE = 0x38  # sets hardware interruption config
    INT_STATUS = 0x3A  # reads current interruption status
    USER_CTRL = 0x6A  # used to enable FIFO buffer
    FIFO_COUNT = 0x72  # 16-bit value
    FIFO_R_W = 0x74  # FIFO data register

    def __init__(self, address, bus=1, logger=None, basefolder=None):
        # Set up mpu6050
        self.address = address
        self.bus = smbus.SMBus(bus)
        self.wake_up()
        self.logger = logger
        if self.basefolder is not None:
            self.basefolder=basefolder

        # set up thread
        threading.Thread.__init__(self)
        self.name = "MPU6050 Module"

        self.log("__init__")

    def log(self, message):
        if self.logger is None:
            print(message)
        else:
            self.logger.info(message)

    def run(self):
        self.log("Starting " + self.name)
        self.capturingData = True
        self.start_capture()
        self.log("Exiting " + self.name)

    def start_capture(self):

        self.log("Start Capture")

        if not self.capturingData:
            return

        self.log("Opening logfile2")

        packet_size = 12  # 2 for each GX GY GZ X Y Z
        log_file = self.basefolder + "/mpu6050_" + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".csv"

        log_fd = open(log_file, 'wb')
        csv_writer = csv.writer(log_fd, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        self.log("Logfile opened")

        # FIFO stuff
        self.reset_user_ctrl_FIFO()  # reset FIFO
        self.set_int_enable(self.INT_ENABLE_FIFO_OFLOW_INT)  # interrupt when data overflow
        self.set_FIFO_config(self.FIFO_EN_ACCEL_BIT, 1)  # use FIFO for accel
        self.set_FIFO_config(self.FIFO_EN_ZG_BIT, 1)  # use FIFO for Gyro Z
        self.set_FIFO_config(self.FIFO_EN_YG_BIT, 1)  # use FIFO for Gyro Y
        self.set_FIFO_config(self.FIFO_EN_XG_BIT, 1)  # use FIFO for Gyro X
        self.set_user_ctrl_FIFO_enable()  # enable using FIFO

        # Your offsets:	2348	635  	1776	 54	  49	 -27
        #                acelX acelY acelZ giroX giroY giroZ
        # other configs
        self.set_x_accel_offset(2354)
        self.set_y_accel_offset(640)
        self.set_z_accel_offset(1779)
        self.set_x_gyro_offset(15)
        self.set_y_gyro_offset(46)
        self.set_z_gyro_offset(-25)
        self.set_accel_range(self.ACCEL_RANGE_2G)  # set 2G for maximal sensibility
        self.set_gyro_range(self.GYRO_RANGE_250DEG)  # set 250DEG for maximal sensibility
        self.set_DLF_mode(self.DLPF_BW_44)  # digital low-pass filter
        self.set_rate(10)  # (1khz / 10) = 100 hz

        start_time = time.clock()

        self.log("Begin while")

        while self.capturingData:
            FIFO_count = self.get_FIFO_count()
            mpu_int_status = self.get_int_status()

            # If overflow is detected by status or fifo count we want to reset
            if (FIFO_count == 1024) or (mpu_int_status & self.INT_ENABLE_FIFO_OFLOW_INT):
                self.reset_user_ctrl_FIFO()
                self.log('OVERFLOW: FIFO count: ' + str(FIFO_count) + ' Int: ' + str(mpu_int_status))
            else:
                while FIFO_count < packet_size:
                    self.log('FIFO count: ' + str(FIFO_count))
                    FIFO_count = self.get_FIFO_count()

                while FIFO_count > packet_size:
                    # self._logger.info('FIFO count2: ' + str(FIFO_count))
                    FIFO_buffer = self.get_FIFO_bytes(packet_size)
                    acc_x = ctypes.c_int16((FIFO_buffer[0] << 8) + FIFO_buffer[1]).value
                    acc_y = ctypes.c_int16((FIFO_buffer[2] << 8) + FIFO_buffer[3]).value
                    acc_z = ctypes.c_int16((FIFO_buffer[4] << 8) + FIFO_buffer[5]).value
                    acc_x /= self.ACCEL_SCALE_MODIFIER_2G
                    acc_y /= self.ACCEL_SCALE_MODIFIER_2G
                    acc_z /= self.ACCEL_SCALE_MODIFIER_2G
                    acc_x *= self.GRAVITIY_MS2
                    acc_y *= self.GRAVITIY_MS2
                    acc_z *= self.GRAVITIY_MS2
                    gyro_x = ctypes.c_int16((FIFO_buffer[6] << 8) + FIFO_buffer[7]).value
                    gyro_y = ctypes.c_int16((FIFO_buffer[8] << 8) + FIFO_buffer[9]).value
                    gyro_z = ctypes.c_int16((FIFO_buffer[10] << 8) + FIFO_buffer[11]).value
                    gyro_x /= self.GYRO_SCALE_MODIFIER_250DEG
                    gyro_y /= self.GYRO_SCALE_MODIFIER_250DEG
                    gyro_z /= self.GYRO_SCALE_MODIFIER_250DEG

                    self.log('X: %3.5f Y: %3.5f Z: %3.5f, GX: %3.5f, GY: %3.5f, GZ: %3.5f' %
                                      (acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z))

                    delta_time = (time.clock() - start_time) * 10
                    data_concat = [
                        '%.3f' % delta_time,
                        '%.5f' % acc_x,
                        '%.5f' % acc_y,
                        '%.5f' % acc_z,
                        '%.5f' % gyro_x,
                        '%.5f' % gyro_y,
                        '%.5f' % gyro_z
                    ]
                    csv_writer.writerow(data_concat)

                    FIFO_count -= packet_size

                    # safety exit if more than 60 seconds recording
                    if(delta_time > 60):
                        self.capturingData=False

        if log_fd:
            log_fd.close()


    def stop(self):
        self.capturingData=False

    # Core bit and byte operations
    def read_bit(self, address, bit_position):
        return self.read_bits(address, bit_position, 1)

    def write_bit(self, address, bit_num, bit_value):
        byte = self.bus.read_byte_data(self.address, address)
        if bit_value:
            byte |= 1 << bit_num
        else:
            byte &= ~(1 << bit_num)
        self.bus.write_byte_data(self.address, address,
                                 ctypes.c_int8(byte).value)

    def read_bits(self, address, bit_start, length):
        byte = self.bus.read_byte_data(self.address, address)
        mask = ((1 << length) - 1) << (bit_start - length + 1)
        byte &= mask
        byte >>= bit_start - length + 1
        return byte

    def write_bits(self, address, bit_start, length, data):
        byte = self.bus.read_byte_data(self.address, address)
        mask = ((1 << length) - 1) << (bit_start - length + 1)
        # Get data in position and zero all non-important bits in data
        data <<= bit_start - length + 1
        data &= mask
        # Clear all important bits in read byte and combine with data
        byte &= ~mask
        byte = byte | data
        # Write the data to the I2C device
        self.bus.write_byte_data(self.address, address,
                                 ctypes.c_int8(byte).value)

    def wake_up(self):
        # Wake up the MPU-6050 since it starts in sleep mode
        self.write_bit(self.PWR_MGMT_1, self.PWR_MGMT1_SLEEP_BIT, 0)

    def reset(self):
        # Reset device
        self.write_bit(self.PWR_MGMT_1, self.PWR_MGMT1_DEVICE_RESET_BIT, 1)
        time.sleep(50 / 1000)

    # I2C communication methods

    def read_i2c_word(self, register):
        """Read two i2c registers and combine them.

        register -- the first register to read from.
        Returns the combined read results.
        """
        # Read the data from the registers
        high = self.bus.read_byte_data(self.address, register)
        low = self.bus.read_byte_data(self.address, register + 1)

        value = (high << 8) + low

        if (value >= 0x8000):
            return -((65535 - value) + 1)
        else:
            return value

    # MPU-6050 Methods
    def set_rate(self, divider):
        """Configure the sampling rate divider.
        Sample Rate = Gyroscope Output Rate / (1 + SMPLRT_DIV)
        where Gyroscope Output Rate = 8kHz when the DLPF is disabled (DLPF_CFG = 0 or 7), and 1kHz
        when the DLPF is enabled.
        Note: The accelerometer output rate is 1kHz. This means that for a Sample Rate greater than 1kHz,
        the same accelerometer sample may be output to the FIFO, DMP, and sensor registers more than
        once
        """
        self.bus.write_byte_data(self.address, self.SMPLRT_DIV, divider)

    def set_DLF_mode(self, mode):
        """Configure the Digital Low-pass Filter.

        CFG |   Accelerometer   |    Gyroscope
            | BW(hz)  Delay(ms) | BW(hz)  Delay(ms)
         0  |  260      0.0     |  256      0.98
         1  |  184      2.0     |  188      1.9
         2  |   94      3.0     |   98      2.8
         3  |   44      4.9     |   42      4.8
         4  |   21      8.5     |   20      8.3
         5  |   10     13.8     |   10     13.4
         6  |    5     19.0     |    5     18.6
        """
        self.write_bits(self.CONFIG, self.CFG_DLPF_CFG_BIT,
                        self.CFG_DLPF_CFG_LENGTH, mode)

    # Acceleration and gyro offset
    def set_x_accel_offset(self, offset):
        self.bus.write_byte_data(self.address, self.XA_OFFS_H,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.XA_OFFS_L_TC,
                                 ctypes.c_int8(offset).value)

    def set_y_accel_offset(self, offset):
        self.bus.write_byte_data(self.address, self.YA_OFFS_H,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.YA_OFFS_L_TC,
                                 ctypes.c_int8(offset).value)

    def set_z_accel_offset(self, offset):
        self.bus.write_byte_data(self.address, self.ZA_OFFS_H,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.ZA_OFFS_L_TC,
                                 ctypes.c_int8(offset).value)

    def set_x_gyro_offset(self, offset):
        self.bus.write_byte_data(self.address, self.XG_OFFS_USRH,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.XG_OFFS_USRL,
                                 ctypes.c_int8(offset).value)

    def set_y_gyro_offset(self, offset):
        self.bus.write_byte_data(self.address, self.YG_OFFS_USRH,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.YG_OFFS_USRL,
                                 ctypes.c_int8(offset).value)

    def set_z_gyro_offset(self, offset):
        self.bus.write_byte_data(self.address, self.ZG_OFFS_USRH,
                                 ctypes.c_int8(offset >> 8).value)
        self.bus.write_byte_data(self.address, self.ZG_OFFS_USRL,
                                 ctypes.c_int8(offset).value)

    def get_FIFO_bytes(self, FIFO_count):
        """Reads the FIFO buffer.

        Returns a list of bytes with the data on FIFO buffer.
        """
        return_list = list()
        for index in range(0, FIFO_count):
            return_list.append(
                self.bus.read_byte_data(self.address, self.FIFO_R_W))
        return return_list

    def get_int_enable(self):
        """Get the current configuration of which events will signal an interruption
        on physical pin."""
        value = self.bus.read_byte_data(self.address, self.INT_ENABLE)
        return value

    # 0x01 == DATA READY; 0x10 == buffer overflow
    def set_int_enable(self, enabled):
        """Set which events will signal an interruption on physical pin."""
        self.bus.write_byte_data(self.address, self.INT_ENABLE, enabled)

    def set_int_config(self, value):
        """Configures the behavior of the interrupt signals at the INT pins."""
        self.bus.write_byte_data(self.address, self.INT_PIN_CFG, value)

    def get_int_config(self):
        """Reads the configuration of INT pins behaviour."""
        value = self.bus.read_byte_data(self.address, self.INT_PIN_CFG)
        return value

    # 0x01 == DATA READY; 0x10 == buffer overflow
    def get_int_status(self):
        """Reads the status of interruption."""
        status = self.bus.read_byte_data(self.address, self.INT_STATUS)
        return status

    def set_FIFO_config(self, flag, value):
        """Set the configuration of FIFO. This is used to choose which
        sensor data is written on buffer."""
        self.write_bit(self.FIFO_EN, flag, value)

    def get_FIFO_config(self):
        """Reads the configuration of FIFO. This is used to choose which
        sensor data is written on buffer."""
        value = self.bus.read_byte_data(self.address, self.FIFO_EN)
        return value

    def get_FIFO_count(self):
        """Reads the current amount of data on FIFO buffer."""
        count = self.read_i2c_word(self.FIFO_COUNT)
        return count

    def set_user_ctrl_FIFO_enable(self):
        """Enables the FIFO buffer on USER_CTRL register."""
        self.write_bit(self.USER_CTRL, self.USER_CTRL_FIFO_EN_BIT, 1)

    def reset_user_ctrl_FIFO(self):
        """Resets the FIFO flag on USER_CTRL register."""
        self.write_bit(self.USER_CTRL, self.USER_CTRL_FIFO_RESET_BIT, 1)

    def get_user_ctrl(self):
        """Reads the USER_CTRL register.

        Returns the value set on register.
        """
        value = self.bus.read_byte_data(self.address, self.USER_CTRL)
        return value

    def get_temp(self):
        """Reads the temperature from the onboard temperature sensor of the MPU-6050.

        Returns the temperature in degrees Celcius.
        """
        raw_temp = self.read_i2c_word(self.TEMP_OUT0)

        # Get the actual temperature using the formule given in the
        # MPU-6050 Register Map and Descriptions revision 4.2, page 30
        actual_temp = (raw_temp / 340.0) + 36.53

        return actual_temp

    def set_accel_range(self, accel_range):
        """Sets the range of the accelerometer to range.

        accel_range -- the range to set the accelerometer to. Using a
        pre-defined range is advised.
        """
        # Write the new range to the ACCEL_CONFIG register
        self.write_bits(self.ACCEL_CONFIG, self.ACCEL_CONFIG_AFS_SEL_BIT,
                        self.ACCEL_CONFIG_AFS_SEL_LENGTH, accel_range)

    def read_accel_range(self, raw=False):
        """Reads the range the accelerometer is set to.

        If raw is True, it will return the raw value from the ACCEL_CONFIG
        register
        If raw is False, it will return an integer: -1, 2, 4, 8 or 16. When it
        returns -1 something went wrong.
        """
        raw_data = self.bus.read_byte_data(self.address, self.ACCEL_CONFIG)
        raw_data >>= 3
        raw_data &= 0x03

        if raw is True:
            return raw_data
        else:
            if raw_data == self.ACCEL_RANGE_2G:
                return 2
            elif raw_data == self.ACCEL_RANGE_4G:
                return 4
            elif raw_data == self.ACCEL_RANGE_8G:
                return 8
            elif raw_data == self.ACCEL_RANGE_16G:
                return 16
            else:
                return -1

    def get_accel_data(self, g=False):
        """Gets and returns the X, Y and Z values from the accelerometer.

        If g is True, it will return the data in g
        If g is False, it will return the data in m/s^2
        Returns a dictionary with the measurement results.
        """
        x = self.read_i2c_word(self.ACCEL_XOUT0)
        y = self.read_i2c_word(self.ACCEL_YOUT0)
        z = self.read_i2c_word(self.ACCEL_ZOUT0)

        accel_scale_modifier = None
        accel_range = self.read_accel_range(True)

        if accel_range == self.ACCEL_RANGE_2G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
        elif accel_range == self.ACCEL_RANGE_4G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_4G
        elif accel_range == self.ACCEL_RANGE_8G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_8G
        elif accel_range == self.ACCEL_RANGE_16G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_16G
        else:
            self.log(
                "Unkown range - accel_scale_modifier set to self.ACCEL_SCALE_MODIFIER_2G"
            )
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G

        x = x / accel_scale_modifier
        y = y / accel_scale_modifier
        z = z / accel_scale_modifier

        if g is True:
            return {'x': x, 'y': y, 'z': z}
        elif g is False:
            x = x * self.GRAVITIY_MS2
            y = y * self.GRAVITIY_MS2
            z = z * self.GRAVITIY_MS2
            return {'x': x, 'y': y, 'z': z}

    def set_gyro_range(self, gyro_range):
        """Sets the range of the gyroscope to range.

        gyro_range -- the range to set the gyroscope to. Using a
        pre-defined range is advised.
        """
        # Write the new range to the GYRO_CONFIG register
        self.write_bits(self.GYRO_CONFIG, self.GYRO_CONFIG_FS_SEL_BIT,
                        self.GYRO_CONFIG_FS_SEL_LENGTH, gyro_range)

    def read_gyro_range(self, raw=False):
        """Reads the range the gyroscope is set to.

        If raw is True, it will return the raw value from the GYRO_CONFIG
        register
        If raw is False, it will return an integer: -1, 2, 4, 8 or 16. When it
        returns -1 something went wrong.
        """
        raw_data = self.bus.read_byte_data(self.address, self.GYRO_CONFIG)
        raw_data >>= 3
        raw_data &= 0x03

        if raw is True:
            return raw_data
        else:
            if raw_data == self.GYRO_RANGE_250DEG:
                return 250
            elif raw_data == self.GYRO_RANGE_500DEG:
                return 500
            elif raw_data == self.GYRO_RANGE_1000DEG:
                return 1000
            elif raw_data == self.GYRO_RANGE_2000DEG:
                return 2000
            else:
                return -1

    def get_gyro_data(self):
        """Gets and returns the X, Y and Z values from the gyroscope.

        Returns the read values in a dictionary.
        """
        x = self.read_i2c_word(self.GYRO_XOUT0)
        y = self.read_i2c_word(self.GYRO_YOUT0)
        z = self.read_i2c_word(self.GYRO_ZOUT0)

        gyro_scale_modifier = None
        gyro_range = self.read_gyro_range(True)

        if gyro_range == self.GYRO_RANGE_250DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
        elif gyro_range == self.GYRO_RANGE_500DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
        elif gyro_range == self.GYRO_RANGE_1000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
        elif gyro_range == self.GYRO_RANGE_2000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
        else:
            self.log(
                "Unkown range - gyro_scale_modifier set to self.GYRO_SCALE_MODIFIER_250DEG"
            )
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG

        x = x / gyro_scale_modifier
        y = y / gyro_scale_modifier
        z = z / gyro_scale_modifier

        return {'x': x, 'y': y, 'z': z}

    def get_all_data(self):
        """Reads and returns all the available data."""
        temp = self.get_temp()
        accel = self.get_accel_data()
        gyro = self.get_gyro_data()

        return [accel, gyro, temp]

if __name__ == "__main__":
    mpu = mpu6050(0x68)

    mpu.start()
    time.sleep(5)
    mpu.capturingData=False
