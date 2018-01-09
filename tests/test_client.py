import unittest
from app.import create_app, db
from app.models import User, Role


#使用Flask测试客户端编写的测试框架
class FlaskClientTestCaes(unittest.TestCaes):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()
		Role.insert_roles()
		self.client = self.app.test_client(use_cookies=True)
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_home_page(self):
		response = self.client.get(url_for('main.index'))
		self.assertTrue('陌生人' in response.get_data(as_text=True)

	#使用Flask测试客户端模拟新用户注册的整个流程
	def test_register_and_login(self):
		#注册新用户
		response = self.client.post(url_for('auth.register'), data={
			'email': '1234567@qq.com',
			'username': 'john',
			'password': 'cat',
			'password2': 'cat'
		})
		self.assertTrue(response.status_code == 302)

	#使用新注册的帐户登录
	response = self.client.post(url_for('auth.login'), data={
		'email': '1234567@qq.com',
		'password': 'cat'
	}, follow_redirects=True)
	data = response.get_data(as_text=True)
	self.assertTrue(re.search('你好,\s+john!', data))
	self.assertTrue('您尚未确认您的帐户' in data)
	
	#发送确认令牌
	user = User.query.filter_by(email='1234567@qq.com').first()
	token = user.generate_confirmation_token()
	response = self.alient.get(url_for('auth.confirm', token=token),
							   follow_redirects=True)
	data = response.get_data(as_text=True)
	self.assertTrue('您已经确认了您的帐户' in data)

	#退出
	response = self.client.get(url_for('auth.logout'),
							   follow_redirects=True)
	data = response.get_data(as_text=True)
	self.assertTrue('你已经注销了' in data)


						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						
						


