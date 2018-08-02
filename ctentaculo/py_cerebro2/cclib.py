# -*- coding: utf-8 -*-

import base64

def hash16_64(b16_str):
	if len(b16_str)!=64:
		raise Exception('Wrong hash length (muse be 64)');

	ba = base64.b16decode(b16_str.encode('ascii'));
	return base64.standard_b64encode(ba).decode('ascii').replace('+', '-').replace('/', '_').replace('=', '~')

def hash64_16(b64_str):
	ba = base64.standard_b64decode(b64_str.replace('-', '+').replace('_', '/').replace('~', '=').encode('ascii'))
	ret = base64.b16encode(ba).decode('ascii')
	if len(ret)!=64:
		raise RuntimeError('Wrong hash length (muse be 64): ' + ret);
	return ret;

def has_flag(flags, flag):
	"""
	Проверяет, выставлен ли флаг flag в передаваемых флагах flags.	
	"""
	
	return ((flags & (1 << flag))!=0)

def string_byte(string):
	if isinstance(string, unicode):
		string = string.encode('utf-8')
	return string
