# -*- coding:UTF-8 -*-
#创建认证蓝本

from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views