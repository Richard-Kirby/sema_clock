# !/usr/bin/env python3

import pigpio
import threading
import time
import sys
import subprocess
import queue
import os
import json

"""
This bit just gets the pigpiod daemon up and running if it isn't already.
The pigpio daemon accesses the Raspberry Pi GPIO.  
"""
p = subprocess.Popen(['pgrep', '-f', 'pigpiod'], stdout=subprocess.PIPE)
out, err = p.communicate()

if len(out.strip()) == 0:
    os.system("sudo pigpiod")
    time.sleep(3)

pi = pigpio.pi()


# Manages the code to angles translation.
class SemaphoreCodes:

    # Reads all the codes from the file.
    def __init__(self):
        with open('./semaphore/semaphore_codes.json') as json_semaphore_codes:
            self.codes = json.load(json_semaphore_codes)

        for code in self.codes["semaphore_codes"]:
            pass
            #print(code["code"], code["left"], code["right"])

    # Returns the flag angles required for each letter.
    def return_flag_angles(self, code):

        # TO_DO: can't find the word codes, individual letters works OK.
        ret_code = None
        for array_member in self.codes["semaphore_codes"]:
            #print(array_member['code'])
            if array_member['code'] is code:
                ret_code = (array_member["left"], array_member["right"])
                break # break out of for loop - found it
        return ret_code


# Sets up a Servo and drives it as requested.
class Servo:

    # Details of how to drive the servo.
    def __init__(self, pwm_pin, low_duty, high_duty):
        self.pwm_pin = pwm_pin
        self.low_duty = low_duty
        self.high_duty = high_duty

    # Drives the servo to a certain angle, including dealing with negative angles.
    # The negative angles lets you deal with a motor that you are using for counterclockwise motion.
    def set_angle(self, angle):

        if angle < 0:
            servo_pulse = self.high_duty + (float(angle / 210) * (self.high_duty - self.low_duty))

        else:
            servo_pulse = int((float(angle / 210) * (self.high_duty - self.low_duty)) + self.low_duty)

        #print(angle, servo_pulse)
        pi.set_servo_pulsewidth(self.pwm_pin, int(servo_pulse))


# The flagger, which translates words into flag movements.  Monitors a queue of what needs to be sent.
class SemaphoreFlagger(threading.Thread):

    def __init__(self, left_servo, right_servo, pause_time, left_offset=0, right_offset=0 ):
        threading.Thread.__init__(self)

        self.left_servo = left_servo
        self.right_servo = right_servo
        self.left_offset = left_offset
        self.right_offset = right_offset
        self.pause_time = pause_time
        self.cmd_queue = queue.Queue()
        self.semaphore_codes = SemaphoreCodes()

    # calculates the physical angles to use - Left is negative as the servo is inverted
    @staticmethod
    def get_physical_angles(angles):

        # Left is made negative as the servo is inverted.  0 doesn't work as -1 *0 = 0, so set to -1
        if angles[1] is 0:
            ret_code = (angles[0], - 1)
        else:
            ret_code = (angles[0], -1 * angles[1])

        return ret_code

    # This is the over-ridden function for the running of the thread.  It just looks for things to pop up
    # in its queue and gets the angles set accordingly.
    def run(self):

        try:

            while True:

                # If Queue isn't empty, deal with the string by processing each letter.
                if not self.cmd_queue.empty():

                    # Get the string
                    string = self.cmd_queue.get_nowait()
                    print(string)

                    # Processing each letter.
                    for i in string.upper():
                        ret_code = self.semaphore_codes.return_flag_angles(i)
                        if ret_code is not None:
                            print(i, "RL", ret_code[1], ret_code[0], )


                            left_angle = ret_code[0] + self.left_offset
                            right_angle = ret_code[1] + self.right_offset

                            (physical_left, physical_right) = self.get_physical_angles((left_angle, right_angle))

                            self.left_servo.set_angle(physical_left)
                            self.right_servo.set_angle(physical_right)
                            time.sleep(self.pause_time)

                    # Need to finish off each string with a rest.  A space is the same as a rest.
                    #ret_code = self.get_physical_angles(self.semaphore_codes.return_flag_angles(' '))
                    #left_angle = ret_code[0] + self.left_offset
                    #right_angle = ret_code[1] + self.right_offset
                    #print("rest", "LR", left_angle, right_angle)

                    #self.left_servo.set_angle(left_angle)
                    #self.right_servo.set_angle(right_angle)
                    time.sleep(self.pause_time)

                time.sleep(self.pause_time)

        except KeyboardInterrupt:
            pi.set_servo_pulsewidth(self.pwm_pin, self.low_duty)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise


if __name__ == "__main__":

    # Create some servo objects
    right_servo = Servo(27, 500, 2500)
    left_servo = Servo(9, 500, 2500)

    # Set up the Semaphore flagger and start the thread.
    semaphore_flagger = SemaphoreFlagger(left_servo, right_servo, 5, left_offset=30, right_offset=30)
    semaphore_flagger.daemon = True
    semaphore_flagger.start()

    try:
        while True:

            #semaphore_flagger.cmd_queue.put_nowait("BU")
            semaphore_flagger.cmd_queue.put_nowait("0 1 2 3 4 5 6 7 8 9")
            #semaphore_flagger.cmd_queue.put_nowait("abcdefghijklmnopqrstuvxyz0123456789")

            time.sleep(1)


    except KeyboardInterrupt:

        print("Quitting the program due to Ctrl-C")

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    finally:
        print("\nTidying up")
        pi.stop()
