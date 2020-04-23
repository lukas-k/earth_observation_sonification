from microbit import *

def midiControlChange(chan, ctrl, value):
    MIDI_CC = 0xB0
    if chan > 15:
        return
    if (ctrl > 127) or (ctrl < 0):
        return
    if value > 127:
        value = 127
    elif value < 0:
        value = 0
    msg = bytes([MIDI_CC | chan, ctrl, value])
    uart.write(msg)

'''
The preprocess-method fulfills several tasks:
1. Normalize and shift the range of acceleration values to MIDI compatible
values 0..127
2. Introduce a threshold.
3. Switch signs: left/right corresponds to +z/-z, forward/backward to -x/+x
'''
def preprocess(vals):
    max_values = 800
    threshold = 220
    # map x: x >= threshold -> backward (MIDI 0..64)
    result_fb = 64
    result_lr = 64
    if vals[0] >= threshold:
        # a linear map between threshold..max_values and 0..64
        slope = -64/(max_values - threshold)
        result_fb = slope * (min(vals[0], max_values) - max_values)
    elif vals[0] <= -threshold:
        # a linear map between -threshold..-max_values and 64..127
        slope = 63/(threshold-max_values)
        result_fb = slope * (max(vals[0], -max_values) + threshold) + 64
    # map z: z >= threshold -> left (MIDI 0..64)
    if vals[2] >= threshold:
        # a linear map between threshold..max_values and 0..64
        slope = -64/(max_values - threshold)
        result_lr = slope * (min(vals[2], max_values) - max_values)
    elif vals[2] <= -threshold:
        # a linear map between -threshold..-max_values and 64..127
        slope = 63/(threshold-max_values)
        result_lr = slope * (max(vals[2], -max_values) + threshold) + 64
    # MIDI -> integers
    result_fb = int(result_fb)
    result_lr = int(result_lr)
    return result_fb, result_lr


# Start program

# initialise UART for MIDI transmission
uart.init(baudrate=31250, bits=8, parity=None, stop=1, tx=pin0)

# wait for button_b press to initiate calibration
while not button_b.is_pressed():
    sleep(50)

acc_calib = accelerometer.get_values()

# sleep between loops
sleep_time = 40  # ms
while True:
    # recalibration requested?
    if button_b.was_pressed():
        # store new calibration values
        acc_calib = accelerometer.get_values()
    # take accelerometer measurement
    measurement = accelerometer.get_values()
    # empty array to hold the calibrated values
    calibrated_values = [0] * 3
    # subtract calibration values for all components
    for i in range(3):
        calibrated_values[i] = measurement[i] - acc_calib[i]
    # MIDI control values are preprocessed
    velocities = preprocess(calibrated_values)

    midiControlChange(0, 10, velocities[0])
    midiControlChange(0, 11, velocities[1])
    sleep(sleep_time)