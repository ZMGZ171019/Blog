#!/usr/bin/env python
# -*- coding:UTF-8 -*-

#启动脚本
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
	import coverage
	COV = coverage.coverage(branch=True, include='app/*')
	COV.start()


from app import create_app, db
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app.models import User, Role, Permission, Post


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


manager.add_command('db', MigrateCommand)


@app.shell_context_processor
def make_shell_context():
	return dict(db=db, User=User, Follow=Follow, Role=Role,
				Permission=Permission, Post=Post, Comment=Comment)


#覆盖测试
@manager.command
def test(coverage=False):
	"""Run the unit tests."""
	if coverage and not os.environ.get('FLASK_COVERAGE'):
		import sys
		os.environ['FLASK_COVERAGE'] = '1'
		os.execvp(sys.executable, [sys.executable] + sys.argv)
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)
	if COV:
		COV.stop()
		COV.save()
		print('Coverage Summary:')
		COV.report()
		basedir = os.path.abspath(os.path.dirname(__file__))
		covdir = os.path.join(basedir, 'tmp/coverage')
		COV.html_report(directory=covdir)
		print('HTML version: file://%s/index.html' % covdir)
		COV.erase()


#在请求分析器的监视下运行程序
@manager.command
def profile(length=25, profile_dir=None):
	#代码探查器在启动应用
	from werkzeug.contrib.profiler import ProfilerMiddleware
	app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
									  profile_dir=profile_dir)
	app.run()

#部署命令
@manager.command
def deploy():
	#运行部署任务
	from flask_migrate import upgrade
	from app.models import Role, User
	
	#把数据库迁移到最新修订版本
	upgrade()
	
	#创建用户角色
	Role.insert_roles()
	
	#让所有用户都关注此用户
	User.add_self_follows()


if __name__ == '__main__':
	manager.run()