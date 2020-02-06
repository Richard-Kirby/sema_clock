import time
import display
import semaphore

clock_display = display.ClockDisplay(1)
clock_display.start()

last_time_displayed = None
semaphore_interval_min = 5

# Create some servo objects
left_servo = semaphore.Servo(27, 500, 2500)
right_servo = semaphore.Servo(9, 500, 2500)

# Set up the Semaphore flagger and start the thread.
semaphore_flagger = semaphore.SemaphoreFlagger(left_servo, right_servo, 0.7)
semaphore_flagger.daemon = True
semaphore_flagger.start()


while True:

    current_time = time.localtime()


    # If first starting up, write the time.  Also write the time if it meets the regular update time.
    # Clear the screen first and then write date and time.
    if last_time_displayed is None or (
            current_time.tm_min % semaphore_interval_min == 0 and current_time.tm_min != last_time_displayed):

        time_str = time.strftime("%Hh %Mm ", current_time)
        print(time_str)

        semaphore_flagger.cmd_queue.put_nowait(time_str)

        last_time_displayed = current_time.tm_min

    time.sleep(2)

