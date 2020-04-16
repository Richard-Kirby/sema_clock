import time
import threading
import display
import semaphore
import tfl_status
import met_weather_status


class SemaphoreClock(threading.Thread):

    def __init__(self, semaphore_interval_min, display_interval_min, left_servo_gpio, left_servo_min, left_servo_max,
                 right_servo_gpio, right_servo_min, right_servo_max, left_offset_angle=22, right_offset_angle=22):

        # Init the threading
        threading.Thread.__init__(self)

        # Start the display
        self.clock_display = display.ClockDisplay()
        self.clock_display.start()

        # Some configuration that could go into a Config File.
        self.last_time_semaphore = None
        self.semaphore_interval_min = semaphore_interval_min

        self.last_time_displayed = None
        self.display_interval_min = display_interval_min

        # Create the servo objects
        left_servo = semaphore.Servo(left_servo_gpio, left_servo_min, left_servo_max)
        right_servo = semaphore.Servo(right_servo_gpio, right_servo_min, right_servo_max)

        # Set up the Semaphore flagger and start the thread.
        self.semaphore_flagger = semaphore.SemaphoreFlagger(left_servo, right_servo, 2, left_offset=left_offset_angle,
                                                            right_offset=right_offset_angle)
        self.semaphore_flagger.daemon = True
        self.semaphore_flagger.start()

        # When first starting up, wait a minute to give the Pi time to get synced with NTP.
        # Also need to build up enough entropy for encryption.
        time.sleep(60)

        # TFL status - gets the data for the Tube Lines.
        self.tfl_status_thread = tfl_status.TFL_Status()
        self.tfl_status_thread.daemon = True
        self.tfl_status_thread.start()

        # Met Status - Start up the thread that deals with the Met Status.
        self.met_status_thread = met_weather_status.MetWeatherStatus()
        self.last_forecast = None
        self.forecast_interval_min = 10
        self.met_status_thread.daemon = True
        self.met_status_thread.start()

    # Main method that runs regularly in the thread.
    def run(self):

        while True:
            current_time = time.localtime()

            if self.tfl_status_thread.status_dictionary is not None:
                self.clock_display.tfl_status_queue.put_nowait(self.tfl_status_thread.status_dictionary)

            # checking whether display needs to be updated
            if self.last_time_displayed is None or (
                    current_time.tm_min % self.display_interval_min == 0
                    and current_time.tm_min != self.last_time_displayed):
                self.clock_display.time_queue.put_nowait(current_time)
                self.last_time_displayed = current_time.tm_min

            # checking whether display needs to be updated
            if self.last_forecast is None or (current_time.tm_min % self.forecast_interval_min == 0
                                              and current_time.tm_min != self.last_forecast):

                # Send latest weather forecast if valid
                if len(self.met_status_thread.five_day_forecast) == 5:  # make sure we have a valid 5d forecast
                    self.clock_display.met_forecast_queue.put_nowait(self.met_status_thread.five_day_forecast)
                    self.last_forecast = current_time.tm_min # stays at None until a valid forecast sent

            # If first starting up, write the time.  Also write the time if it meets the regular update time.
            # Clear the screen first and then write date and time.
            if self.last_time_semaphore is None or (
                    current_time.tm_min % self.semaphore_interval_min == 0
                    and current_time.tm_min != self.last_time_semaphore):

                time_str = time.strftime("%Hh %Mm ", current_time)
                print(time_str)

                self.semaphore_flagger.cmd_queue.put_nowait(time_str)

                self.last_time_semaphore = current_time.tm_min

            time.sleep(2)


if __name__ == "__main__":

    print("main program")
    semaphore_clock = SemaphoreClock(15, 1, 9, 500, 2500, 27, 500, 2500, left_offset_angle=22, right_offset_angle=22)
    semaphore_clock.daemon = True
    semaphore_clock.start()

    while True:
        time.sleep(10)
