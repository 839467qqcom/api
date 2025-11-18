
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
#get project dir
BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#get common dir
COMMONDIR = os.path.join(BASEDIR, 'common')
#get config dir
CONFDIR = os.path.join(BASEDIR, 'config')
#get data dir
DATADIR = os.path.join(BASEDIR, 'data')
#get library dir
LIBDIR = os.path.join(BASEDIR, 'library')
#get log dir
LOGDIR = os.path.join(BASEDIR, 'log')
#get report dir
REPORTDIR = os.path.join(BASEDIR, 'report')
#get testcaset dir
CASEDIR = os.path.join(BASEDIR, 'testcase')



# print(CASEDIR)  # 注释掉调试输出