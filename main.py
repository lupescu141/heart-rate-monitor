import fifo
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import micropython
import urequests as requests  
import ujson 
import network
import math
from umqtt.simple import MQTTClient
micropython.alloc_emergency_exception_buf(200)


# Hardware:

            
        # Buttons:
            
sw0 = Pin(9, Pin.IN, Pin.PULL_UP) # Down
sw1 = Pin(8, Pin.IN, Pin.PULL_UP) # SELECT
sw2 = Pin(7, Pin.IN, Pin.PULL_UP) # UP

        
        # Display Settings:
        
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

HEART = [
[ 0, 0, 0, 0, 0, 0, 0, 0, 0],
[ 0, 1, 1, 0, 0, 0, 1, 1, 0],
[ 1, 1, 1, 1, 0, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 0, 1, 1, 1, 1, 1, 1, 1, 0],
[ 0, 0, 1, 1, 1, 1, 1, 0, 0],
[ 0, 0, 0, 1, 1, 1, 0, 0, 0],
[ 0, 0, 0, 0, 1, 0, 0, 0, 0],
]

        # Sensor:

sensor = ADC(26)


def calculate_bpm(beats):
    
    if beats:
        beat_time = beats[-1] - beats[0]
        
        if beat_time:
            
            return (len(beats) / (beat_time)) * 60

last_y = 0


def refresh(bpm, beat, v, minima, maxima):
    
    global last_y

    oled.vline(0, 0, 32, 0)
    oled.scroll(-1,0) # Scroll left 1 pixel

    if maxima-minima > 0:
        # Draw beat line.
        y = 32 - int(16 * (v-minima) / (maxima-minima))
        oled.line(125, last_y, 126, y, 1)
        last_y = y

    # Clear top text area.
    oled.fill_rect(0,0,128,16,0) # Clear the top text area
    oled.fill_rect(0,40,128,30,0)

    if bpm:
        oled.text("BPM: %d" % bpm, 12, 0)

    # Draw heart if beating.
    if beat:
        
        for y, row in enumerate(HEART):
            for x, c in enumerate(row):
                oled.pixel(x, y, c)
                
    oled.text("PRESS SW_2 TO", 10, 45, 1)
    oled.text("STOP", 47, 55, 1)
    oled.show()
 

# Timers
timer = Timer(-1)
timer2 = Timer(-1)


# WLAN SETTINGS

# Replace these values with your own
SSID = "KMD759_Group_5"
PASSWORD = "ryhma51234"
BROKER_IP = "192.168.5.253"

# Function to connect to WLAN
def connect_wlan():
    # Connecting to the group WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        print("Connecting... ")
        time.sleep(1)

    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])
    
def connect_mqtt():
    mqtt_client=MQTTClient("", BROKER_IP)
    mqtt_client.connect(clean_session=True)
    return mqtt_client


#Functions

def calculate_mean(data):
    return sum(data) / len(data)


def calculate_sdnn(rr_intervals):
    mean_rr = calculate_mean(rr_intervals)
    squared_diff = [(x - mean_rr) ** 2 for x in rr_intervals]
    variance = sum(squared_diff) / len(rr_intervals)
    sdnn = math.sqrt(variance)
    return sdnn

def calculate_sdsd(rr_intervals):
    differences = [second - first for first, second in zip(rr_intervals[:-1], rr_intervals[1:])]
    sdsd = math.sqrt(sum([(diff - calculate_mean(differences))**2 for diff in differences]) / (len(differences) - 1))
    return sdsd

def calculate_rmssd(rr_intervals):
    differences = [second - first for first, second in zip(rr_intervals[:-1], rr_intervals[1:])]
    squared_diffs = [(diff ** 2) for diff in differences]
    rmssd = math.sqrt(sum(squared_diffs) / len(differences))
    return rmssd

def calculate_mean_heart_rate(rr_intervals):
    # Convert RR intervals to heart rates (beats per minute)
    heart_rates = []  # Convert milliseconds to beats per minute (bpm)
    
    for i in rr_intervals:
        
        heart_rates.append(60000 / i)
    # Calculate the mean heart rate
    mean_heart_rate = sum(heart_rates) / len(rr_intervals)
    
    return mean_heart_rate


