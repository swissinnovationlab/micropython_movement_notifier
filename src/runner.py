import common
from hcsr04 import HCSR04
from adafruit_soundboard import Soundboard

sensor = None
sensor_timeout = 100
sensor_timestamp = 0
sound = None
last_distance = 0
last_speak_timestamp = 0
last_speak_timeout = 5000

def init():
    print("[RUNNER]: init")
    global sensor, sound
    sensor = HCSR04(trigger_pin=20, echo_pin=21)
    sound = Soundboard(0)

def loop():
    global sensor_timestamp, last_distance, last_speak_timestamp
    if common.millis_passed(sensor_timestamp) >= sensor_timeout:
        sensor_timestamp = common.get_millis()
        distance = sensor.distance_cm()  # max 12ms, 162cm
        if abs(int(distance) - int(last_distance)) > 50:
            last_distance = distance
            if common.millis_passed(last_speak_timestamp) > last_speak_timeout:
                last_speak_timestamp = common.get_millis()
                sound.play(0)
        print('Distance:', distance, 'cm')


def run():
    print("[RUNNER]: run")
    init()
    while True:
        loop()
