import common
from hcsr04 import HCSR04

sensor = None
sensor_timeout = 100
sensor_timestamp = 0


def init():
    print("[RUNNER]: init")
    global sensor
    sensor = HCSR04(trigger_pin=20, echo_pin=21)


def loop():
    global sensor_timestamp
    if common.millis_passed(sensor_timestamp) >= sensor_timeout:
        sensor_timestamp = common.get_millis()
        distance = sensor.distance_cm()  # max 12ms, 162cm
        print('Distance:', distance, 'cm')


def run():
    print("[RUNNER]: run")
    init()
    while True:
        loop()
