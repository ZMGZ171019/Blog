# -*- coding:UTF-8 -*-

import bleach
import hashlib
from datetime import datetime
from markdown import markdown
from . import db, login_manager
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from app.exceptions import ValidationError

#权限常量
class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x08


#角色的权限
class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User', backref='role', lazy='dynamic')
	
	#在数据库中创建角色
	@staticmethod
	def insert_roles():
		roles = {
			'User': (Permission.FOLLOW |
					 Permission.COMMENT |
					 Permission.WRITE_ARTICLES, True),
			'Moderator': (Permission.FOLLOW |
						  Permission.COMMENT |
						  Permission.WRITE_ARTICLES |
						  Permission.MODERATE_COMMENTS, False),
			'Administrator': (0Xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name


#关注关联表的模型
class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
							primary_key=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
							primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)


#User模型
class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(64), unique=True, index=True)
	username = db.Column(db.String(64), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))#所在地
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	avatar_hash = db.Column(db.String(32))
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	#使用两个一对多关系实现多对多关系
	followed = db.relationship('Follow',
							   foreign_keys=[Follow.follower_id],
							   backref=db.backref('follower', lazy='joined'),
							   lazy='dynamic',
							   cascade='all, delete-orphan')
	followers = db.relationship('Follow',
								foreign_keys=[Follow.followed_id],
								backref=db.backref('followed', lazy='joined'),
								lazy='dynamic',
								cascade='all, delete-orphan')
	comments = db.relationship('Comment', backref='author', lazy='dynamic')

	#用户权限
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:#默认用户权限
				self.role = Role.query.filter_by(default=True).first()
		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(
				self.email.encode('utf-8')).hexdigest()
		self.followed.append(Follow(followed=self))#构建用户时将用户设为自己的关注者

	#试图读取密码时触发异常
	@property
	def password(self):
		raise AttributeError('密码不可读')
	
	#注册密码
	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)
	
	#验证密码
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
	
	def __repr__(self):
		return '<User %r>' % self.username

	#确认用户帐户
	def generate_confirmation_token(self, expiration=3600):#生成确认令牌
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.id})

	#比对确认令牌
	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		return True

	#刷新用户的最后访问时间
	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	def can(self, permissions):
		return self.role is not None and (self.role.permissions & permissions) == permissions

	#检查管理员权限
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	#生成Gravatar URL
	def gravatar(self, size=100, default='identicon', rating='g'):
		if request.is_secure:
			url = 'https://secure.gravatar.com/avatar'
		else:
			url = 'https://gravatar.com/avatar'
		hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
			url=url, hash=hash, size=size, default=default, rating=rating)

	def generate_email_change_token(self, new_email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps(
			{'change_email': self.id, 'new_email': new_email}).decode('utf-8')

	def change_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		if data.get('change_email') != self.id:
			return False
		new_email = data.get('new_email')
		if new_email is None:
			return False
		if self.query.filter_by(email=new_email).first() is not None:
			return False
		self.email = new_email
		self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
		db.session.add(self)
		return True

	def gravatar(self, size=100, default='identicon', rating='g'):
		if request.is_secure:
			url = 'https://secure.gravatar.com/avatar'
		else:
			url = 'http://www.gravater.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
			url=url, hash=hash, size=size, default=default, rating=rating)

	#生成虚拟用户
	@staticmethod
	def generate_fake(count=100):
		from sqlalchemy.exc import IntegrityError
		from random import seed
		import forgery_py
		
		seed()
		for i in range(count):
			u = User(email=forgery_py.internet.email_address(),
					 username=forgery_py.internet.user_name(True),
					 password=forgery_py.lorem_ipsum.word(),
					 confirmed=True,
					 name=forgery_py.name.full_name(),
					 location=forgery_py.address.city(),
					 about_me=forgery_py.lorem_ipsum.sentence(),
					 member_since=forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()

	#获取所关注用户的文章
	@property
	def followed_post(self):
		return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

	#将用户设为自己的关注者
	@staticmethod
	def add_self_follows():
		for user in User.query.all():
			if not user.is_following(user):
				user.follow(user)
				db.session.add(user)
				db.session.commit()

	def follow(self, user):
		if not self.is_following(user):
			f = Follow(follower=self, followed=user)
			db.session.add(f)

	def unfollow(self, user):
		f = self.followed.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)

	def is_following(self, user):
		return self.followed.filter_by(
			followed_id=user.id).first() is not None

	def is_followed_by(self, user):
		return self.followers.filter_by(
			follower_id=user.id).first() is not None

	@property
	def followed_posts(self):
		return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

	#支持基于令牌的认证
	def generate_quth_tolen(self, expiration):
		s = Serializer(current_app.config·['SECRET_KEY'],
					   expires_in=expiration)
		return s.dumps({'id': self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])

	#将用户转换成JSON格式的序列化字典
	def to_json(self):
		json_user = {
			'url': url_for('api.get_user', id=self.id, _external=Trne),
			'username': self.username,
			'member_since': self.member_since,
			'last_seen': self.last_seen,
			'post': url_for('api.get_user_posts', id=self.id, _external=True),
			'followed_posts': url_for('api.get_user_followed_posts',
									  id=self.id, _external=True),
			'post_count': self.posts.count()
		}
		return json_user

	def __repr__(self):
		return '<User %r>' % self.username


#文章模型
class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	#body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	comments = db.relationship('Comment', backref='post', lazy='dynamic')

	#生成虚拟博客文章
	@staticmethod
	def generate_fake(count=100):
		from random import seed, randint
		import forgery_py
		
		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0, user_count - 1)).first()
			p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
					 timestamp=forgery_py.date.date(True),
					 author=u)
			db.session.add(p)
			db.session.commit()

	#在Post模型中处理Markdown文本
	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
						'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
						'h1', 'h2', 'h3', 'p']
		target.body_html = bleach.linkify(bleach.clean(
			markdown(value, output_format='html'),
			tags=allowed_tags, strip=True))

	#将文章转换成JSON格式的序列化字典
	def to_json(self):
		json_post = {
			'url': url_for('api.get_post', id=self.id, _external=True),
			'body': self.body,
			'body_html': self.body_html,
			'timestamp': self.timestamp,
			'author': url_for('api.get_user', id=self.author_id,
							  _external=True),
			'comments': url_for('api.get_post_comments', id=self.id,
								_external=True),
			'comment_count': self.comments.count()
		}
		return json_post

	#从JSON格式数据创建一篇博客文章
	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not have a body')
		return Post(body=body)

db.event.listen(Post.body, 'set', Post.on_changed_body)


#方便在用户没检查用户是否登录前调用can等函数
class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False

	def is_administrator(self):
		return False

login_manager.anonymous_user = AnonymousUser


#加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


#Comment模型
class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
		target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
													   tags=allowed_tags, strip=True))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)
	






























