import time
import cv2

from defaults.values import *
from enums.ColormapEnum import Colormap


class GuiController:
    def __init__(self,
                 window_title: str = WINDOW_TITLE,
                 width: int = SENSOR_WIDTH,
                 height: int = SENSOR_HEIGHT,
                 scale: int = SCALE,
                 colormap: Colormap = COLORMAP,
                 contrast: float = CONTRAST,
                 blur_radius: int = BLUR_RADIUS,
                 threshold: int = THRESHOLD):
        # Passed parameters
        self.window_title = window_title
        self.width = width
        self.height = height
        self.scale = scale
        self.colormap = colormap
        self.contrast = contrast
        self.blur_radius = blur_radius
        self.threshold = threshold
        
        # Calculated properties
        self.scaled_width = int(self.width * self.scale)
        self.scaled_height = int(self.height * self.scale)
        
        # States
        self.is_hud_visible: bool = HUD_VISIBLE
        self.is_fullscreen: bool = FULLSCREEN
        self.is_inverted: bool = False
        
        # Recording stats
        self.recording_start_time: float = RECORDING_START_TIME
        self.last_snapshot_time: str = LAST_SNAPSHOT_TIME
        self.recording_duration: str = RECORDING_DURATION
        
        # Other
        self._font = FONT
        
        # Initialize the GUI
        cv2.namedWindow(self.window_title, cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(self.window_title, self.scaled_width, self.scaled_height)
        
    def update_recording_stats(self):
        """
        Updates the recording stats.
        """
        self.recording_duration = (time.time() - self.recording_start_time)
        self.recording_duration = time.strftime("%H:%M:%S", time.gmtime(self.recording_duration))
        
    def draw_gui(self, imdata, temp, average_temp, max_temp, min_temp, is_recording, mrow, mcol, lrow, lcol):
        """
        Draws the GUI elements on the thermal image.
        """
        # Apply affects
        img = self.apply_effects(imdata=imdata)
        
        # Apply inversion
        if self.is_inverted:
            img = cv2.bitwise_not(img)

        # Apply colormap
        img = self.apply_colormap(img)

        # Draw crosshairs
        img = self.draw_crosshairs(img)
        
        # Draw temp
        img = self.draw_temp(img, temp)

        # Draw HUD
        if self.is_hud_visible:
            img = self.draw_hud(img, average_temp, is_recording)
        
        # Display floating max temp
        if max_temp > average_temp + self.threshold:
            img = self.draw_max_temp(img, mrow, mcol, max_temp)

        # Display floating min temp
        if min_temp < average_temp - self.threshold:
            img = self.draw_min_temp(img, lrow, lcol, min_temp)
            
        # Update recording stats
        if is_recording:
            self.update_recording_stats()

        return img

    def draw_temp(self, img, temp):
        """
        Draws the temperature onto the image.
        """
        cv2.putText(
            img,
            str(temp)+' C',
            (int(self.scaled_width / 2) + 10, int(self.scaled_height / 2) - 10),
            self._font,
            0.45,
            (0, 0, 0),
            2,
            cv2.LINE_AA)
        cv2.putText(
            img,
            str(temp)+' C',
            (int(self.scaled_width / 2) + 10, int(self.scaled_height / 2) - 10),
            self._font,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA)
        
        return img

    def draw_crosshairs(self, img):
        """
        Draws crosshairs on the image.
        """
        cv2.line(
            img,
            (int(self.scaled_width / 2), int(self.scaled_height / 2) + 20),
            (int(self.scaled_width / 2), int(self.scaled_height / 2) - 20),
            (255, 255, 255),
            2)  # vline
        cv2.line(
            img,
            (int(self.scaled_width / 2) + 20, int(self.scaled_height / 2)),
            (int(self.scaled_width / 2) - 20, int(self.scaled_height / 2)),
            (255, 255, 255),
            2)  # hline

        cv2.line(
            img,
            (int(self.scaled_width / 2), int(self.scaled_height / 2) + 20),
            (int(self.scaled_width / 2), int(self.scaled_height / 2) - 20),
            (0, 0, 0),
            1)  # vline
        cv2.line(
            img,
            (int(self.scaled_width / 2) + 20, int(self.scaled_height / 2)),
            (int(self.scaled_width / 2) - 20, int(self.scaled_height / 2)),
            (0, 0, 0),
            1)  # hline
        
        return img

    def draw_hud(self, img, average_temp, is_recording):
        """
        Draws the HUD onto the image.
        """
        # Display black box for our data
        cv2.rectangle(
            img, 
            (0, 0),
            (160, 134),
            (0, 0, 0),
            -1)
        
        # Put text in the box
        cv2.putText(
            img,
            'Avg Temp: ' + str(average_temp) + ' C',
            (10, 14),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Label Threshold: '+str(self.threshold)+' C',
            (10, 28),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Colormap: '+self.colormap.name,
            (10, 42),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Blur: ' + str(self.blur_radius) + ' ',
            (10, 56),
            self._font, 
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Scaling: '+str(self.scale)+' ',
            (10, 70),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Contrast: '+str(self.contrast)+' ',
            (10, 84),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        cv2.putText(
            img,
            'Snapshot: '+self.last_snapshot_time+' ',
            (10, 98),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        if not is_recording:
            cv2.putText(
                img,
                'Recording: '+str(is_recording),
                (10, 112),
                self._font,
                0.4,
                (200, 200, 200),
                1,
                cv2.LINE_AA)
        else:
            cv2.putText(
                img,
                'Recording: '+self.recording_duration,
                (10, 112),
                self._font,
                0.4,
                (40, 40, 255),
                1,
                cv2.LINE_AA)
            
        cv2.putText(
            img,
            'Inverted: '+str(self.is_inverted),
            (10, 126),
            self._font,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA)
            
        return img
    
    def draw_max_temp(self, img, row: int, col: int, max_temp):
        """
        Draws the maximum temperature point on the image.
        """
        # Draw max temp circle(s)
        cv2.circle(
            img,
            (row*self.scale, col*self.scale),
            5,
            (0, 0, 0),
            2)
        cv2.circle(
            img,
            (row*self.scale, col*self.scale),
            5,
            (0, 0, 255),
            -1)
        
        # Draw max temp label(s)
        cv2.putText(
            img=img,
            text=str(max_temp) + ' C',
            org=((row*self.scale)+10, (col*self.scale)+5),
            fontFace=self._font, 
            fontScale=0.45,
            color=(0, 0, 0), 
            thickness=2, 
            lineType=cv2.LINE_AA)
        
        cv2.putText(
            img=img,
            text=str(max_temp) + ' C',
            org=((row*self.scale)+10, (col*self.scale)+5),
            fontFace=self._font,
            fontScale=0.45,
            color=(0, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA)

        return img
    
    def draw_min_temp(self, img, row: int, col: int, min_temp):
        """
        Draws the minimum temperature point on the image.
        """
        # Draw min temp circle
        cv2.circle(img, (row*self.scale, col*self.scale), 5, (0, 0, 0), 2)
        cv2.circle(img, (row*self.scale, col*self.scale), 5, (255, 0, 0), -1)
        
        # Draw min temp label(s)
        cv2.putText(
            img,
            str(min_temp) + ' C',
            ((row*self.scale)+10,
             (col*self.scale)+5),
            self._font,
            0.45,
            (0, 0, 0),
            2,
            cv2.LINE_AA)
        cv2.putText(
            img,
            str(min_temp) + ' C',
            ((row*self.scale)+10,
             (col*self.scale)+5),
            self._font,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA)

        return img
    
    def apply_colormap(self, img):
        """
        Applies the selected colormap to the image data.
        """
        match Colormap(self.colormap):
            case Colormap.JET:
                img = cv2.applyColorMap(img, cv2.COLORMAP_JET)
            case Colormap.HOT:
                img = cv2.applyColorMap(img, cv2.COLORMAP_HOT)
            case Colormap.MAGMA:
                img = cv2.applyColorMap(img, cv2.COLORMAP_MAGMA)
            case Colormap.INFERNO:
                img = cv2.applyColorMap(img, cv2.COLORMAP_INFERNO)
            case Colormap.PLASMA:
                img = cv2.applyColorMap(img, cv2.COLORMAP_PLASMA)
            case Colormap.BONE:
                img = cv2.applyColorMap(img, cv2.COLORMAP_BONE)
            case Colormap.SPRING:
                img = cv2.applyColorMap(img, cv2.COLORMAP_SPRING)
            case Colormap.AUTUMN:
                img = cv2.applyColorMap(img, cv2.COLORMAP_AUTUMN)
            case Colormap.VIRIDIS:
                img = cv2.applyColorMap(img, cv2.COLORMAP_VIRIDIS)
            case Colormap.PARULA:
                img = cv2.applyColorMap(img, cv2.COLORMAP_PARULA)
            case Colormap.INV_RAINBOW:
                img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        return img

    def apply_effects(self, imdata):
        """
        Applies effects (contrast, blur, upscaling, interpolation, etc.) to the image data.
        """
        # Contrast
        img = cv2.convertScaleAbs(imdata, alpha=self.contrast)
        
        # Bicubic interpolate, upscale and blur
        img = cv2.resize(img, (self.scaled_width, self.scaled_height), interpolation=cv2.INTER_CUBIC)  # Scale up!
        
        # Blur
        if self.blur_radius > 0:
            img = cv2.blur(img, (self.blur_radius, self.blur_radius))

        return img
