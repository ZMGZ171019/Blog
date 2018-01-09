# -*- coding:UTF-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


#登录表单
class LoginForm(FlaskForm):
	email = StringField('电子邮箱', validators=[DataRequired(), Length(1, 64),
											 Email()])#StringField字段 validatorsc由验证函数组成的列表 DataRequired验证非空 Length验证输入的字符串长度 Email验证邮件地址
	password = PasswordField('密码', validators=[DataRequired()])#该类表示属性为type='password'的<input>元素
	remember_me = BooleanField('记住我')#该类表示复选框
	submit = SubmitField('登陆')#该类表示属性为type='submit'的<input>元素 提交按键


#用户注册表单
class RegistrationForm(FlaskForm):
	email = StringField('电子邮箱', validators=[DataRequired(), Length(1, 64),
											 Email()])
	username = StringField('用户名', validators=[
		DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
										  '用户名必须只有字母，数字、点或下划线组合')])
	password = PasswordField('密码', validators=[
		DataRequired(), EqualTo('password2', message='密码必须匹配.')])
	password2 = PasswordField('确认密码', validators=[DataRequired()])
	submit = SubmitField('注册')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('电子邮箱箱已经注册.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已在使用.')


class ChangePasswordForm(FlaskForm):
	old_password = PasswordField('旧密码', validators=[DataRequired()])
	password = PasswordField('新密码', validators=[
		DataRequired(), EqualTo('password2', message='密码必须匹配')])
	password2 = PasswordField('确认新密码',
							  validators=[DataRequired()])
	submit = SubmitField('更新密码')


class PasswordResetRequestForm(FlaskForm):
	email = StringField('电子邮箱', validators=[DataRequired(), Length(1, 64),
											 Email()])
	submit = SubmitField('重置密码')


class PasswordResetForm(FlaskForm):
	password = PasswordField('新密码', validators=[
		DataRequired(), EqualTo('password2', message='密码必须匹配')])
	password2 = PasswordField('确认密码', validators=[DataRequired()])
	submit = SubmitField('重置密码')


class ChangeEmailForm(FlaskForm):
	email = StringField('新电子邮箱', validators=[DataRequired(), Length(1, 64),
												 Email()])
	password = PasswordField('密码', validators=[DataRequired()])
	submit = SubmitField('更新电子邮件地址')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('电子邮件已经注册')