class HeartMonitor():
    
    def __init__(self):
        
        # main attribtes:
        self.deviceState = "Main menu"
        self.buttonsAreUp = True
        
        # mainMenu attributes:
        
        self.menuTxtBpm 	= "HEART RATE"
        self.menuTxtHrv		= "HRV ANALYSIS"
        self.menuTxtHistory = "HISTORY"
        self.menuTxtKubios 	= "KUBIOS"
        self.menuTxtMqtt 	= "SEND MQTT"
        self.menuPointer = ">"
        self.menuState = 1
        
        # measure_heart_rate attributes:
        
        self.history = []
        self.beats = []
        self.beat = False
        self.MAX_HISTORY = 250
        self.TOTAL_BEATS = 30
        self.UserBPMText = 0
        self.v = 0
        self.minima = 0
        self.maxima = 0
        self.threshold_on = 0
        self.threshold_off = 0
        self.bpm = None
        self.emptyBeats = False
        
        # basic_hrv_analysis attributes:
        
        self.meanPPI 	= 0
        self.meanHR 	= 0
        self.RMSSD 		= 0
        self.SDNN 		= 0
        self.bpm_time = 0
        self.prev_bpm_time = 0
        self.intervals = []
        self.timeLeft = 30
        
        # history attributes:
        
        self.historyList = []
        self.timestamp = []
        
        # kubios attributes:
        
        self.dataset = { 
                        "type": "RRI", 
                        "data": "intervals", 
                        "analysis": {"type": "readiness"}
                        } 
        
        # sendData_MQTT attributes:
        
        self.measurement = { 
                        "mean_hr": self.meanHR, 
                        "mean_ppi": self.meanPPI, 
                        "rmssd": self.RMSSD, 
                        "sdnn": self.SDNN
                        } 
    
    def checkButtonsAreUp(self):
        
        if sw0() == 1 and sw1() == 1 and sw2() == 1:
            
            self.buttonsAreUp = True
            
    
    def mainMenu(self):

        time.sleep(0.05)
        oled.text(self.menuTxtBpm, 15, 2, 1)
        oled.text(self.menuTxtHrv, 15, 15, 1)
        oled.text(self.menuTxtHistory, 15, 28, 1)
        oled.text(self.menuTxtKubios, 15, 41, 1)
        oled.text(self.menuTxtMqtt, 15, 54, 1)
        oled.show()
        
        if self.menuState == 1:
            
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 2, 1)
            

        elif self.menuState == 2:
            
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 15, 1)
            
            
        elif self.menuState == 3:
            
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 28, 1)
            

        elif self.menuState == 4:
            
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 41, 1)
        
        elif self.menuState == 5:
            
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 54, 1)
            
            
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 1:
                
                self.menuState = 5
                self.buttonsAreUp = False 
            
            else:
                
                self.menuState -= 1
                self.buttonsAreUp = False 
                
        if sw0() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 5:
                
                self.menuState = 1
                self.buttonsAreUp = False 
            
            else:
                
                self.menuState += 1
                self.buttonsAreUp = False 
                
        if sw1() == 0 and self.buttonsAreUp == True:
            
            if self.menuState == 1:
                
                oled.fill(0)
                self.buttonsAreUp = False 
                self.deviceState = "measure heart rate pause"
                
            elif self.menuState == 2:
                
                oled.fill(0)
                self.buttonsAreUp = False
                self.deviceState = "Basic hrv analysis pause"
            
            elif self.menuState == 3:
                
                oled.fill(0)
                self.buttonsAreUp = False 
                self.deviceState = "History"

            elif self.menuState == 4:
                pass
            
            elif self.menuState == 5:
                
                oled.fill(0)
                self.buttonsAreUp = False 
                self.deviceState = "sendData_MQTT"
        
        self.checkButtonsAreUp()
        
        
    def measure_heart_rate_pause(self):
        
        oled.fill(0)
        oled.text("START ", 45, 0, 1)
        oled.text("MEASUREMENT BY", 8, 11, 1)
        oled.text("PRESSING BUTTON", 5, 23, 1)
        oled.text("SW_2", 45, 35, 1)
        oled.text("SW_1 FOR MENU", 10, 56, 1)
        self.v = 0
        self.minima = 0
        self.maxima = 0
        self.threshold_on = 0
        self.threshold_off = 0
        self.emptyBeats = False 
        oled.show()
        
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Measure heart rate"
            
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
        
        self.checkButtonsAreUp()
        
        
    def measure_heart_rate(self):
        
            
        # Maintain a log of previous values to
        # determine min, max and threshold.
        self.v = sensor.read_u16()
        self.history.append(self.v)
        

        # Get the tail, up to MAX_HISTORY length
        self.history = self.history[-self.MAX_HISTORY:]
        
        self.minima, self.maxima = min(self.history), max(self.history)
        self.threshold_on = (self.minima + self.maxima * 3) // 4   # 3/4
        self.threshold_off = (self.minima + self.maxima) // 2      # 1/2

        if self.v > self.threshold_on and self.beat == False:

            self.beat = True
            self.beats.append(time.time())
            
            if self.emptyBeats == False:
                
                self.beats.clear()
                self.emptyBeats = True 
                
            self.beats = self.beats[-self.TOTAL_BEATS:]
            self.bpm=calculate_bpm(self.beats)
            

        if self.v < self.threshold_off and self.beat == True:
            
            self.beat = False
                
        if sw2() == 0 and self.buttonsAreUp == True:
            
            self.buttonsAreUp = False
            self.deviceState = "measure heart rate pause"
            
        self.checkButtonsAreUp()
        refresh(self.bpm, self.beat, self.v, self.minima, self.maxima)
            
    def basic_hrv_analysis_pause(self):
        
        oled.text("PRESS SW_2", 20, 10, 1)
        oled.text("TO START", 25, 22, 1)
        oled.text("Calculating", 20, 34, 1)
        oled.show()
        
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            timer.init(mode=Timer.ONE_SHOT, period=30000, callback= self.hrv_calc)
            timer2.init(mode=Timer.PERIODIC, period=1000, callback= self.minusSecond)
            self.timeLeft = 30
            self.deviceState = "Basic hrv analysis"
            
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
        
        self.checkButtonsAreUp()
    
    def basic_hrv_analysis(self):
        
        oled.fill(0)
        oled.text("CALCULATING...", 10, 10, 1)
        oled.text(f'{self.timeLeft}', 58, 25, 1)
        oled.text("PRESS SW_2 TO", 13, 41, 1)
        oled.text("GO BACK", 40, 53, 1)
        oled.show()
        
        # Maintain a log of previous values to
        # determine min, max and threshold.
        self.v = sensor.read_u16()
        self.history.append(self.v)
        
        # Get the tail, up to MAX_HISTORY length
        self.history = self.history[-self.MAX_HISTORY:]
        
        self.minima, self.maxima = min(self.history), max(self.history)
        self.threshold_on = (self.minima + self.maxima * 3) // 4   # 3/4
        self.threshold_off = (self.minima + self.maxima) // 2      # 1/2

        if self.v > self.threshold_on and self.beat == False:
            
            self.bpm_time = time.ticks_ms()
            time_since_peak = self.bpm_time - self.prev_bpm_time
            
            if time_since_peak > 290 and time_since_peak < 2000:
                
                self.intervals.append(time_since_peak)
            
            if self.emptyBeats == False:
                
                self.intervals.clear()
                self.emptyBeats = True
                
            self.prev_bpm_time = self.bpm_time
            self.beat = True

        if self.v < self.threshold_off and self.beat == True:
            
            self.beat = False
        
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Basic hrv analysis pause"
        
        self.checkButtonsAreUp()
    
        
    def hrv_calc(self, monkey):
        
        print(monkey)
        for i in self.intervals:
            print(i)
            
        self.SDNN = calculate_sdnn(self.intervals)
        self.RMSSD = calculate_rmssd(self.intervals)
        self.meanHR = calculate_mean_heart_rate(self.intervals)
        self.meanPPI = calculate_mean(self.intervals)
        self.historyList.clear()
        self.historyList.append(self.SDNN)
        self.historyList.append(self.RMSSD)
        self.historyList.append(self.meanHR)
        self.historyList.append(self.meanPPI)
        self.timestamp.append(time.localtime())
        
        self.measurement = { 
                        "mean_hr": self.meanHR, 
                        "mean_ppi": self.meanPPI, 
                        "rmssd": self.RMSSD, 
                        "sdnn": self.SDNN
                        }
        oled.fill(0)
        self.deviceState = "showHrvResult"
        
    def showHrvResult(self):
        
        oled.text(f"SDNN:     {self.SDNN :.0f}", 0, 0, 1)
        oled.text(f"RMSSD:    {self.RMSSD :.0f}", 0, 14, 1)
        oled.text(f"MEAN HR:  {self.meanHR :.0f}", 0, 28, 1)
        oled.text(f"MEAN PPI: {self.meanPPI :.0f}", 0, 42, 1)
        oled.text("SW_1 FOR MENU", 10, 56, 1)
        oled.show()
        
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
            
        self.checkButtonsAreUp()

    def minusSecond(self, monkey):
        
        self.timeLeft -= 1
    
    
    def hrvHistory(self):
        
        if len(self.historyList) == 0:
            
            oled.text("HISTORY", 35, 0, 1)
            oled.text("IS EMPTY", 30, 12, 1)
            oled.text("PRESS SW_1 TO", 10, 27, 1)
            oled.text("GO BACK", 35, 39, 1)
            oled.show()
        
        else:
            oled.text(f"{self.timestamp[0][0]} {self.timestamp[0][1]} {self.timestamp[0][2]} {self.timestamp[0][3]}:{self.timestamp[0][4]}" , 10, 0, 1)
            oled.text(f"SDNN:     {self.SDNN :.0f}", 0, 12, 1)
            oled.text(f"RMSSD:    {self.RMSSD :.0f}", 0, 23, 1)
            oled.text(f"MEAN HR:  {self.meanHR :.0f}", 0, 34, 1)
            oled.text(f"MEAN PPI: {self.meanPPI :.0f}", 0, 45, 1)
            oled.text("SW_1 FOR MENU", 10, 56, 1)
            oled.show()
        
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
            
        self.checkButtonsAreUp()
        
    def kubios(self):
        pass
                   
                   
    def sendData_MQTT(self):
        
        if len(self.historyList) == 0:
            
            oled.text("HRV RESULT", 25, 0, 1)
            oled.text("IS EMPTY", 30, 12, 1)
            oled.text("PRESS SW_1 TO", 10, 27, 1)
            oled.text("GO BACK", 35, 39, 1)
            oled.show()
        
        else :
        
            connect_wlan()
        
            # Connect to MQTT
            try:
                mqtt_client=connect_mqtt()
            
            except Exception as e:
                print(f"Failed to connect to MQTT: {e}")

            # Send MQTT message
            try:
                while True:
                    # Sending a message every 5 seconds.
                    topic = "HrvResult"
                    message = "Great job group X!"
                    mqtt_client.publish(topic, ujson.dumps(self.measurement))
                    print(f"Sending to MQTT: {topic} -> {self.hrvHistory}")
                    time.sleep(5)
                    self.deviceState = "Mqtt succesfull"
                    break 
                
            except Exception as e:
                print(f"Failed to send MQTT message: {e}")
                
            
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
        
        self.checkButtonsAreUp()

        

# Main Loop:
device = HeartMonitor()
connect_wlan()

# Timer callback
def timer_callback(timer):
    
    device.bpm_calc()


while True:
    
    if device.deviceState == "Main menu":
        
        device.mainMenu()
        
    if device.deviceState == "Measure heart rate":
        
        device.measure_heart_rate()
        
    if device.deviceState == "Basic hrv analysis":
        
        device.basic_hrv_analysis()
        
    if device.deviceState == "History":
        
        device.hrvHistory()
        
    if device.deviceState == "kubios":
        
        device.kubios()
        
    if device.deviceState == "measure heart rate pause":
        
        device.measure_heart_rate_pause()
    
    if device.deviceState == "showHrvResult":
        
        device.showHrvResult()
        
    if device.deviceState == "Basic hrv analysis pause":
        
        device.basic_hrv_analysis_pause()
    
    if device.deviceState == "sendData_MQTT":
        
        device.sendData_MQTT()
