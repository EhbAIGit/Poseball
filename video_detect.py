import queue
import time
import cv2
import numpy as np
import socket
import threading

class server_messenger():
    def __init__(self):
        self.server_ip = '192.168.0.43'  # Replace with Laptop 1's IP address
        self.server_port = 12345  # Choose a port number
        self.server_socket = None
        self.running = True
        self.received_message = queue.Queue() 
        self.send_message = queue.Queue()
        self.received_message1 = queue.Queue() 
        self.send_message1 = queue.Queue()
        self.client_socket1 = None
        self.client_address1 = None
        self.received_message2 = queue.Queue() 
        self.send_message2 = queue.Queue()
        self.client_socket2 = None
        self.client_address2 = None

    def connect_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(2)
        print(f"Server listening on {self.server_ip}:{self.server_port}")

    def connect_client(self):
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection from {client_address}")
            if(self.client_socket1 is None):
                self.client_socket1 = client_socket
                self.client_address1 = client_address
            else:
                self.client_socket2 = client_socket
                self.client_address2 = client_address

    def receiver1(self):
        while self.running:
            if self.client_socket1 is None:
                time.sleep(1)
                continue
            message = self.client_socket1.recv(1024).decode()
            self.received_message1.put(message)
            time.sleep(1)
   
    def sender1(self):
        while self.running:
            if self.client_socket1 is None:
                time.sleep(1)
                continue
            if self.send_message1.empty() is False:
                message = self.send_message1.get()
                self.client_socket1.send(message.encode())
            time.sleep(1)
        
    def receiver2(self):
        while self.running:
            if self.client_socket2 is None:
                time.sleep(1)
                continue
            message = self.client_socket2.recv(1024).decode()
            self.received_message2.put(message)
            time.sleep(1)

    def sender2(self):
        while self.running:
            if self.client_socket2 is None:
                time.sleep(1)
                continue
            if self.send_message2.empty() is False:
                message = self.send_message2.get()
                self.client_socket2.send(message.encode())
            time.sleep(1)

class detected_objects:
    def __init__(self,object_name,x,y,w,h,contour):
        self.object_name = object_name
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.contour = contour

