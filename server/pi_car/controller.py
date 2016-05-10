import RPi.GPIO as GPIO
import smbus
import logging
import atexit
import time
import threading

#Use I2C or origin GPIO Ports
USE_I2C = True

GPIO_FRONT_LEFT_DIR = 7
GPIO_FRONT_LEFT_PWM = 11
GPIO_FRONT_RIGHT_DIR = 12
GPIO_FRONT_RIGHT_PWM = 13
GPIO_BACK_LEFT_DIR = 15
GPIO_BACK_LEFT_PWM = 16
GPIO_BACK_RIGHT_DIR = 18
GPIO_BACK_RIGHT_PWM = 22
GPIO_CAMARA_SERVO = 29

init = False

def threaded(fn):
	def wrapper(*args, **kwargs):
	        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
	return wrapper

def t_init():
	global init
	if init == False:
		logging.debug('init')
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(True)
		if USE_I2C:
			logging.debug('Using I2C')
		init = True


def t_cleanup():
	global init
	if init == True:
		print('cleanup')
        	GPIO.cleanup()

atexit.register(t_cleanup)

class Wheel(object):
	
        PWM_FREQUENCY = 50

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
		#self.pwm_ch.stop()
		
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

        def __init__(self, pwm_io):
	        logging.debug('Servo init: ' + str(pwm_io))
	        t_init()

                self.pwm_io = pwm_io
                GPIO.setup(self.pwm_io, GPIO.OUT)
                self.pwm_ch = GPIO.PWM(self.pwm_io, self.PWM_FREQUENCY)
                self.pwm_ch.start(0)
		
		self.running = True
		self.servo_loop()
	
        def __del__(self):
		print('Servo destroryed')
		#self.pwm_ch.stop()
	
	def destroy(self):
		self.running = False

	def setAngle(self, angle):
		self.angle = angle

        @threaded
	def servo_loop(self):
		while(self.running):
       		        for i in range(0,181,10):
                	        self.pwm_ch.ChangeDutyCycle(2.5 + 10 * i / 180) # Angle Speed
                                time.sleep(0.02)                                # 20ms
	                        #self.pwm_ch.ChangeDutyCycle(0)                 # Back to zero 
				#time.sleep(0.2)
		     
                        for i in range(181,0,-10):
                                self.pwm_ch.ChangeDutyCycle(2.5 + 10 * i / 180)
	                        time.sleep(0.02)
                                #self.pwm_ch.ChangeDutyCycle(0)
	                        #time.sleep(0.2)

class Car(object):
	
	speed = 0
	decreeseFactor = 0.2
        forwarding = False
	turningLeft = False
	turningRight = False
	
	def __init__(self):
		logging.debug('Car init')
		t_init()
		self.wheel_front_left = Wheel(GPIO_FRONT_LEFT_DIR, GPIO_FRONT_LEFT_PWM)
		self.wheel_front_right = Wheel(GPIO_FRONT_RIGHT_DIR, GPIO_FRONT_RIGHT_PWM)
		self.wheel_back_left = Wheel(GPIO_BACK_LEFT_DIR, GPIO_BACK_LEFT_PWM)
		self.wheel_back_right = Wheel(GPIO_BACK_RIGHT_DIR, GPIO_BACK_RIGHT_PWM)
		self.camara_servo = Servo(GPIO_CAMARA_SERVO)

	def __del__(self):
		print('Car destroyed')
		self.camara_servo.destroy()

        def forward(self):
                self.forwarding = True 
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.forward()
		self.wheel_front_right.forward()
		self.wheel_back_left.forward()
		self.wheel_back_right.forward()
		self.updateSpeed()

        def backward(self):
                self.forwarding = False
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.backward()
		self.wheel_front_right.backward()
		self.wheel_back_left.backward()
		self.wheel_back_right.backward()
		self.updateSpeed()

        def left(self):
                self.forwarding = False
		self.turningLeft = True
		self.turningRight = False
		self.wheel_front_left.backward()
		self.wheel_front_right.forward()
		self.wheel_back_left.backward()
		self.wheel_back_right.forward()
		self.updateSpeed()

	def right(self):
                self.forwarding = False
		self.turningLeft = False
		self.turningRight = True
		self.wheel_front_left.forward()
		self.wheel_front_right.backward()
		self.wheel_back_left.forward()
		self.wheel_back_right.backward()
		self.updateSpeed()

	def setSpeed(self, speed):
		self.speed = speed
		self.updateSpeed()
		
	def updateSpeed(self):
                currentSpeed = self.speed * 0.5 if self.forwarding else self.speed 
		self.wheel_front_left.setSpeed(
				self.decreeseFactor * currentSpeed if self.turningLeft else currentSpeed)
		self.wheel_front_right.setSpeed(
				self.decreeseFactor * currentSpeed if self.turningRight else currentSpeed)
		self.wheel_back_left.setSpeed(
				self.decreeseFactor * currentSpeed if self.turningLeft else currentSpeed)
		self.wheel_back_right.setSpeed(
				self.decreeseFactor * currentSpeed if self.turningRight else currentSpeed)

	def stop(self):
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.stop()
		self.wheel_front_right.stop()
		self.wheel_back_left.stop()
		self.wheel_back_right.stop()


