# -*- coding:UTF-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, current_user, logout_user
from . import auth
from .. import db
from ..email import send_email
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm,\
	PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


#登录路由
@auth.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():#验证表单数据
		user = User.query.filter_by(email=form.email.data).first()#查找数据库中是否有用户填写的email对应的用户名
		if user is not None and user.verify_password(form.password.data):#如果用户名不为空并且密码正确
			login_user(user, form.remember_me.data)#该函数的参数是要登录的用户名以及’记住我‘布尔值 如果布尔值为False那么关闭浏览器后用户会话就过期
			return redirect(request.args.get('next') or url_for('main.index'))#返回最后访问页或者首页
		flash('用户名或密码无效')
	return render_template('auth/login.html', form=form)#返回登陆页


#登出路由
@auth.route('/logout')
@login_required
def logout():
	logout_user()#删除并重设用户会话
	flash('你已经注销了')
	return redirect(url_for('main.index'))


#用户注册路由，发送确认邮件的注册路由
@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,
					username=form.username.data,
					password=form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, '确认你的帐户',
				   'auth/email/confirm', user=user, token=token)
		flash('确认邮件已通过电子邮件发送给你.')
		return redirect(url_for('main.index'))
	return render_template('auth/register.html', form=form)


#确认用户的帐户
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm(token):
		flash('你已经确认了您的帐户.谢谢 !')
	else:
		flash('确认链接无效或已过期.')
	return redirect(url_for('main.index'))


#更新登录用户的访问时间
@auth.before_app_request
def before_request():
	if current_user.is_authenticated:
		current_user.ping()
		if not current_user.confirmed \
		and request.endpoint[:5] != 'auth.':
			return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	return render_template('auth/unconfirmed.html')


#重新发送帐户确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_confirmation_token()
	send_email(current_user.email, '确认你的帐户',
			   'auth/email/confirm', user=current_user, token=token)
	flash('一封新的确认邮件已经通过电子邮件发给你了.')
	return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			db.session.commit()
			flash('你的密码已更新')
			return redirect(url_for('main.index'))
		else:
			flash('密码无效')
	return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			token = user.generate_reset_token()
			send_email(user.email, '重置你的密码',
					   'auth/email/reset_password',
					   user=user, token=token,
					   next=request.args.get('next'))
		flash('有一个指示你的密码重置的电子邮件发送给你.')
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetForm()
	if form.validate_on_submit():
		if User.reset_password(token, form.password.data):
			db.session.commit()
			flash('您的密码已更新')
			return redirect(url_for('auth.login'))
		else:
			return redirect(url_for('main.index'))
	return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.password.data):
			new_email = form.email.data
			token = current_user.generate_email_change_token(new_email)
			send_email(new_email, '确认你的电子邮件地址',
					   'auth/email/change_email',
					   user=current_user, token=token)
			flash('确认你新邮箱地址的邮件已发送给您')
			return redirect(url_for('main.index'))
		else:
			flash('无效的电子邮件或密码')
	return render_template("auth/change_email.html", form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
	if current_user.change_email(token):
		db.session.commit()
		flash('您的电子邮件地址已更新')
	else:
		flash('无效的请求')
	return redirect(url_for('main.index'))





























