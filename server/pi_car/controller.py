import RPi.GPIO as GPIO
import logging
import atexit

GPIO_FRONT_LEFT_DIR = 7
GPIO_FRONT_LEFT_PWM = 11
GPIO_FRONT_RIGHT_DIR = 12
GPIO_FRONT_RIGHT_PWM = 13
GPIO_BACK_LEFT_DIR = 15
GPIO_BACK_LEFT_PWM = 16
GPIO_BACK_RIGHT_DIR = 18
GPIO_BACK_RIGHT_PWM = 22

init = False

def t_init():
	global init
	if init == False:
		logging.debug('init')
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(True)
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

class Car(object):
	
	speed = 0
	decreeseFactor = 0.2
	turningLeft = False
	turningRight = False
	
	def __init__(self):
		logging.debug('Car init')
		t_init()
		self.wheel_front_left = Wheel(GPIO_FRONT_LEFT_DIR, GPIO_FRONT_LEFT_PWM)
		self.wheel_front_right = Wheel(GPIO_FRONT_RIGHT_DIR, GPIO_FRONT_RIGHT_PWM)
		self.wheel_back_left = Wheel(GPIO_BACK_LEFT_DIR, GPIO_BACK_LEFT_PWM)
		self.wheel_back_right = Wheel(GPIO_BACK_RIGHT_DIR, GPIO_BACK_RIGHT_PWM)

	def __del__(self):
		print('Car destroyed')

        def forward(self):
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.forward()
		self.wheel_front_right.forward()
		self.wheel_back_left.forward()
		self.wheel_back_right.forward()
		self.updateSpeed()

        def backward(self):
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.backward()
		self.wheel_front_right.backward()
		self.wheel_back_left.backward()
		self.wheel_back_right.backward()
		self.updateSpeed()

        def left(self):
		self.turningLeft = True
		self.turningRight = False
		self.wheel_front_left.forward()
		self.wheel_front_right.forward()
		self.wheel_back_left.forward()
		self.wheel_back_right.forward()
		self.updateSpeed()

	def right(self):
		self.turningLeft = False
		self.turningRight = True
		self.wheel_front_left.forward()
		self.wheel_front_right.forward()
		self.wheel_back_left.forward()
		self.wheel_back_right.forward()
		self.updateSpeed()

	def setSpeed(self, speed):
		self.speed = speed
		self.updateSpeed()
		
	def updateSpeed(self):
		self.wheel_front_left.setSpeed(
				self.decreeseFactor * self.speed if self.turningLeft else self.speed)
		self.wheel_front_right.setSpeed(
				self.decreeseFactor * self.speed if self.turningRight else self.speed)
		self.wheel_back_left.setSpeed(
				self.decreeseFactor * self.speed if self.turningLeft else self.speed)
		self.wheel_back_right.setSpeed(
				self.decreeseFactor * self.speed if self.turningRight else self.speed)

	def stop(self):
		self.turningLeft = False
		self.turningRight = False
		self.wheel_front_left.stop()
		self.wheel_front_right.stop()
		self.wheel_back_left.stop()
		self.wheel_back_right.stop()


