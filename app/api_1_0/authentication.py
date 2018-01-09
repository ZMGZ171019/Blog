from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User
from . import api
from .errors import forbidden, unauthorized

auth = HTTPBasicAuth()


#初始化Flask-HTTPAuth
@auth.verify_password
def verify_password(email, password):
	if email == '':
		g.current_user = AnonymousUser()
		return True
	user = User.query.filter_by(email = email).first()
	if not user:
		return False
	g.current_user = user
	return user.verify_password(password)


#Flask-HTTPAuth错误处理程序
@auth.error_handler
def auth_error():
	return unauthorized('域相关参数设置有误')


@api.before_request
@auth.login_required
def before_request():
	if not g.current_user.is_anonymous and \
	not g.current_user.confirmed:
		return forbidden('未经证实的消息')


#支持令牌的改进验证回调
@auth.verify_password
def verify_password(email_or_token, password):
	if email_or_token == '':
		g.current_user = AnonymousUser()
		return True
	if password == '':
		g.current_user = User.verify_auth_token(email_or_token)
		g.token_used = True
		return g.current_user is not None
	user = User.query.filter_by(email=email_or_token).first()
	if not user:
		return False
	g.current_user = user
	g.token_used = False
	return user.verify_password(password)


#生成认证令牌
@api.route('/token')
def get_token():
	if g.current_user.is_anonymous() or g.token_used:
		return unauthorized('Invalid credentials')
	return jsonify({'token': g.current_user.generate_auth_token(
		expiration=3600), 'expiration':3600})














