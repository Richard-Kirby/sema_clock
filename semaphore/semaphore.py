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

    # Returns the flag angles required for each letter.
    def return_flag_angles(self, code):

        # TO_DO: can't find the word codes, individual letters works OK.
        ret_code = None
        for array_member in self.codes["semaphore_codes"]:
            if array_member['code'] is code:
                ret_code = (array_member["left"], array_member["right"])
                break  # break out of for loop - found it
        return ret_code


# Sets up a Servo and drives it as requested.
class Servo:

    # Details of how to drive the servo.
    def __init__(self, servo_dict):
        self.servo_dict = servo_dict        

    # Drives the servo to a certain angle, including dealing with negative angles.
    # The negative angles lets you deal with a motor that you are using for counterclockwise motion.
    def set_angle(self, angle):

        if angle < 0:
            servo_pulse = self.servo_dict['high_duty'] + (float(angle / 210) * (self.servo_dict['high_duty'] 
                                                                                - self.servo_dict['low_duty']))

        else:
            servo_pulse = int((float(angle / 210) * (self.servo_dict['high_duty'] - self.servo_dict['low_duty'])) 
                              + self.servo_dict['low_duty'])

        pi.set_servo_pulsewidth(self.servo_dict['pwm_pin'], int(servo_pulse))


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
    def set_physical_angles(self, letter, angles):

        # Left is made negative as the servo is inverted.  0 doesn't work as -1 *0 = 0, so set to -1
        if angles[1] is 0:
            physical_left, physical_right = (angles[0], - 1)
        else:
            physical_left, physical_right= (angles[0], -1 * angles[1])

        #print("letter {} L= {} R= {}".format(letter, physical_left, physical_right))

        self.left_servo.set_angle(physical_left)
        self.right_servo.set_angle(physical_right)

    def signal_error(self, char):
        for i in range(5):
            self.set_physical_angles(char, (135 + self.left_offset, 135 + self.right_offset))
            time.sleep(0.5)
            self.set_physical_angles(char, (45 + self.left_offset, 45 + self.right_offset))
            time.sleep(0.5)

    # This is the over-ridden function for the running of the thread.  It just looks for things to pop up
    # in its queue and gets the angles set accordingly.
    def run(self):

        try:

            while True:

                # If Queue isn't empty, deal with the string by processing each letter.
                if not self.cmd_queue.empty():

                    # Get the string
                    string = self.cmd_queue.get_nowait()

                    # Processing each letter.
                    for i in string.upper():
                        ret_code = self.semaphore_codes.return_flag_angles(i)

                        if ret_code is not None:
                            self.set_physical_angles(i, (ret_code[0] + self.left_offset,
                                                         ret_code[1] + self.right_offset))
                            time.sleep(self.pause_time)
                        else:
                            print("Error - couldn't find {}".format(i))
                            self.signal_error(i)

                    time.sleep(self.pause_time)

                time.sleep(self.pause_time)

        except KeyboardInterrupt:
            pi.set_servo_pulsewidth(self.pwm_pin, self.low_duty)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise


if __name__ == "__main__":

    # Create some servo objects
    
    right_servo_def = {'pwm_pin': 27, 'low_duty': 500, 'high_duty': 2500}
    left_servo_def = {'pwm_pin': 9, 'low_duty': 500, 'high_duty': 2500}

    right_sema_servo = Servo(right_servo_def)
    left_sema_servo = Servo(left_servo_def)

    # Set up the Semaphore flagger and start the thread.
    semaphore_flagger = SemaphoreFlagger(left_sema_servo, right_sema_servo, 2, left_offset=22, right_offset=22)
    semaphore_flagger.daemon = True
    semaphore_flagger.start()

    try:
        while True:

            #test_suite = "01234567890Abcdefghijklmnopqrstuvwxyz "
            #semaphore_flagger.cmd_queue.put_nowait("BU")
            #test_suite = "Abcdefghijklmnopqrstuvwxyz 1234567890"
            test_suite = "owxyz"

            for char in test_suite:
                #print(char)
                semaphore_flagger.cmd_queue.put_nowait(char)

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
