#!/usr/bin/env python3

import logging
import logging.handlers
import argparse
import sys
import time  # this is only being used as part of the example

import RPi.GPIO as GPIO
import os


DEBUG_ACTIVE=False

# Deafults
LOG_FILENAME = "/tmp/HaltRebootDaemon.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="Halt and Reboot Service for Raspberry PI")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
    LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)


def Mils2Second(millisecond):
    return millisecond/1000

def timeout_ms_expired(PrevTime, timeout):
    diff = ((time.time() *1000) - PrevTime)
    if ( diff > timeout):
        return 1
    else:
        return 0

def get_ms_time():
    return (time.time()*1000)


# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())
            
    def flush(self):
        pass


# # Replace stdout with logging to file at INFO level
# sys.stdout = MyLogger(logger, logging.INFO)
# # Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)

#GPIO Configuration

class InOut(object):
    def __init__(self,id,type, onEventPressed="", onEventDeressed="", BounceTimeout=20):
        if ((type==GPIO.IN) or (type==GPIO.OUT)):
            self.id=id
            self.type=type
            self.value=0
            self.blinking=0
            self.blinktime=0
            self.blinkperiod=0
            self.blinkdutycicle=0
            self.BounceTimeOut=0
            self.LastIn=0
            self.EventPressed=""
            self.EventDeressed=""
            self.BouceTime=get_ms_time()
            self.EventRised=1
            GPIO.setup(self.id,self.type)

        if (type==GPIO.IN):

            if (BounceTimeout<0):
                BounceTimeout=0

            self.blinktime=get_ms_time()
            self.blinkperiod=0
            self.blinkdutycicle=50
            self.BounceTimeOut=BounceTimeout
            self.LastIn=GPIO.input(self.id)
            self.EventPressed=onEventPressed
            self.EventDeressed=onEventDeressed
            self.BouceTime=get_ms_time()
            self.EventRised=1
            
    
    def SetOutput(self,value,blinking=0,period=1000,dutycicle=50):
        if self.type==GPIO.OUT:
            self.value=value
            self.blinking=blinking

            if (self.value<0):
                self.value=0
            elif (self.value>1):
                self.value=1
            
            
            if (dutycicle<0):
                dutycicle=1
            elif (dutycicle>100):
                dutycicle=100
                
            if period<0:
                period=1
            
            if (self.blinking):
                self.blinktime=get_ms_time()
                self.blinkperiod=period
                self.blinkdutycicle=dutycicle
            
            GPIO.output(self.id,self.value)
    
    def GetInput(self): 
        return (GPIO.input(self.id))
    
    def InOutLoop(self):
        if(self.type==GPIO.OUT):
            if(self.blinking):
                if self.blinkdutycicle<=0:
                    self.blinkdutycicle=1
                    
                OnTime = (self.blinkperiod * (1/(100/self.blinkdutycicle)))
                OffTime = self.blinkperiod - OnTime
                
                if (self.value==1): 
                    if (timeout_ms_expired(self.blinktime,OnTime)):
                        self.blinktime=get_ms_time()
                        self.value=0
                        GPIO.output(self.id,self.value)
                else:
                    if (timeout_ms_expired(self.blinktime,OffTime)):
                        self.blinktime=get_ms_time()
                        self.value=1
                        GPIO.output(self.id,self.value)
                        
        elif(self.type==GPIO.IN):
            self.CurrIn=GPIO.input(self.id)
            if (self.CurrIn!=self.LastIn):
                self.LastIn=self.CurrIn
                self.BouceTime=get_ms_time()
                self.EventRised=0
                
            else:
                if (self.EventRised==0):
                    if ( (self.BounceTimeOut==0) or (timeout_ms_expired(self.BouceTime,self.BounceTimeOut)) ):

                        if (self.CurrIn==1):
                            self.EventDeressed(self.id)
                        else:
                            self.EventPressed(self.id)
                        
                        self.EventRised=1
                        

class MyIO(object):
    def __init__(self,BtnPressEvent,BtnDepressEvent):
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            self.Button   = InOut(28,GPIO.IN,BtnPressEvent,BtnDepressEvent,30)
            self.GreenLed = InOut(29,GPIO.OUT)
            self.RedLed   = InOut(30,GPIO.OUT)
        except value:
            pass

    def Loop(self):
        self.Button.InOutLoop()
        self.GreenLed.InOutLoop()
        self.RedLed.InOutLoop()
            


# nPipe_path= "/tmp/HaltRestartDemon.fifo"
# 
# nPipe = os.mkfifo(nFIFO_path)


BUTTON_PRESSED=0

def ButtonPressedFunction(channel):
    if (DEBUG_ACTIVE): print(channel, "ButtonPressed at ", time.time())
    global BUTTON_PRESSED
    BUTTON_PRESSED=1

def ButtonDepressedFunction(channel):
    if (DEBUG_ACTIVE): print(channel, "ButtonDepressed at ", time.time())
    global BUTTON_PRESSED
    BUTTON_PRESSED=0


def main():
    global BUTTON_PRESSED
    LocalIO=MyIO(ButtonPressedFunction,ButtonDepressedFunction)
    
    CurrentStatus= 0
    # Loop forever, doing something useful hopefully:
    while True:
        LocalIO.Loop()
        
        
        if (CurrentStatus == 0):
            logger.info("Shutdown and Reboot Service started")
            if (DEBUG_ACTIVE): print ("Shutdown and Reboot Service started")
            LocalIO.GreenLed.SetOutput(1,0,0,0)
            LocalIO.RedLed.SetOutput(0,0,0,0)
            CurrentStatus=1
            BUTTON_PRESSED=0
    
        elif (CurrentStatus == 1):
            if (BUTTON_PRESSED==1):
                if (DEBUG_ACTIVE): print ("pressed")
                StepTime=get_ms_time()
                CurrentStatus=2
           
        elif (CurrentStatus == 2):
            if (BUTTON_PRESSED==0):
                #shutdown request
                StepTime=get_ms_time()
                CurrentStatus = 10
            elif (timeout_ms_expired(StepTime,4000)):
                #reboot request
                StepTime=get_ms_time()
                CurrentStatus = 20
    
        elif (CurrentStatus == 10):
            LocalIO.GreenLed.SetOutput(1,1,500,50)
            CurrentStatus=11
    
        elif (CurrentStatus == 11):
            if (timeout_ms_expired(StepTime,250)):
                LocalIO.RedLed.SetOutput(1,1,500,50)
                CurrentStatus=12
    
        elif (CurrentStatus == 12):
            if (DEBUG_ACTIVE): print ("Shutdown the System now")
            logger.info("Shutdown the System now")
            if (DEBUG_ACTIVE==False): os.system("shutdown -h now")
            CurrentStatus=50
    
    
        elif (CurrentStatus == 20):
            LocalIO.GreenLed.SetOutput(1,0,0,0)
            LocalIO.RedLed.SetOutput(1,1,500,50)
            CurrentStatus=21
    
        elif (CurrentStatus == 21):
            if (DEBUG_ACTIVE): print ("Reboot the System now")
            logger.info("Reboot the System now")
            if (DEBUG_ACTIVE==False): os.system("shutdown -r now")
            CurrentStatus=50
            
    
        elif (CurrentStatus == 50):
            #wait
            pass
        
        else:
            GPIO.cleanup()
            exit(0)
    
        time.sleep(Mils2Second(5))    
    
    
main()



