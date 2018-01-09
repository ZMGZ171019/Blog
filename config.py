# -*- coding:UTF-8 -*-


#程序的配置
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
	FLASKY_MAIL_SENDER = 'Flasky Admin <124326022@qq.com>'
	FLASKY_ADMIN =  os.environ.get('FLASKY_ADMIN')
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	FLASKY_POSTS_PER_PAGE=os.environ.get('FLASKY_POSTS_PER_PAGE') or 10
	FLASKY_POSTS_PER_PAGE = 20
	FLASKY_FOLLOWERS_PER_PAGE = 50
	FLASKY_COMMENTS_PER_PAGE = 30
	JSON_AS_ASCII = False
	#启用缓慢查询记录功能的配置
	SQLALCHEMY_RECORD_QUERIES = True
	FLASKY_DB_QUERY_TIMEOUT = 0.5


	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.qq.com'
	MAIL_PORT = '25'
	MAIL_USE_TLS = 'True'
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or "mysql+pymysql://root:1234567@localhost:3306/db?charset=utf8"


class TestingConfig(Config):
	TESTING = True
	WTF_CSRF_ENABLED = False #在测试配置中禁用CSRF保护
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'mysql+pymysql://root:1234567@localhost:3306/db'


class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1234567@localhost:3306/db'
	
	#程序出错时发送电子邮件
	@classmethod
	def init_app(cls, app):
		Config.init_app(app)
		
		#把错误通过电子邮件发送给管理员
		import logging
		from logging.handlers import SMTPHandler
		cledentials = None
		secure = None
		if getattr(cls, 'MAIL_USERNAME', None) is not None:
			credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
			if getattr(cls, 'MAIL_USE_TLS', None):
				secure = ()
		mail_handler = SMTPHandler(
			mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
			formaddr=cls.FLASKY_MAIL_SENDER,
			toaddrs=[cls.FLASKY_ADMIN],
			subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + 'Application Error',
			credentials=credentials,
			secure=secure)
		mail_handler.setLevel(loggong.ERROR)
		app.logger.addHandler(mail_handler)


config = {
	'development': DevelopmentConfig,
	'testing':TestingConfig,
	'production': ProductionConfig,
	
	'default': DevelopmentConfig
}
