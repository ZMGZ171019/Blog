from flask_wtf import FlaskForm
from ..models import Role, User
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField


class NameForm(FlaskForm):
	name = StringField('您叫什么名字?', validators=[DataRequired()])
	submit = SubmitField('提交')


#资料编辑表单
class EditProfileForm(FlaskForm):
	name = StringField('真正名字', validators=[Length(0, 64)])
	location = StringField('位置', validators=[Length(0, 64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('提交')


#管理员使用的资料编辑表单
class EditProfileAdminForm(FlaskForm):
	email = StringField('电子邮箱', validators=[DataRequired(), Length(1, 64),
											 Email()])
	username = StringField('用户名', validators=[
		DataRequired(), Length(1, 64),
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
			   '用户名必须只包含字母，数字，点或下划线.')])
	confirmed = BooleanField('确认')
	role = SelectField('角色', coerce=int)
	name = StringField('角色名', validators=[Length(0, 64)])
	location = StringField('位置', validators=[Length(0, 64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('提交')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name)
							 for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email and \
		User.query.filter_by(email=field.data).first():
			raise ValidationError('电子邮件已经注册.')

	def validate_username(self, field):
		if field.data != self.user.username and \
		User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已在使用.')


#博客文章表单
class PostForm(FlaskForm):
	body = PageDownField("你在想什么？", validators=[DataRequired()])
	submit = SubmitField('提交')


#评论输入表单
class CommentForm(FlaskForm):
	body = StringField('', validators=[DataRequired()])
	submit = SubmitField('提交')
