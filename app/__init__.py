# -*- coding:UTF-8 -*-
#程序包的构造文件


from config import config
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template


mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
bootstrap = Bootstrap()
login_manager = LoginManager()


login_manager.session_protection = 'strong'#提供不同的安全等级防止用户会话被篡改。设为‘strong',Flask-Login会记录客户端IP地址和浏览器的用户代理信息。
login_manager.login_view = 'auth.login'#设置登录页面的端点，因登陆路由在蓝本中定，所以要加上蓝本名。


def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	login_manager.init_app(app)
	bootstrap.init_app(app)
	pagedown.init_app(app)
	moment.init_app(app)
	mail.init_app(app)
	db.init_app(app)
	
	#注册蓝本
	from .main import main as main_blueprint
	app.register_blueprint(main_blueprint)
	
	#附加蓝本
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint, url_prefix='/auth')

	#注册API蓝本
	from .api_1_0 import api as api_1_0_blueprint
	app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

	return app