class game_referee:
    def __init__(self):
        self.MODE = "CONNECT CLIENT"
        self.CLIENT1_MODE = "CONNECT CLIENT"
        self.CLIENT2_MODE = "CONNECT CLIENT"
        self.toy_disconnect_flag = False
        self.winner = "TIE"
        self.collision_threshold = 1.07
        self.server_ip = '192.168.0.43'  # Replace with Laptop 1's IP address
        self.server_port = 12345  # Choose a port number
        self.server_socket = None
        self.messenger = None
        self.game_start_time = 0

    def connect_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(1)
        print(f"Server listening on {self.server_ip}:{self.server_port}")

    def calculate_distance(self, object1, object2):
        return np.sqrt((object1.x - object2.x)**2 + (object1.y - object2.y)**2)

    def check_escape(self, object1, object2):
        if(object1 is not None) and (object2 is not None) :
            distance = self.calculate_distance(object1, object2)
            if (distance < (min(object1.w, object1.h)/2 +min(object2.w, object2.h)/2)):
                "game over by escape"
                self.MODE = "GAME OVER"
                print("STATUS REFEREE: GAME WON BY ESCAPER")
                self.CLIENT1_MODE = "GAME OVER"
                self.CLIENT2_MODE = "GAME OVER"
                self.winner = "ESCAPER"
                return True
        return False

    def check_collision(self, object1, object2):
        if(object1 is not None) and (object2 is not None):
            distance = self.calculate_distance(object1, object2)
            if (distance < self.collision_threshold*(object1.w+object1.h+object2.w+object2.h)/4):
                "game over by collision"
                self.MODE = "GAME OVER"
                print("STATUS REFEREE: GAME WON BY CHASER")
                self.CLIENT1_MODE = "GAME OVER"
                self.CLIENT2_MODE = "GAME OVER"
                self.winner = "CHASER"
                return True
        return False

    def check_timer(self):
        if(time.time() - self.game_start_time > 300):
            self.MODE = "GAME OVER"
            print("STATUS REFEREE: GAME TIED BY TIMER EXPIRY")
            self.CLIENT1_MODE = "GAME OVER"
            self.CLIENT2_MODE = "GAME OVER"
            self.winner = "TIE"
            return True
        return False

    def check_client1(self):
        received_message1 = None
        if self.messenger.received_message1.empty() is False:
            received_message1 = self.messenger.received_message1.get()
            if(received_message1 == "CLIENT 1: TOY DISCONNECT") or (self.toy_disconnect_flag == True):
                self.toy_disconnect_flag = True
                return

        if(self.CLIENT1_MODE == "CONNECT CLIENT"):
            if(received_message1 == "CLIENT 1: CONNECTED"):
                self.messenger.received_message.put(received_message1)
                print("STATUS: CLIENT 1 CONNECTED")
            elif(received_message1 == "REFEREE: BOTH CLIENTS CONNECTED"):
                self.CLIENT1_MODE = "ESTABLISH TOY"
                ball_mode = "BEGIN TOY CONNECTION"
                self.messenger.send_message1.put(ball_mode)
        
        elif(self.CLIENT1_MODE == "ESTABLISH TOY"):
            if(received_message1 == "CLIENT 1: DECIDE ROLE"):
                self.messenger.received_message.put(received_message1)
            elif(received_message1 == "REFEREE: ROLE DECIDED CHASER"):
                ball_mode = "CHASER"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "REFEREE: ROLE DECIDED ESCAPER"):
                ball_mode = "ESCAPER"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "CLIENT 1: PLAYER ROLE DECIDED"):
                self.messenger.received_message.put(received_message1)
            elif(received_message1 == "86B7") or (received_message1 == "7740") or (received_message1 == "62C3")or (received_message1 == "0EF1")or (received_message1 == "E30C") or (received_message1 == "27A5"):
                self.messenger.send_message1.put(received_message1)
            elif(received_message1 == "CLIENT 1: TOY CONNECTED"):
                self.messenger.received_message.put("CLIENT 1: TOY CONNECTED")
            elif(received_message1 == "REFEREE: BOTH TOYS CONNECTED"):
                ball_mode = "BALL READY"
                self.CLIENT1_MODE = "NEW GAME"
                self.messenger.send_message1.put(ball_mode)
        
        elif(self.CLIENT1_MODE == "NEW GAME"):
            if(received_message1 == "CLIENT 1: WAITING TO START"):
                self.messenger.received_message.put("CLIENT 1: WAITING TO START")
            elif(received_message1 == "REFEREE: NEW GAME APPROVED"):
                ball_mode = "GAME STARTED"
                self.CLIENT1_MODE = "GAME STARTED"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "REFEREE: NEW GAME NOT APPROVED"):
                self.CLIENT1_MODE = "GAME OVER"
        
        elif(self.CLIENT1_MODE == "GAME STARTED"):
            if(received_message1 == "CLIENT 1: FIRST CALIBRATION OVER"):
                self.messenger.received_message.put("CLIENT 1: FIRST CALIBRATION OVER")
            elif(received_message1 == "REFEREE: ALLOWED MOVE"):
                ball_mode = "MOVE"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "REFEREE: MOVE NOT APPROVED"):
                self.CLIENT1_MODE = "GAME OVER"
            
            elif(received_message1 == "CLIENT 1: LOW BATTERY"):
                print("STATUS CLIENT 1: BATTERY LOW")
                self.messenger.received_message.put("CLIENT 1: LOW BATTERY")
            elif(received_message1 == "REFEREE: LOW BATTERY"):
                self.CLIENT1_MODE = "GAME STOP"

        elif(self.CLIENT1_MODE == "GAME OVER"):
            ball_mode = "GAME OVER"
            self.messenger.send_message1.put(ball_mode)
            self.CLIENT1_MODE = "GAME RESTART"
        
        elif(self.CLIENT1_MODE == "GAME RESTART"):
            if(received_message1 == "CLIENT 1: WAITING TO RESTART"):
                self.messenger.received_message.put("CLIENT 1: WAITING TO RESTART")
            elif(received_message1 == "REFEREE: RESTART APPROVED"):
                self.CLIENT1_MODE = "NEW GAME"
                ball_mode = "BALL READY"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "REFEREE: RECONNECT APPROVED"):
                self.CLIENT1_MODE = "ESTABLISH TOY"
                ball_mode = "ESTABLISH TOY"
                self.messenger.send_message1.put(ball_mode)
            elif(received_message1 == "REFEREE: RECONNECT NOT APPROVED"):
                self.CLIENT1_MODE = "GAME OVER"

        if(self.CLIENT1_MODE == "GAME STOP"):
            self.toy_disconnect_flag = True

    def check_client2(self):
        received_message2 = None
        if self.messenger.received_message2.empty() is False:
            received_message2 = self.messenger.received_message2.get()
            if(received_message2 == "CLIENT 2: TOY DISCONNECT") or (self.toy_disconnect_flag == True):
                self.toy_disconnect_flag = True
                return

        if(self.CLIENT2_MODE == "CONNECT CLIENT"):
            if(received_message2 == "CLIENT 2: CONNECTED"):
                self.messenger.received_message.put(received_message2)
                print("STATUS: CLIENT 2 CONNECTED")
            elif(received_message2 == "REFEREE: BOTH CLIENTS CONNECTED"):
                self.CLIENT2_MODE = "ESTABLISH TOY"
                ball_mode = "BEGIN TOY CONNECTION"
                self.messenger.send_message2.put(ball_mode)
        
        elif(self.CLIENT2_MODE == "ESTABLISH TOY"):
            if(received_message2 == "CLIENT 2: DECIDE ROLE"):
                self.messenger.received_message.put(received_message2)
            elif(received_message2 == "REFEREE: ROLE DECIDED CHASER"):
                ball_mode = "CHASER"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "REFEREE: ROLE DECIDED ESCAPER"):
                ball_mode = "ESCAPER"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "CLIENT 2: PLAYER ROLE DECIDED"):
                self.messenger.received_message.put(received_message2)
            elif(received_message2 == "86B7") or (received_message2 == "7740") or (received_message2 == "62C3")or (received_message2 == "0EF1")or (received_message2 == "E30C") or (received_message2 == "27A5") or (received_message2 == "27A5"):
                self.messenger.send_message2.put(received_message2)
            elif(received_message2 == "CLIENT 2: TOY CONNECTED"):
                self.messenger.received_message.put("CLIENT 2: TOY CONNECTED")
            elif(received_message2 == "REFEREE: BOTH TOYS CONNECTED"):
                ball_mode = "BALL READY"
                self.CLIENT2_MODE = "NEW GAME"
                self.messenger.send_message2.put(ball_mode)

        elif(self.CLIENT2_MODE == "NEW GAME"):
            if(received_message2 == "CLIENT 2: WAITING TO START"):
                self.messenger.received_message.put("CLIENT 2: WAITING TO START")
            elif(received_message2 == "REFEREE: NEW GAME APPROVED"):
                ball_mode = "GAME STARTED"
                self.CLIENT2_MODE = "GAME STARTED"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "REFEREE: NEW GAME NOT APPROVED"):
                self.CLIENT2_MODE = "GAME OVER"
        
        elif(self.CLIENT2_MODE == "GAME STARTED"):
            if(received_message2 == "CLIENT 2: FIRST CALIBRATION OVER"):
                self.messenger.received_message.put("CLIENT 2: FIRST CALIBRATION OVER")
            elif(received_message2 == "REFEREE: ALLOWED MOVE"):
                ball_mode = "MOVE"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "REFEREE: MOVE NOT APPROVED"):
                self.CLIENT2_MODE = "GAME OVER"
            
            elif(received_message2 == "CLIENT 2: LOW BATTERY"):
                print("STATUS CLIENT 2: BATTERY LOW")
                self.messenger.received_message.put("CLIENT 2: LOW BATTERY")
            elif(received_message2 == "REFEREE: LOW BATTERY"):
                self.CLIENT2_MODE = "GAME STOP"

        elif(self.CLIENT2_MODE == "GAME OVER"):
            ball_mode = "GAME OVER"
            self.messenger.send_message2.put(ball_mode)
            self.CLIENT2_MODE = "GAME RESTART"
        
        elif(self.CLIENT2_MODE == "GAME RESTART"):
            if(received_message2 == "CLIENT 2: WAITING TO RESTART"):
                self.messenger.received_message.put("CLIENT 2: WAITING TO RESTART")
            elif(received_message2 == "REFEREE: RESTART APPROVED"):
                self.CLIENT2_MODE = "NEW GAME"
                ball_mode = "BALL READY"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "REFEREE: RECONNECT APPROVED"):
                self.CLIENT2_MODE = "ESTABLISH TOY"
                ball_mode = "ESTABLISH TOY"
                self.messenger.send_message2.put(ball_mode)
            elif(received_message2 == "REFEREE: RECONNECT NOT APPROVED"):
                self.CLIENT2_MODE = "GAME OVER"

        if(self.CLIENT2_MODE == "GAME STOP"):
            self.toy_disconnect_flag = True
    
    def game_advance(self):
        received_message = None
        if self.messenger.received_message.empty() is False:
            received_message = self.messenger.received_message.get()
        if(self.toy_disconnect_flag == True):
            print("STATUS REFEREE: TOYS ARE BEING DISCONNECTED DUE TO ISSUES AT CLIENT END")
            time.sleep(5)
            self.messenger.send_message1.queue.clear()
            self.messenger.received_message1.queue.clear()
            self.messenger.send_message2.queue.clear()
            self.messenger.received_message2.queue.clear()
            self.CLIENT1_MODE = "ESTABLISH TOY"
            self.CLIENT2_MODE = "ESTABLISH TOY"
            self.MODE = "ESTABLISH TOY"
            message = "ESTABLISH TOY"
            self.messenger.client_socket1.send(message.encode())
            self.messenger.client_socket2.send(message.encode())
                
            is_connect = input("REFEREE PROMPT: DO YOU WANT TO CONNECT TOYS AGAIN ? (Y/N): ")
            if(is_connect == "y") or (is_connect == "Y"):
                print("STATUS REFEREE: REINITIATING CONNECTION")
                time.sleep(5) 
                self.messenger.send_message1.queue.clear()
                self.messenger.received_message1.queue.clear()
                self.messenger.send_message2.queue.clear()
                self.messenger.received_message2.queue.clear()

                message = "BEGIN TOY CONNECTION"
                self.messenger.client_socket1.send(message.encode())
                self.messenger.client_socket2.send(message.encode())
                self.toy_disconnect_flag = False
            return

        elif(self.MODE == "CONNECT CLIENT"):
            if(received_message == "CLIENT 1: CONNECTED") or (received_message == "CLIENT 2: CONNECTED"):
                self.MODE = "CONNECT ANOTHER CLIENT" 
                print("STATUS REFEREE: ", received_message, " WAITING FOR ANOTHER CLIENT")
        elif(self.MODE == "CONNECT ANOTHER CLIENT"):
            if(received_message == "CLIENT 1: CONNECTED") or (received_message == "CLIENT 2: CONNECTED"):
                self.messenger.received_message1.put("REFEREE: BOTH CLIENTS CONNECTED")
                self.messenger.received_message2.put("REFEREE: BOTH CLIENTS CONNECTED")
                self.MODE = "ESTABLISH TOY" 
                print("STATUS REFEREE: BOTH CLIENTS CONNECTED")
        
        elif(self.MODE == "ESTABLISH TOY"):
            if(received_message == "CLIENT 1: DECIDE ROLE") or (received_message == "CLIENT 2: DECIDE ROLE"):
                self.MODE = "ESTABLISH ANOTHER TOY"
                print("STATUS REFEREE: WAITING FOR ANOTHER CLIENT")
        elif(self.MODE == "ESTABLISH ANOTHER TOY"):
            if(received_message == "CLIENT 1: DECIDE ROLE") or (received_message == "CLIENT 2: DECIDE ROLE"):
                is_chaser = input("PROMPT REFEREE: MAKE CLIENT 1 CHASER? (Y/N): ")
                if (is_chaser == "y") or (is_chaser == "Y"):
                    self.messenger.received_message1.put("REFEREE: ROLE DECIDED CHASER")
                    self.messenger.received_message2.put("REFEREE: ROLE DECIDED ESCAPER")
                else:
                    self.messenger.received_message1.put("REFEREE: ROLE DECIDED ESCAPER")
                    self.messenger.received_message2.put("REFEREE: ROLE DECIDED CHASER")
                self.MODE = "TOY NAME"

        elif(self.MODE == "TOY NAME"):
            if (received_message == "CLIENT 1: PLAYER ROLE DECIDED") or (received_message == "CLIENT 2: PLAYER ROLE DECIDED"):
                self.MODE = "ANOTHER TOY NAME"
        elif(self.MODE == "ANOTHER TOY NAME"):
            if (received_message == "CLIENT 1: PLAYER ROLE DECIDED") or (received_message == "CLIENT 2: PLAYER ROLE DECIDED"):
                toy1_name = input("PROMPT REFEREE: ENTER TOY1 NAME: ")
                self.messenger.received_message1.put(toy1_name)
                toy2_name = input("PROMPT REFEREE: ENTER TOY2 NAME: ")
                self.messenger.received_message2.put(toy2_name)
                self.MODE = "CHECK TOY"
        
        elif(self.MODE == "CHECK TOY"):
            if(received_message == "CLIENT 1: TOY CONNECTED") or (received_message == "CLIENT 2: TOY CONNECTED"):
                self.MODE = "CHECK ANOTHER TOY"
        elif(self.MODE == "CHECK ANOTHER TOY"):
            if(received_message == "CLIENT 1: TOY CONNECTED") or (received_message == "CLIENT 2: TOY CONNECTED"):
                self.messenger.received_message1.put("REFEREE: BOTH TOYS CONNECTED")
                self.messenger.received_message2.put("REFEREE: BOTH TOYS CONNECTED")
                self.MODE = "NEW GAME"
        
        elif(self.MODE == "NEW GAME"):
            if(received_message == "CLIENT 1: WAITING TO START") or (received_message == "CLIENT 2: WAITING TO START"):
                print("STATUS REFEREE: ", received_message, " WAITING FOR ANOTHER CLIENT")
                self.MODE = "ANOTHER NEW GAME"
        elif(self.MODE == "ANOTHER NEW GAME"):
            if(received_message == "CLIENT 1: WAITING TO START") or (received_message == "CLIENT 2: WAITING TO START"):
                print("STATUS REFEREE: BOTH CLIENTS WAITING TO START")
                is_new = input("PROMPT REFEREE: DO YOU WANNA START NEW GAME? (Y/N): ")
                if(is_new == "Y") or (is_new == "y"):
                    self.messenger.received_message1.put("REFEREE: NEW GAME APPROVED")
                    self.messenger.received_message2.put("REFEREE: NEW GAME APPROVED")
                    self.MODE = "FIRST CALIBRATION"
                    print("STATUS REFEREE: WAITING FOR FIRST CALIBRATION OF BOTH TOYS")
                else:
                    self.messenger.received_message1.put("REFEREE: NEW GAME NOT APPROVED")
                    self.messenger.received_message2.put("REFEREE: NEW GAME NOT APPROVED")
                    self.MODE = "GAME OVER"
                    
        elif(self.MODE == "FIRST CALIBRATION"):
            if(received_message == "CLIENT 1: FIRST CALIBRATION OVER") or (received_message == "CLIENT 2: FIRST CALIBRATION OVER"):
                self.MODE = "ANOTHER FIRST CALIBRATION"
                print("STATUS REFEREE: ", received_message, " WAITING FOR ANOTHER CLIENT")
        elif(self.MODE == "ANOTHER FIRST CALIBRATION"):
            if(received_message == "CLIENT 1: FIRST CALIBRATION OVER") or (received_message == "CLIENT 2: FIRST CALIBRATION OVER"):
                print("STATUS REFEREE: FIRST CALIBRATION OVER FOR BOTH CLIENTS")
                is_move = input("DO YOU WANT ALLOW PLAYERS TO MOVE? (Y/N): ")
                if (is_move == "Y") or (is_move == "y"):
                    print("STATUS REFEREE:: THE GAME BEGINS")
                    self.game_start_time = time.time()
                    self.messenger.received_message1.put("REFEREE: ALLOWED MOVE")
                    self.messenger.received_message2.put("REFEREE: ALLOWED MOVE")
                    self.MODE = "GAME STARTED"
                else:
                    self.messenger.received_message1.put("REFEREE: MOVE NOT APPROVED")
                    self.messenger.received_message2.put("REFERER: MOVE NOT APPROVED")
                    print("STATUS REFEREE: GAME START NOT APPROVED")
                    self.MODE = "GAME OVER"

        elif(self.MODE == "GAME STARTED"):
            if(received_message == "CLIENT 1: LOW BATTERY") or (received_message == "CLIENT 2: LOW BATTERY"):
                print("STATUS REFEREE: BATTERY LOW")
                self.messenger.received_message1.put("REFEREE: LOW BATTERY")
                self.messenger.received_message2.put("REFEREE: LOW BATTERY")
                self.MODE = "GAME STOP"

        elif(self.MODE == "GAME OVER"):
            print("STATUS REFEREE: GAME FINISHED")
            self.MODE = "GAME RESTART"
        
        elif(self.MODE == "GAME RESTART"):
            if(received_message == "CLIENT 1: WAITING TO RESTART") or (received_message == "CLIENT 2: WAITING TO RESTART"):
                self.MODE = "ANOTHER GAME RESTART"
        elif(self.MODE == "ANOTHER GAME RESTART"):
            if(received_message == "CLIENT 1: WAITING TO RESTART") or (received_message == "CLIENT 2: WAITING TO RESTART"):
                is_end = input("PROMPT REFEREE: DO YOU WANT TO RESTART GAME? (Y/N): ")
                if (is_end == "Y") or (is_end == "y"):
                    self.messenger.received_message1.put("REFEREE: RESTART APPROVED")
                    self.messenger.received_message2.put("REFEREE: RESTART APPROVED")
                    self.MODE = "NEW GAME"
                    print("STATUS REFEREE: RESTART INITIATED")
                else:
                    is_end = input("PROMPT REFEREE: DO YOU WANT TO RECONNECT BALLS (Y/N): ")
                    if (is_end == "Y") or (is_end == "y"):
                        self.messenger.received_message1.put("REFEREE: RECONNECT APPROVED")
                        self.messenger.received_message2.put("REFEREE: RECONNECT APPROVED")
                        self.MODE = "ESTABLISH TOY"
                        print("STATUS REFEREE: TOY RECONNECT INITIATED")
                    else:
                        self.messenger.received_message1.put("REFEREE: RECONNECT NOT APPROVED")
                        self.messenger.received_message2.put("REFEREE: RECONNECT NOT APPROVED")
                        print("STATUS REFEREE: TOY RECONNECT NOT APPROVED")
                        self.MODE = "GAME OVER"

        if(self.MODE == "GAME STOP"):
            print("STATUS REFEREE: TOY RECONNECT INITIATED")
            self.toy_disconnect_flag = True

