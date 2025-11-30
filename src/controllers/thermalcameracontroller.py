import cv2
import time
import os
import numpy as np

from defaults.values import *
from defaults.keybinds import *

from enums.ColormapEnum import Colormap
from controllers.guiController import GuiController


class ThermalCameraController:
    def __init__(self,
                 device_index: int = VIDEO_DEVICE_INDEX,
                 width: int = SENSOR_WIDTH,
                 height: int = SENSOR_HEIGHT,
                 fps: int = DEVICE_FPS,
                 device_name: str = DEVICE_NAME,
                 media_output_path: str = MEDIA_OUTPUT_PATH):
        # Parameters init
        self._device_index: int = device_index
        self._device_name: str = device_name
        self._width: int = width
        self._height: int = height
        self._fps: int = fps

        # Calculated values init
        self._raw_temp = TEMPERATURE_RAW
        self._temp = TEMPERATURE
        self._max_temp = TEMPERATURE_MAX
        self._min_temp = TEMPERATURE_MIN
        self._avg_temp = TEMPERATURE_AVG
        self._mcol: int = 0
        self._mrow: int = 0
        self._lcol: int = 0
        self._lrow: int = 0

        # Media/recording init
        self._is_recording = not RECORDING
        self._media_output_path: str = media_output_path

        if not os.path.exists(self._media_output_path):
            os.makedirs(self._media_output_path)

        # GUI Init
        self._gui_controller = GuiController(
            width=self._width,
            height=self._height)

        # OpenCV init
        self._cap = None
        self._video_out = None

    @staticmethod
    def print_bindings():
        """
        Print key bindings for the program.
        """
        keybinds = \
            f'Key Bindings:\n' \
            f'{KEY_INCREASE_BLUR} {KEY_DECREASE_BLUR}: Increase/Decrease Blur\n' \
            f'{KEY_INCREASE_FLOATING_HIGH_LOW_TEMP_LABEL_THRESHOLD} {KEY_DECREASE_FLOATING_HIGH_LOW_TEMP_LABEL_THRESHOLD}' \
            f': Floating High and Low Temp Label Threshold\n' \
            f'{KEY_INCREASE_SCALE} {KEY_DECREASE_SCALE}: Change Interpolated scale Note: ' \
            f'This will not change the window size on the Pi\n' \
            f'{KEY_INCREASE_CONTRAST} {KEY_DECREASE_CONTRAST}: Contrast\n' \
            f'{KEY_FULLSCREEN} {KEY_WINDOWED}: Fullscreen Windowed ' \
            f'(note going back to windowed does not seem to work on the Pi!)\n' \
            f'{KEY_RECORD} {KEY_STOP}: Record and Stop\n' \
            f'{KEY_SNAPSHOT} : Snapshot\n' \
            f'{KEY_CYCLE_THROUGH_COLORMAPS} : Cycle through ColorMaps\n' \
            f'{KEY_INVERT} : Invert ColorMap\n' \
            f'{KEY_TOGGLE_HUD} : Toggle HUD\n' \
            f'{KEY_QUIT} : Quit\n' \

        print(keybinds)

    @staticmethod
    def print_credits():
        """
        Print credits/author(s) for the program.
        """
        print('Original Author: Les Wright 21 June 2023')
        print('https://youtube.com/leslaboratory')
        print('Fork Author: Riley Meyerkorth 17 January 2025')
        print('Fork Updater: nagi603 30 November 2025')
        print('A Python program to read, parse and display thermal data from the Topdon TC001/TS001 Thermal cameras!\n')

    def _check_for_key_press(self, key_press: int, img):
        """
        Checks and acts on key presses.
        """
        # BLUR RADIUS
        if key_press == ord(KEY_INCREASE_BLUR):  # Increase blur radius
            self._gui_controller.blur_radius += BLUR_RADIUS_INCREMENT
        if key_press == ord(KEY_DECREASE_BLUR):  # Decrease blur radius
            self._gui_controller.blur_radius -= BLUR_RADIUS_INCREMENT
            if self._gui_controller.blur_radius <= BLUR_RADIUS_MIN:
                self._gui_controller.blur_radius = BLUR_RADIUS_MIN

        # THRESHOLD CONTROL
        if key_press == ord(KEY_INCREASE_FLOATING_HIGH_LOW_TEMP_LABEL_THRESHOLD):  # Increase threshold
            self._gui_controller.threshold += THRESHOLD_INCREMENT
        if key_press == ord(KEY_DECREASE_FLOATING_HIGH_LOW_TEMP_LABEL_THRESHOLD):  # Decrease threashold
            self._gui_controller.threshold -= THRESHOLD_INCREMENT
            if self._gui_controller.threshold <= THRESHOLD_MIN:
                self._gui_controller.threshold = THRESHOLD_MIN

        # SCALE CONTROLS
        if key_press == ord(KEY_INCREASE_SCALE):  # Increase scale
            self._gui_controller.scale += SCALE_INCREMENT
            if self._gui_controller.scale >= SCALE_MAX:
                self._gui_controller.scale = SCALE_MAX
            self._gui_controller.scaled_width = self._width * self._gui_controller.scale
            self._gui_controller.scaled_height = self._height * self._gui_controller.scale
            if not self._gui_controller.is_fullscreen:
                cv2.resizeWindow(self._gui_controller.window_title, self._gui_controller.scaled_width,
                                 self._gui_controller.scaled_height)
        if key_press == ord(KEY_DECREASE_SCALE):  # Decrease scale
            self._gui_controller.scale -= SCALE_INCREMENT
            if self._gui_controller.scale <= SCALE_MIN:
                self._gui_controller.scale = SCALE_MIN
            self._gui_controller.scaled_width = self._width * self._gui_controller.scale
            self._gui_controller.scaled_height = self._height * self._gui_controller.scale
            if not self._gui_controller.is_fullscreen:
                cv2.resizeWindow(self._gui_controller.window_title, self._gui_controller.scaled_width,
                                 self._gui_controller.scaled_height)

        # FULLSCREEN CONTROLS
        if key_press == ord(KEY_FULLSCREEN):  # Enable fullscreen
            self._gui_controller.is_fullscreen = FULLSCREEN
            cv2.namedWindow(self._gui_controller.window_title, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(self._gui_controller.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        if key_press == ord(KEY_WINDOWED):  # Disable fullscreen
            self._gui_controller.is_fullscreen = not FULLSCREEN
            cv2.namedWindow(self._gui_controller.window_title, cv2.WINDOW_GUI_NORMAL)
            cv2.setWindowProperty(self._gui_controller.window_title, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self._gui_controller.window_title, self._gui_controller.scaled_width,
                             self._gui_controller.scaled_height)

        # CONTRAST CONTROLS
        if key_press == ord(KEY_INCREASE_CONTRAST):  # Increase contrast
            self._gui_controller.contrast += CONTRAST_INCREMENT
            self._gui_controller.contrast = round(self._gui_controller.contrast, 1)  # fix round error
            if self._gui_controller.contrast >= CONTRAST_MAX:
                self._gui_controller.contrast = CONTRAST_MAX
        if key_press == ord(KEY_DECREASE_CONTRAST):  # Decrease contrast
            self._gui_controller.contrast -= CONTRAST_INCREMENT
            self._gui_controller.contrast = round(self._gui_controller.contrast, 1)  # fix round error
            if self._gui_controller.contrast <= CONTRAST_MIN:
                self._gui_controller.contrast = CONTRAST_MIN

        # HUD CONTROLS
        if key_press == ord(KEY_TOGGLE_HUD):  # Toggle HUD
            if self._gui_controller.is_hud_visible:
                self._gui_controller.is_hud_visible = not HUD_VISIBLE
            else:
                self._gui_controller.is_hud_visible = HUD_VISIBLE

        # COLOR MAPS
        if key_press == ord(KEY_CYCLE_THROUGH_COLORMAPS):  # Cycle through color maps
            if self._gui_controller.colormap.value + 1 > Colormap.INV_RAINBOW.value:
                self._gui_controller.colormap = Colormap.NONE
            else:
                self._gui_controller.colormap = Colormap(self._gui_controller.colormap.value + 1)
        if key_press == ord(KEY_INVERT):  # Cycle through color maps
            self._gui_controller.is_inverted = not self._gui_controller.is_inverted

        # RECORDING/MEDIA CONTROLS
        if key_press == ord(KEY_RECORD) and not self._is_recording:  # Start recording
            self._video_out = self._record()
            self._is_recording = RECORDING
            self._gui_controller.recording_start_time = time.time()

        if key_press == ord(KEY_STOP):  # Stop recording
            self._is_recording = not RECORDING
            self._gui_controller.recording_duration = RECORDING_DURATION

        if key_press == ord(KEY_SNAPSHOT):  # Take a snapshot
            self._gui_controller.last_snapshot_time = self._snapshot(img)

    def _record(self):
        """
        STart recording video to file.
        """
        current_time_str = time.strftime("%Y%m%d--%H%M%S")
        # do NOT use mp4 here, it is flakey!
        self._video_out = cv2.VideoWriter(
            f"{self._media_output_path}/{current_time_str}-output.avi",
            cv2.VideoWriter_fourcc(*'XVID'),
            self._fps,
            (self._gui_controller.scaled_width, self._gui_controller.scaled_height))
        return self._video_out

    def _snapshot(self, img):
        """
        Takes a snapshot of the current frame.
        """
        # I would put colons in here, but it Win throws a fit if you try and open them!
        current_time_str = time.strftime("%Y%m%d-%H%M%S")
        self._gui_controller.last_snapshot_time = time.strftime("%H:%M:%S")
        cv2.imwrite(f"{self._media_output_path}/{self._device_name}-{current_time_str}.png", img)
        return self._gui_controller.last_snapshot_time

    @staticmethod
    def normalize_temperature(raw_temp: float, d: int = 64, c: float = 273.15) -> float:
        """
        Normalizes/converts the raw temperature data using the formula found by LeoDJ.
        Link: https://www.eevblog.com/forum/thermal-imaging/infiray-and-their-p2-pro-discussion/200/
        """
        return (raw_temp / d) - c

    def calculate_temperature(self, thdata):
        """
        Calculates the (normalized) temperature of the frame.
        """
        raw = self.calculate_raw_temperature(thdata)
        return round(self.normalize_temperature(raw), TEMPERATURE_SIG_DIGITS)

    def calculate_raw_temperature(self, thdata):
        """
        Calculates the raw temperature of the center of the frame.
        """
        return thdata[self._height // 2][self._width // 2]

    def calculate_average_temperature(self, thdata):
        """
        Calculates the average temperature of the frame.
        """
        return round(self.normalize_temperature(thdata.mean()), TEMPERATURE_SIG_DIGITS)

    def calculate_minimum_temperature(self, thdata):
        """
        Calculates the minimum temperature of the frame.
        """
        self._lcol, self._lrow = np.unravel_index(np.argmin(thdata), thdata.shape)
        return round(self.normalize_temperature(thdata[self._lcol][self._lrow]), TEMPERATURE_SIG_DIGITS)

    def calculate_maximum_temperature(self, thdata):
        """
        Calculates the maximum temperature of the frame.
        """
        # Find the max temperature in the frame
        self._mcol, self._mrow = np.unravel_index(np.argmax(thdata), thdata.shape)
        return round(self.normalize_temperature(thdata[self._mcol][self._mrow]), TEMPERATURE_SIG_DIGITS)

    def run(self):
        """
        Runs the main runtime loop for the program.
        """
        # Initialize video
        self._cap = cv2.VideoCapture(self._device_index)

        """
        disable automatic YUY2 -> RGB conversion in OpenCV
        """
        self._cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

        # Start main runtime loop
        while self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                # Split frame into two parts: image data and thermal data
                # We use frame[0] since on Windows this is returned as a 2D array with size [1][<number of pixels>]
                # Other OS are untested
                imdata, thdata = np.array_split(frame[0], 2)

                # First convert the image to YUV
                image_array = np.frombuffer(imdata, dtype=np.uint8)
                if image_array.size != SENSOR_WIDTH * SENSOR_HEIGHT * 2:
                    print(f'\nWrong resolution data from camera, ({image_array.size/2/(1024*1024)} MP,) '
                          f'try other indexes in values.py / startup options')
                    exit(1)
                else:
                    yuv_pic = image_array.reshape((self._height, self._width, 2))
                # Next convert to RGB
                rgb_pic = cv2.cvtColor(yuv_pic, cv2.COLOR_YUV2RGB_YUY2)
                # Assemble the thermal data
                thm_pic = np.frombuffer(thdata, dtype=np.uint16).reshape((self._height, self._width))

                # Now parse the data from the bottom frame and convert to temp!
                # Grab data from the center pixel...
                self._raw_temp = self.calculate_raw_temperature(thm_pic)
                self._temp = self.calculate_temperature(thm_pic)

                # Calculate minimum temperature
                self._min_temp = self.calculate_minimum_temperature(thm_pic)

                # Calculate maximum temperature
                self._max_temp = self.calculate_maximum_temperature(thm_pic)

                # Find the average temperature in the frame
                self._avg_temp = self.calculate_average_temperature(thm_pic)

                # Draw GUI elements
                heatmap = self._gui_controller.draw_gui(
                    imdata=rgb_pic,
                    temp=self._temp,
                    max_temp=self._max_temp,
                    min_temp=self._min_temp,
                    average_temp=self._avg_temp,
                    is_recording=self._is_recording,
                    mcol=self._mcol,
                    mrow=self._mrow,
                    lcol=self._lcol,
                    lrow=self._lrow)

                # Check for recording
                if self._is_recording:
                    self._video_out.write(heatmap)

                # Check for quit and other inputs
                key_press = cv2.waitKey(1)
                if key_press == ord(KEY_QUIT):
                    # Check for recording and close out
                    if self._is_recording:
                        self._video_out.release()
                    return

                self._check_for_key_press(key_press=key_press, img=heatmap)

                # Display image
                cv2.imshow(self._gui_controller.window_title, heatmap)
