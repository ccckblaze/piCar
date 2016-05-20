import RPi.GPIO as GPIO
import smbus
import logging
import atexit
import time
import thread
from enum import Enum
from threading import Thread, Timer

#Use I2C or origin GPIO Ports
USE_I2C = False
I2C_ADDR = 0x20
I2C_DEVICE = 1

GPIO_FRONT_LEFT_DIR = 7
GPIO_FRONT_LEFT_PWM = 11
GPIO_FRONT_RIGHT_DIR = 12
GPIO_FRONT_RIGHT_PWM = 13
GPIO_BACK_LEFT_DIR = 15
GPIO_BACK_LEFT_PWM = 16
GPIO_BACK_RIGHT_DIR = 18
GPIO_BACK_RIGHT_PWM = 22
GPIO_CAMERA_SERVO = 29

init = False
def threaded(fn):
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

def t_init():
    global init
    if init == False:
        logging.debug('init')
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(True)
        if USE_I2C:
            logging.debug('Using I2C')
            global i2c
            try:
                i2c = smbus.SMBus(I2C_DEVICE)
            except (IOError):
                logging.debug('I2C Device Not Found!')
            
            # Set PCF8575 outputs
            try :
                # value to send
                temp = 0x55AA
                i2c.write_block_data(I2C_ADDR, 0, [0xEA, 0x11])
                #i2c.write_byte(I2C_ADDR, 0xF1)
                #print 'PCF8575 at address 0x{0:02x} WRITE 0x{1:04x}'.format( I2C_ADDR, temp )
                #i2c.write_byte_data( I2C_ADDR, temp & 0xff, ( temp & 0xff ) >> 8 )
            except IOError :
                logging.debug('PCF8575 Device not found at I2C address 0x{1:02x}'.format( I2C_ADDR ))
                error = 1
            else :
                # Now read from PCF8575
                #temp = i2c.read_word_data( I2C_ADDR, 0 )
                #print 'PCF8575 at address 0x{0:02x} READ 0x{1:04x}'.format( I2C_ADDR, temp )
                pass
        init = True


def t_cleanup():
    global init
    if init == True:
        print('cleanup')
        GPIO.cleanup()

atexit.register(t_cleanup)

class Wheel(object):
        
    PWM_FREQUENCY = 1000
    destroyed = False

    def __init__(self, direction_io, pwm_io):
        logging.debug('Wheel init: ' + str(direction_io) + ', ' + str(pwm_io))
        t_init()
        self.dir_io = direction_io
        GPIO.setup(self.dir_io, GPIO.OUT)

        self.pwm_io = pwm_io
        GPIO.setup(self.pwm_io, GPIO.OUT)
        self.pwm_ch = GPIO.PWM(self.pwm_io, self.PWM_FREQUENCY)
        self.pwm_ch.start(0)

    def __del__(self):
        print('Wheel destroryed')

    def destory(self):
        self.destroyed = True
        self.pwm_ch.stop()
                
    def forward(self):
        GPIO.output(self.dir_io, True)

    def backward(self):
        GPIO.output(self.dir_io, False)

    def setSpeed(self, speed):
        self.pwm_ch.ChangeDutyCycle(speed)

    def stop(self):
        self.setSpeed(0)

class Servo(object):
        
    PWM_FREQUENCY = 50
    destroyed = False

    degree = 90

    class ServoLoopThread(Thread):
        def __init__(self, owner):
            self.owner = owner 
            self.thread_stop = False
            Thread.__init__(self)

        def run(self):
            prevDegree = self.owner.degree
            while not self.thread_stop:
                try:
                    if not prevDegree == self.owner.degree:
                        self.owner.pwm_ch.ChangeDutyCycle(2.5 + 10 * self.owner.degree / 180) # Angle Speed
                        prevDegree = self.owner.degree
                    time.sleep(0.5)
                except (AttributeError, TypeError):
                    print('Exception exit')

            thread.exit_thread()

        def stop(self):
            self.thread_stop = True

    def __init__(self, pwm_io):
        logging.debug('Servo init: ' + str(pwm_io))
        t_init()

        self.pwm_io = pwm_io
        GPIO.setup(self.pwm_io, GPIO.OUT)
        self.pwm_ch = GPIO.PWM(self.pwm_io, self.PWM_FREQUENCY)
        self.pwm_ch.start(0)
        self.servoLoopThread = self.ServoLoopThread(self)
        self.servoLoopThread.start()
        
    def __del__(self):
        print('Servo destroryed')
       
    def destroy(self):
        self.destroyed = True
        self.servoLoopThread.stop()
        self.servoLoopThread.join()
        self.servoLoopThread = None
        self.pwm_ch.stop()

    def setDegree(self, degree):
        if degree >= 0 and degree <= 180:
            self.degree = degree
        else:
            logging.debug('degree not valid')

