import RPi.GPIO as GPIO
import time

Motor_R1_Pin = 16
Motor_R2_Pin = 18
Motor_L1_Pin = 11
Motor_L2_Pin = 13
t = 0.1
dc = 80


GPIO.setmode(GPIO.BOARD)
GPIO.setup(Motor_R1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_R2_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L2_Pin, GPIO.OUT, initial=GPIO.LOW)

pwm_r1 = GPIO.PWM(Motor_R1_Pin, 500)
pwm_r2 = GPIO.PWM(Motor_R2_Pin, 500)
pwm_l1 = GPIO.PWM(Motor_L1_Pin, 500)
pwm_l2 = GPIO.PWM(Motor_L2_Pin, 500)
pwm_r1.start(0)
pwm_r2.start(0)
pwm_l1.start(0)
pwm_l1.start(0)

def stop():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)

def forward():
    pwm_r1.ChangeDutyCycle(98.5)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def notime_forward(dc = 40):
    pwm_r1.ChangeDutyCycle(dc-4)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    
def backward():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(dc)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(dc)
    time.sleep(t)
    stop()

def notime_backward():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(dc)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(dc)
    
def turnLeft():
    pwm_r1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()
    
def notime_turnLeft():
    pwm_r1.ChangeDutyCycle(dc)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(0)
    pwm_l2.ChangeDutyCycle(0)
    
def turnRight():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(t)
    stop()

def notime_turnRight():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(0)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)

def cleanup():
    stop()
    pwm_r1.stop()
    pwm_r2.stop()
    pwm_l1.stop()
    pwm_l2.stop()
    GPIO.cleanup()          

def dodgeleft():
    notime_turnLeft()
    time.sleep(0.3)
    notime_forward(80)
    time.sleep(0.5)
    
    notime_turnRight()
    time.sleep(0.1)
    notime_forward(80)
    time.sleep(0.5)
    
    notime_turnRight()
    time.sleep(0.5)
    notime_forward(80)
    time.sleep(0.3)
    
    notime_turnLeft()
    time.sleep(0.5)
    notime_forward(80)
    time.sleep(0.5)
    stop()

def dodgeright():
    notime_turnRight()
    time.sleep(0.3)
    notime_forward()
    time.sleep(0.5)
    
    notime_turnLeft()
    time.sleep(0.3)
    notime_forward()
    time.sleep(0.5)
    
    notime_turnLeft()
    time.sleep(0.3)
    notime_forward()
    time.sleep(0.5)
    
    notime_turnRight()
    time.sleep(0.3)
    stop()

def turn_around():
    pwm_r1.ChangeDutyCycle(0)
    pwm_r2.ChangeDutyCycle(dc)
    pwm_l1.ChangeDutyCycle(dc)
    pwm_l2.ChangeDutyCycle(0)
    time.sleep(0.75)
    stop()
    
def partrol():
    notime_forward()
    time.sleep(2)
    turn_around()
    notime_forward()
    time.sleep(2)