class video_capture:
    def __init__(self, cap):
        self.cap = cap
        self.lower_blue = np.array([92, 20, 160])
        self.upper_blue = np.array([110, 255, 255])
        self.lower_red = np.array([121, 20, 160])
        self.upper_red = np.array([165, 255, 255])
        self.lower_green = np.array([20, 100, 0])
        self.upper_green = np.array([56, 255, 255])
        self.roi_x = 25
        self.roi_y = 14
        self.roi_width = 602
        self.roi_height = 423
        self.bright_fact = 2.50
        self.min_area = 100
        self.max_area = 600

    def brighten_frame(self):
        self.frame = self.frame*self.bright_fact
        self.frame = np.clip(self.frame, 0, 255).astype(np.uint8)
        cv2.rectangle(self.frame, (self.roi_x, self.roi_y), (self.roi_x + self.roi_width, self.roi_y + self.roi_height), (255, 0, 0), 2)

    def find_object(self, object_name):
        if(object_name == "CHASER"):
            lower_limit = self.lower_blue
            upper_limit = self.upper_blue
        if(object_name == "ESCAPER"):
            lower_limit = self.lower_red
            upper_limit = self.upper_red
        if(object_name == "EXIT1") or (object_name == "EXIT2"):
            lower_limit = self.lower_green
            upper_limit = self.upper_green

        hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        
        mask = cv2.inRange(hsv_frame, lower_limit, upper_limit)
        masked_frame = cv2.bitwise_and(self.frame, self.frame, mask=mask)
        
        roi_frame = masked_frame[self.roi_y:self.roi_y + self.roi_height, self.roi_x:self.roi_x + self.roi_width]
        
        contours, _ = cv2.findContours(mask[self.roi_y:self.roi_y + self.roi_height, self.roi_x:self.roi_x + self.roi_width].copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        filtered_contours = [contour for contour in contours if self.min_area < cv2.contourArea(contour) < self.max_area]
        
        if(len(filtered_contours)>0):
            if(object_name == "EXIT2") and len(filtered_contours)>1:
                x, y, w, h = cv2.boundingRect(filtered_contours[1])
                detected_object = detected_objects(object_name, x, y, w, h, filtered_contours[1])
            else:
                x, y, w, h = cv2.boundingRect(filtered_contours[0])
                detected_object = detected_objects(object_name, x, y, w, h, filtered_contours[0]) 
            self.display_object(detected_object)
            return detected_object
        else:
            return None

    def display_object(self, object1):
        center = (object1.x + self.roi_x + object1.w // 2, object1.y+ self.roi_y  + object1.h // 2)
        cv2.rectangle(self.frame, (object1.x + self.roi_x , object1.y+ self.roi_y ), (object1.x + self.roi_x +object1.w, object1.y + self.roi_y +object1.h), (0, 255, 0), 2)
        size_text = f'Size: {cv2.contourArea(object1.contour):.2f}'
        cv2.putText(self.frame, size_text, (object1.x + self.roi_x , object1.y + self.roi_y ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    def display_video(self, MODE, winner):
        if(MODE == "GAME OVER"):
            if(winner == "CHASER"):
                cv2.putText(self.frame, "COLLISION", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if(winner == "ESCAPER"):
                cv2.putText(self.frame, "ESCAPE", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
        # Display the frame in a window named 'Camera Feed'
        cv2.imshow('Camera Feed', self.frame)


def main():
    # Initialize video capture from the default camera (usually 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    REFEREE = game_referee()
    VIDEOGRAPHER = video_capture(cap)
    cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Camera Feed', 1400, 900)
    
    #SERVER = server_messenger()
    #REFEREE.messenger = SERVER
    #SERVER.connect_server()
    #client_thread = threading.Thread(target=SERVER.connect_client)
    #sender1_thread = threading.Thread(target=SERVER.sender1)
    #receiver1_thread = threading.Thread(target=SERVER.receiver1)
    #sender2_thread = threading.Thread(target=SERVER.sender2)
    #receiver2_thread = threading.Thread(target=SERVER.receiver2)
    #client_thread.start()
    #sender1_thread.start()
    #receiver1_thread.start()
    #sender2_thread.start()
    #receiver2_thread.start()

    while True:
        #REFEREE.check_client1()
        #REFEREE.check_client2()
        #REFEREE.game_advance()
        
        ret, VIDEOGRAPHER.frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        VIDEOGRAPHER.brighten_frame()
        
        CHASER = VIDEOGRAPHER.find_object("CHASER")
        ESCAPER = VIDEOGRAPHER.find_object("ESCAPER")
        EXIT1 = VIDEOGRAPHER.find_object("EXIT1")
        EXIT2 = VIDEOGRAPHER.find_object("EXIT2")
        
        REFEREE.check_collision(CHASER,ESCAPER)
        REFEREE.check_escape(ESCAPER,EXIT1)
        REFEREE.check_escape(ESCAPER,EXIT2)
        #REFEREE.check_timer()
        
        # Display the frame in a window named 'Camera Feed'
        VIDEOGRAPHER.display_video(REFEREE.MODE, REFEREE.winner)

        # Break the loop if 'q' key is pressed
        if (cv2.waitKey(1) & 0xFF == ord('q')) or (REFEREE.MODE == "EXIT"):
            break
    
    # Release the video capture and close all OpenCV windows
    #SERVER.running = False
    #client_thread.join()
    #sender1.join()
    #receiver1.join()
    #sender2.join()
    #receiver2.join()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


