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
import re
import controller
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
			controller.t_left()
			return "left"
		elif id == 't_right':
			controller.t_right()
			return "right"
		elif id == 't_up':
			controller.t_forward()
			return "up"
		elif id == 't_down':
			controller.t_backward()
			return "down"
		elif id == 't_stop':
			controller.t_stop()
			return "stop"

	return redirect(url_for('show_index'))
