'''
#=============================================================================
#     FileName: views.py
#         Desc: 
#       Author: wangheng
#        Email: wujiwh@gmail.com
#     HomePage: http://wangheng.org
#      Version: 0.0.1
#   LastChange: 2015-01-14 13:46:29
#      History:
#=============================================================================
'''
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
from pi_car import app
from controller import Car

@app.before_first_request
def initialize():
	print('initialize')
	global car
	car = Car()
	car.setSpeed(100)

@app.route('/')
def show_index():
	return render_template('home.html')

@app.route("/login", methods=["GET", "POST"])                                   
def login():                                                                    
	if request.method=="GET":                                                   
		return "get"+request.form["user"]
	elif request.method=="POST":                                                
		return "post"

@app.route('/ctl',methods=['GET','POST'])
def ctrl_id():
	if request.method == 'POST':
		id=request.form['id']
		
		if id == 't_left':
			car.left()
			return "left"
		elif id == 't_right':
			car.right()
			return "right"
		elif id == 't_up':
			car.forward()
			return "up"
		elif id == 't_down':
			car.backward()
			return "down"
		elif id == 't_stop':
			car.stop()
			return "stop"

	return redirect(url_for('show_index'))
