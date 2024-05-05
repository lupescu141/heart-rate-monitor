import fifo
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import micropython
import urequests as requests  
import ujson 
import network 
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


        # Sensor:

sensor = ADC(26)
sensor_history_size = 200
history = []
timer = Timer(-1)
timer.deinit()
sensor_bool = False


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
        self.menuPointer = ">"
        self.menuState = 1
        
        # measure_heart_rate attributes:
        
        self.beats = 0
        self.beat = False
        self.UserBPMText = 0
        
        # basic_hrv_analysis attributes:
        
        self.meanPPI 	= 0
        self.meanPPItxt = "MEAN PPI: "
        self.meanHR 	= 0
        self.meanHRtxt  = "MEAN HR: "
        self.RMSSD 		= 0
        self.RMSSDtxt	= "RMSSD: "
        self.SDNN 		= 0
        self.SDNNtxt	= "SDNN: "
        
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
            
            
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 1:
                
                self.menuState = 4
                self.buttonsAreUp = False 
            
            else:
                
                self.menuState -= 1
                self.buttonsAreUp = False 
                
        if sw0() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 4:
                
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
                pass
            
            elif self.menuState == 3:
                
                oled.fill(0)
                self.buttonsAreUp = False 
                self.deviceState = "History"

            elif self.menuState == 4:
                pass
        
        self.checkButtonsAreUp()
        
        
    def measure_heart_rate_pause(self):
        
        oled.text("START ", 45, 0, 1)
        oled.text("MEASUREMENT BY", 8, 11, 1)
        oled.text("PRESSING BUTTON", 5, 23, 1)
        oled.text("SW_2", 45, 35, 1)
        oled.text("SW_1 FOR MENU", 10, 56, 1)
        oled.show()
        
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Measure heart rate"
            timer.init(period=5000, mode=Timer.PERIODIC, callback=timer_callback)			#Timer päälle BPM laskua varten
            
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
        
        self.checkButtonsAreUp()
        
        
    def measure_heart_rate(self):

        global history
        global sensor_history_size
        
        oled.text("BPM: ", 35, 10, 1)
        oled.text("PRESS SW_2 TO", 10, 35, 1)
        oled.text("STOP", 47, 48, 1)
        oled.show()
            
        sensor_data = sensor.read_u16()
        history.append(sensor_data)
        history = history[-sensor_history_size:]
        
        floor, roof = min(history), max(history)
        
        max_filter = floor + (roof - floor) * 0.48
        min_filter = (floor + roof)//2
            
        if not self.beat and sensor_data > max_filter:
            self.beat = True
            self.beats += 1
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
            
        elif sensor_data < max_filter and self.beat:
            self.beat = False
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
                
        if sw2() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            timer.deinit()
            self.deviceState = "measure heart rate pause"
            
        self.checkButtonsAreUp()
            
        
    def bpm_calc(self):
        
        oled.fill_rect(65, 10, 50, 10, 0)
        print("callback")
        bpm = self.beats * 12
        self.beats = 0
        self.UserBPMText = "BPM: "+ str(bpm)
        oled.text(self.UserBPMText, 35, 10, 1)
        print(bpm)
        oled.show()
        
        
    def basic_hrv_analysis(self):
        pass
                
        
    def history(self):
        
        if len(self.historyList) == 0:
            
            oled.text("HISTORY", 35, 0, 1)
            oled.text("IS EMPTY", 30, 12, 1)
            oled.text("PRESS SW_1 TO", 10, 27, 1)
            oled.text("GO BACK", 35, 39, 1)
            oled.show()
        
        if sw1() == 0 and self.buttonsAreUp == True:
            
            oled.fill(0)
            self.buttonsAreUp = False
            self.deviceState = "Main menu"
            
        self.checkButtonsAreUp()
        
    def kubios(self):
        pass
                   
                   
    def sendData_MQTT(self):
        pass


# Main Loop:
device = HeartMonitor()

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
        
        device.history()
        
    if device.deviceState == "kubios":
        
        device.kubios()
        
    if device.deviceState == "measure heart rate pause":
        
        device.measure_heart_rate_pause()
    