class Direction(Enum):

    none = 0
    forward = 1
    backward = 2
    left = 3
    right = 4

class Car(object):
        
    CAMERA_SERVO_DEGRE_DELTA = 10
    TIMEOUT = 5
    destroyed = False

    checkTimeout = False
    commandTiming = 0
    speed = 0
    stoped = True
    direction = Direction.none

    class DetectLoopThread(Thread):
        def __init__(self, owner):
            self.owner = owner 
            self.thread_stop = False
            Thread.__init__(self)

        def run(self):
            while not self.thread_stop:
                try:
                    delay = 0.2
                    if self.owner.checkTimeout:
                        if self.owner.commandTiming >= self.owner.TIMEOUT:
                            self.owner.stop()
                            self.owner.commandTiming = 0
                            self.owner.checkTimeout = False
                            logging.debug('Timeout')
                        else:
                            self.owner.commandTiming += delay

                    time.sleep(delay)

                except (AttributeError, TypeError):
                    print('Exception exit')

        def stop(self):
            self.thread_stop = True
       
    def __init__(self):
        logging.debug('Car init')
        t_init()
        self.wheel_front_left = Wheel(GPIO_FRONT_LEFT_DIR, GPIO_FRONT_LEFT_PWM)
        self.wheel_front_right = Wheel(GPIO_FRONT_RIGHT_DIR, GPIO_FRONT_RIGHT_PWM)
        self.wheel_back_left = Wheel(GPIO_BACK_LEFT_DIR, GPIO_BACK_LEFT_PWM)
        self.wheel_back_right = Wheel(GPIO_BACK_RIGHT_DIR, GPIO_BACK_RIGHT_PWM)
        self.camera_servo = Servo(GPIO_CAMERA_SERVO)
        self.detectLoopThread = self.DetectLoopThread(self)
        self.detectLoopThread.start()

    def __del__(self):
        print('Car destroyed')
        self.wheel_front_left.destory()
        self.wheel_front_right.destory()
        self.wheel_back_left.destory()
        self.wheel_back_right.destory()
        self.camera_servo.destroy()

    def destroy(self):
        self.destroyed = True
        self.detectLoopThread.stop()
        self.detectLoopThread.join()
        self.detectLoopThread = None

    def timeout(self):
        try:
            logging.debug('timeout')
            if not self.destroyed:
                self.stop() 
        except (AttributeError, TypeError):
            logging.debug('Exception exit')

    def forward(self):
        self.stoped = False
        self.direction = Direction.forward
        self.wheel_front_left.forward()
        self.wheel_front_right.forward()
        self.wheel_back_left.forward()
        self.wheel_back_right.forward()
        self.updateSpeed()
        self.setTimeout()

    def backward(self):
        self.stoped = False
        self.direction = Direction.backward
        self.wheel_front_left.backward()
        self.wheel_front_right.backward()
        self.wheel_back_left.backward()
        self.wheel_back_right.backward()
        self.updateSpeed()
        self.setTimeout()

    def left(self):
        self.stoped = False
        self.direction = Direction.left
        self.wheel_front_left.backward()
        self.wheel_front_right.forward()
        self.wheel_back_left.backward()
        self.wheel_back_right.forward()
        self.updateSpeed()
        self.setTimeout()

    def right(self):
        self.stoped = False
        self.direction = Direction.right
        self.wheel_front_left.forward()
        self.wheel_front_right.backward()
        self.wheel_back_left.forward()
        self.wheel_back_right.backward()
        self.updateSpeed()
        self.setTimeout()

    def setSpeed(self, speed):
        self.speed = speed
        self.updateSpeed()
    
    def cameraLeft(self):
        self.camera_servo.setDegree(self.camera_servo.degree + self.CAMERA_SERVO_DEGRE_DELTA)
        
    def cameraRight(self):
        self.camera_servo.setDegree(self.camera_servo.degree - self.CAMERA_SERVO_DEGRE_DELTA)
        
    def setTimeout(self):
        self.checkTimeout = True
        self.commandTiming = 0
        
    def updateSpeed(self):
        if not self.stoped:
            #currentSpeed = self.speed * 0.5 if self.forwarding else self.speed 
            currentSpeed = self.speed
        else:
            currentSpeed = 0

        self.wheel_front_left.setSpeed(
            currentSpeed)
        self.wheel_front_right.setSpeed(
            currentSpeed)
        self.wheel_back_left.setSpeed(
            currentSpeed)
        self.wheel_back_right.setSpeed(
            currentSpeed)

    def stop(self):
        self.stoped = True
        self.direction = Direction.none
        self.wheel_front_left.stop()
        self.wheel_front_right.stop()
        self.wheel_back_left.stop()
        self.wheel_back_right.stop()

