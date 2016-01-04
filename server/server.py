#!/usr/bin/python
'''
#=============================================================================
#     FileName: server.py
#         Desc:
#       Author: wangheng
#        Email: wujiwh@gmail.com #     HomePage: http://wangheng.org
#      Version: 0.0.1
#   LastChange: 2015-01-13 20:58:54
#      History:
#=============================================================================
'''
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logging.debug('Logger ready!')

from pi_car import app

is_main = os.environ.get("WERKZEUG_RUN_MAIN")
app.run(host='0.0.0.0', port=2000)
