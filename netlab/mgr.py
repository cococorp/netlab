#!/usr/bin/env python

import sys, os
import argparse, logging, uuid
import datetime
import json
import bottle

VAR_PATH = '/var/lib/netmgr'
LOG_PATH = '/var/log/netmgr.log'

class CustomEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()
		return super(CustomEncoder, self).default(obj)

class Session(object):
	def __init__(self):
		self.id = str(uuid.uuid1())
		self.created = datetime.datetime.now()
		
	def dump(self):
		return {
			'id': self.id,
			'created': self.created
		}

@bottle.route('/sessions')
def sessions_list():
	logging.info("sessions_list()")
	ls = os.listdir(VAR_PATH)
	return { 'keys': ls }

@bottle.route('/sessions', method='POST')
def sessions_new():
	#data = bottle.request.json
	logging.info("sessions_new(): %s" % bottle.request.params)
	session = Session()
	path = os.path.join(VAR_PATH, session.id)
	with open(path, 'w') as fp:
		json.dump(session.dump(), fp, cls=CustomEncoder)
	return { 'id': session.id }

@bottle.route('/sessions', method='DELETE')
def sessions_clear():
	logging.info("sessions_clear()")
	ls = os.listdir(VAR_PATH)
	for entry in ls:
		os.remove(os.path.join(VAR_PATH, entry))

@bottle.route('/sessions/<id>')
def sessions_get(id):
	logging.info("sessions_get(%s)" % id)
	return bottle.static_file(id, root=VAR_PATH)

@bottle.route('/sessions/<id>', method='DELETE')
def sessions_delete(id):
	logging.info("sessions_delete(%s)" % id)
	# TODO: check that 'id' does NOT have slashes (/) or updirs (..)
	path = os.path.join(VAR_PATH, id)
	os.remove(path)

@bottle.route('/sessions/<id>/start', method='POST')
def sessions_start(id):
	logging.info("sessions_start(%s)" % id)
	return { 'status': 'starting' }

@bottle.route('/sessions/<id>/stop', method='POST')
def sessions_stop(id):
	logging.info("sessions_stop(%s)" % id)
	return { 'status': 'stopping' }

@bottle.route('/sessions/<id>/console', method='POST')
def sessions_console(id):
	logging.info("sessions_console(%s)" % id)
	return { 'status': 'ok' }

#@bottle.route('/envs')
#def envs_list():
#	logging.info("envs_list()")
#	ls = os.listdir(VAR_PATH)
#	return { 'keys': ls }

def init_logging(options):
	# NOTE: this call can only be done ONCE
	# and it MUST be the 1st call into the logging module for it to work
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)-15s %(message)s',
						filename=options.log,
						filemode='w')

	console = logging.StreamHandler()
	if options.quiet:
		console.setLevel(logging.ERROR)
	else:
		if options.verbose == 1:
			console.setLevel(logging.INFO)
		elif options.verbose >= 2:
			console.setLevel(logging.DEBUG)
		else:
			console.setLevel(logging.WARN)
	logging.getLogger().addHandler(console)

def parse_args():
	parser = argparse.ArgumentParser(description='NetLab Manager')
	parser.add_argument('-v', '--verbose', action='count', default=0,
						help='Increase verbosity, can be specified multiple times')
	parser.add_argument('-q', '--quiet', action='store_true', default=False,
						help='Be really quiet')
	parser.add_argument('-L', '--log', default=LOG_PATH,
						help='Specify the logfile')
	return parser.parse_args()

def main():
	if os.getuid() != 0:
		sys.exit('netmgr must be run as root.')
		
	if not os.path.exists(VAR_PATH):
		os.makedirs(VAR_PATH)

	args = parse_args()

	init_logging(args)

	logging.info("Starting")
	
	bottle.run(host='0.0.0.0', port=999, debug=True)

	logging.info("Shutdown")
	logging.shutdown()
	