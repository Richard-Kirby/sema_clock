import time
import display
import semaphore
import tfl_status

clock_display = display.ClockDisplay()
clock_display.start()

last_time_semaphore = None
semaphore_interval_min = 15

last_time_displayed = None
display_interval_min = 1


# Create some servo objects
left_servo = semaphore.Servo(9, 500, 2500)
right_servo = semaphore.Servo(27, 500, 2500)

# Set up the Semaphore flagger and start the thread.
semaphore_flagger = semaphore.SemaphoreFlagger(left_servo, right_servo, 2, left_offset=22, right_offset=22)
semaphore_flagger.daemon = True
semaphore_flagger.start()

# When first starting up, wait a minute to give the Pi time to get synced with NTP.
time.sleep(60)

while True:

    current_time = time.localtime()

    # checking whether display needs to be updated
    if last_time_displayed is None or (
            current_time.tm_min % display_interval_min == 0 and current_time.tm_min != last_time_displayed):
        clock_display.time_queue.put_nowait(current_time)
        last_time_displayed = current_time.tm_min

    # If first starting up, write the time.  Also write the time if it meets the regular update time.
    # Clear the screen first and then write date and time.
    if last_time_semaphore is None or (
            current_time.tm_min % semaphore_interval_min == 0 and current_time.tm_min != last_time_semaphore):

        time_str = time.strftime("%Hh %Mm ", current_time)
        print(time_str)

        semaphore_flagger.cmd_queue.put_nowait(time_str)

        last_time_semaphore = current_time.tm_min


    time.sleep(2)

