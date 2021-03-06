# -*- coding:UTF-8 -*-

import unittest
from app.models import User, Role


class UserModelTestCase(unittest.TestCase):
	#密码散列化测试
	def test_password_setter(self):
		u = User(password = 'cat')
		self.assertTrue(u.password_hash is not None)
	
	def test_no_password_getter(self):
		u = User(password = 'cat')
		with self.assertRaises(attributeError):
			u.password
	
	def test_password_verification(self):
		u = User(password = 'cat')
		self.assertTrue(u.verify_password('cat'))
		self.assertFalse(u.verify_password('dog'))
	
	def test_password_salts_are_random(self):
		u = User(password = 'cat')
		u2 = User(password = 'cat')
		self.assertTrue(u.password_hash != u2.password_hash)

	#角色和权限的单元测试
	def test_roles_and_permissions(self):
		Role.insert_roles()
		u = User(email='1234567@qq.com', password='cat')
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

	def test_anonymous_user(self):
		u = AnonymousUser()
		self.assertFalse(u.can(Permission.FOLLOW))
