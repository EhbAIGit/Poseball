import numpy as np
import cv2
import mediapipe as mp
import time
import math
import time                                                       
from spherov2 import scanner                             
from spherov2.sphero_edu import SpheroEduAPI                      
from spherov2.types import Color                         
import threading
import queue
#from spherov2.commands import Commands
#from spherov2.helper import to_int
#from spherov2.listeners.power import BatteryVoltageStateThresholds
#from spherov2.commands.api_and_shell import ApiAndShell
#from spherov2.commands.connection import Connection
#from spherov2.commands.drive import Drive
#from spherov2.commands.firmware import Firmware
#from spherov2.commands.io import IO
from spherov2.commands.power import Power
#from spherov2.commands.sensor import Sensor
#from spherov2.commands.system_info import SystemInfo
#from spherov2.controls.v2 import AnimationControl, DriveControl, LedControl, SensorControl, StatsControl, Processors
#from spherov2.toy import ToyV2, Toy, ToySensor
#from spherov2.types import ToyType

class CameraThread(threading.Thread):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.running = True

    def run(self):
        while self.running:
            success, frame = self.cap.read()
                                                                 
class SpheroController:                                           
    def __init__(self, posedetector, cap, pTime):        
        self.toy = None
        self.posedetector = posedetector
        self.cap = cap
        self.pTime = pTime
        self.MODE = "CALIBRATE"
        self.MODE_time = 0
        self.base_heading = 0
        self.toy_direction = "FRONT"
        self.default_hip_knee_dist = 0
        self.default_head_hip_dist = 0
        self.battery_voltage = 4.2
        self.voltage_threshold = 3.8
        self.main_frame = "Image"
        self.timer = 0
        self.timer_limit = 3600
                                
    def discover_toy(self):                                                                 
        time.sleep(1)
        self.toy_role = input("IS BALL CHASER (Y/N): ")
        toy_name = input("ENTER NAME OF BALL: ")
        self.toy_name = "SB-" + toy_name
        try:                                                                         
            self.toy = scanner.find_toy(toy_name=self.toy_name)                             
        except Exception as e:                                                             
            print(f"Error discovering toy: {e}")

                                                                         
    def connect_toy(self):                                                                           
        if self.toy is not None:
            try:                
                return SpheroEduAPI(self.toy)                              
            except Exception as e:                                     
                print(f"Error connecting to toy: {e}")
        else:                            
            print("No toy discovered. Please run discover_toy() first.")
    
    def test_run(self):                         
        self.discover_toy()              
        with self.connect_toy() as api: 
            if api is not None:          
                try:                  
                    api.set_main_led(Color(r=0, g=0, b=255))
                    api.set_speed(60)
                    time.sleep(2)
                    api.set_speed(0)
                except Exception as e:
                    print(f"Error: {e}")
    
    def show_battery_low(self):
        png_data = open('Low_battery.png', 'rb').read()
        image = cv2.imdecode(np.frombuffer(png_data, np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow(self.main_frame, image)
        cv2.waitKey(5)

    def define_window_size(self, window_name, width, height):
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, width, height)

    def state_machine(self):
        with self.connect_toy() as api:
            self.MODE_time = time.time()
            api.set_back_led(Color(255, 0, 0))
            if(self.toy_role == "Y") or (self.toy_role == "y"):
                api.set_main_led(Color(0, 0, 255))
            else:
                api.set_main_led(Color(255, 0, 0))
            previous_wrist_distance = 0
            self.battery_voltage = Power.get_battery_voltage(self.toy)
            self.define_window_size(self.main_frame, 1400, 900)

            exit_condition = False
            timer_start = time.time()
            while exit_condition is False:
                self.timer = time.time() - timer_start
                self.battery_voltage = Power.get_battery_voltage(self.toy)
                print(self.battery_voltage,self.timer)
                exit_condition = (self.timer > self.timer_limit) or (self.battery_voltage < self.voltage_threshold)
                
                success, img = self.cap.read()
                if not success:
                    continue  # Skip this iteration if the frame is empty
                img = self.posedetector.findPose(img)
                lmList = self.posedetector.findPosition(img, draw=False)

                if(lmList is not None and (len(lmList) > 30)):
                    #STATE MACHINE
                    two_wrist_distance = self.posedetector.findDistance(img, 19, 20)
                    time_since_last_mode = int(time.time()-self.MODE_time)
                    if((two_wrist_distance < 20) and (time_since_last_mode > 2) and (previous_wrist_distance > 20)):
                        print(self.MODE, self.MODE_time)
                        
                        if(self.MODE == "START"):
                            self.MODE = "CALIBRATE"
                            self.MODE_time = time.time()
                            api.set_back_led(Color(255, 0, 0))
                        
                        elif(self.MODE == "CALIBRATE"):
                            right_hip_knee_dist = self.posedetector.findDistance(img, 23, 29, draw=False)
                            left_hip_knee_dist = self.posedetector.findDistance(img, 24, 30, draw=False)
                            self.default_hip_knee_dist = (right_hip_knee_dist + left_hip_knee_dist)/2
                            
                            right_head_hip_dist = self.posedetector.findDistance(img, 0, 23, draw=False)
                            left_head_hip_dist = self.posedetector.findDistance(img, 0, 24, draw=False)
                            self.default_head_hip_dist = (right_head_hip_dist + left_head_hip_dist)/2
                            
                            right_head_shoulder_dist = self.posedetector.findDistance(img, 0, 11, draw=False)
                            left_head_shoulder_dist = self.posedetector.findDistance(img, 0, 13, draw=False)
                            self.default_head_shoulder_dist = (right_head_shoulder_dist + left_head_shoulder_dist)/2
             		    
                            right_shoulder_hip_dist = self.posedetector.findDistance(img, 11, 23, draw=False)
                            left_shoulder_hip_dist = self.posedetector.findDistance(img, 13, 24, draw=False)
                            self.default_shoulder_hip_dist = (right_shoulder_hip_dist + left_shoulder_hip_dist)/2

                            self.default_forward_dist = (self.default_head_hip_dist + self.default_head_shoulder_dist + self.default_shoulder_hip_dist)/3
                            
                            self.MODE = "MOVE"
                            self.MODE_time = time.time()
                            api.set_back_led(Color(150, 100, 100))
                            api.set_front_led(Color(0, 0, 0))
                        elif(self.MODE == "MOVE"):
                            api.set_speed(0)
                            api.set_front_led(Color(0, 0, 0))
                            self.MODE = "CALIBRATE"
                            self.MODE_time = time.time()
                            api.set_back_led(Color(255, 0, 0))
                    previous_wrist_distance = two_wrist_distance
                
                    #STATE_ACTION
                    if(self.MODE == "CALIBRATE"):
                        api.set_speed(0)
                        right_hip_angle = self.posedetector.findAngle(img, 0, 23, 29, draw=False)
                        left_hip_angle = self.posedetector.findAngle(img, 0, 24, 30, draw=False)
                        average_bend = int((right_hip_angle + left_hip_angle - 360)/5)
                        if(abs(average_bend)>2):
                            api.set_heading(api.get_heading() + average_bend)
                        self.base_heading = api.get_heading()
                        self.toy_direction = "FRONT"
                    elif(self.MODE == "MOVE"):
                        #LEFT RIGHT
                        right_hip_angle = self.posedetector.findAngle(img, 0, 23, 27, draw=False)
                        left_hip_angle = self.posedetector.findAngle(img, 0, 24, 28, draw=False)
                        average_bend = int((right_hip_angle + left_hip_angle - 360)/2)
                        
                        #BACK
                        right_hip_knee_dist = self.posedetector.findDistance(img, 23, 29, draw=False)
                        left_hip_knee_dist = self.posedetector.findDistance(img, 24, 30, draw=False)
                        hip_knee_dist = (right_hip_knee_dist + left_hip_knee_dist)/2
                        
                        #FRONT
                        right_head_hip_dist = self.posedetector.findDistance(img, 0, 23, draw=False)
                        left_head_hip_dist = self.posedetector.findDistance(img, 0, 24, draw=False)
                        head_hip_dist = (right_head_hip_dist + left_head_hip_dist)/2
                        
                        right_head_shoulder_dist = self.posedetector.findDistance(img, 0, 11, draw=False)
                        left_head_shoulder_dist = self.posedetector.findDistance(img, 0, 13, draw=False)
                        head_shoulder_dist = (right_head_shoulder_dist + left_head_shoulder_dist)/2

                        right_shoulder_hip_dist = self.posedetector.findDistance(img, 11, 23, draw=False)
                        left_shoulder_hip_dist = self.posedetector.findDistance(img, 13, 24, draw=False)
                        shoulder_hip_dist = (right_shoulder_hip_dist + left_shoulder_hip_dist)/2
                            
                        forward_dist = (head_hip_dist + head_shoulder_dist + shoulder_hip_dist)/3
                                                
                        if(average_bend < -15):
                            if (self.toy_direction != "LEFT"):
                                api.set_heading(self.base_heading-90)
                                api.set_front_led(Color(0, 0, 255))
                                #api.set_main_led(Color(255, 0, 100))
                            api.set_speed(50)
                            self.toy_direction = "LEFT"
                        elif(average_bend > 15):
                            if (self.toy_direction != "RIGHT"):
                                api.set_heading(self.base_heading+90)
                                api.set_front_led(Color(0, 0, 255))
                                #api.set_main_led(Color(0, 255, 100))
                            api.set_speed(50)
                            self.toy_direction = "RIGHT"
                        elif(hip_knee_dist < (0.9*self.default_hip_knee_dist)):
                            if (self.toy_direction != "BACK"):
                                api.set_heading(self.base_heading+180)
                                api.set_front_led(Color(255, 0, 0))
                                #api.set_main_led(Color(255, 0, 0))
                            api.set_speed(50)
                            self.toy_direction = "BACK"
                        #elif(head_hip_dist < (0.93*self.default_head_hip_dist)) and (head_shoulder_dist < 0.93*self.default_head_shoulder_dist):
                        elif(forward_dist < 0.9*self.default_forward_dist):
                            if (self.toy_direction != "FRONT"):
                                api.set_heading(self.base_heading)
                                api.set_front_led(Color(0, 255, 0))
                                #api.set_main_led(Color(0, 255, 0))
                            api.set_speed(50)
                            self.toy_direction = "FRONT"
                        else:
                            api.set_speed(0)
                            api.set_front_led(Color(0, 0, 0))
                            #api.set_main_led(Color(0, 0, 0))
                            self.toy_direction = "NONE"

                cTime = time.time()
                fps = 1 / (cTime - self.pTime)
                self.pTime = cTime
                cv2.imshow(self.main_frame, img)
                cv2.waitKey(1)

            self.exit_action()
    
    def exit_action(self):
        if (self.battery_voltage < self.voltage_threshold):
            png_data = open('Low_battery.png', 'rb').read()
        elif (self.timer > self.timer_limit):
            png_data = open('TimesUp.png', 'rb').read()

        image = cv2.imdecode(np.frombuffer(png_data, np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow(self.main_frame, image)
        cv2.waitKey(5)
        

class poseDetector():
 
    def __init__(self, mode=False, upBody=False, smooth=True,
             detectionCon=0.5, trackCon=0.5):

        self.mode = mode
        self.upBody = upBody
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose

        self.pose = self.mpPose.Pose(self.mode
                                 , min_detection_confidence=0.5
                                 , min_tracking_confidence=0.5
                                 )

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                # print(id, lm)
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return self.lmList

    def findDistance(self, img, p1, p2, draw=True):
        x1, y1 = self.lmList[p1][1:]                                                                 
        x2, y2 = self.lmList[p2][1:] 

        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        if(draw==True):
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv2.circle(img, (x1, y1), 10, (0, 0, 255), cv2.FILLED)                                   
            cv2.circle(img, (x1, y1), 15, (0, 0, 255), 2)                                            
            cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)                                   
            cv2.circle(img, (x2, y2), 15, (0, 0, 255), 2)
            cv2.putText(img, str(int(distance)), (x2, y2),cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        return distance
    
    def findAngle(self, img, p1, p2, p3, draw=True):
 
        # Get the landmarks
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        x3, y3 = self.lmList[p3][1:]
 
        # Calculate the Angle
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) -
                             math.atan2(y1 - y2, x1 - x2))
        if angle < 0:
            angle += 360
 
        #print(angle)
 
        # Draw
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv2.line(img, (x3, y3), (x2, y2), (255, 255, 255), 3)
            cv2.circle(img, (x1, y1), 15, (0, 0, 255), 2)
            cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (0, 0, 255), 2)
            cv2.circle(img, (x3, y3), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 15, (0, 0, 255), 2)
            cv2.putText(img, str(int(angle)), (x2 - 50, y2 + 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
        return angle

def main():
    cap = cv2.VideoCapture(2)
    pTime = 0
    detector = poseDetector()

    # Create and start the camera capture thread
    camera_thread = CameraThread(cap)
    camera_thread.start()

    while (True):
        Sphero_obj = SpheroController(detector, cap, pTime)  # Pass the frame queue to your controller
        try:
            Sphero_obj.discover_toy()
            Sphero_obj.state_machine()
        except Exception as e:
            print("Error in connecting to Sphero Toy. Attempting connection again")
        del Sphero_obj

    # When done, stop the camera thread
    camera_thread.running = False
    camera_thread.join()

if __name__ == "__main__":
    main()
