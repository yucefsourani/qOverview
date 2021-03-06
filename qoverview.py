#!/usr/bin/env python3

import os
import sys
import subprocess as sp
import dbus
import json

from PyQt5.QtCore import QObject, QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQuick import QQuickView

#import config
import wm

tmp_dir = os.path.join(os.environ.get('XDG_RUNTIME_DIR', '/tmp'), 'qoverview')

socket_path = os.path.join(tmp_dir, 'sock')
pid_file_path = os.path.join(tmp_dir, 'server.pid')

class PythonQMLInterface(QObject):

	def __init__(self, view):
		self.view = view
		super(PythonQMLInterface, self).__init__()
		self.options = json.loads(config.get_config())
		self.apps_list = json.loads(config.get_apps_list())

	@pyqtSlot(str)
	def window_clicked(self, w_id):
		print(w_id)
		self.view.hide()
		wm.activate(w_id)
		sys.exit()

	@pyqtSlot(str)
	def window_clicked_midbutton(self, w_id):
		print(w_id)
		wm.close(w_id)

	@pyqtSlot(result=bool)
	def is_midbutton_enabled(self):
		return options.get('middle-mouse-close', True)

	@pyqtSlot(str)
	def app_clicked(self, app_item):
		print(app_item)
		self.view.hide()
		config.desktop_entry_execute(config.desktop_entry_locate(app_item))
		sys.exit()

	@pyqtSlot()
	def background_clicked(self):
		self.view.hide()
		sys.exit()

	@pyqtSlot(str, result=list)
	def search(self, search_terms):
		results = []

		done = []

		for entry in self.apps_list:
			try:
				if entry['Name'].lower().startswith(search_terms.lower()) and entry['Name'] not in done:
					results.append([entry['Name'], entry['EntryName'], entry['IconPath']])
					done.append(entry['Name'])

			except KeyError:
				pass

		return sorted(results)

	@pyqtSlot(result=list)
	def get_background_overlay_color(self):
		return self.options.get('background-color-overlay', [0, 0, 0, 0])

	@pyqtSlot(result=str)
	def get_background(self):
		return config.get_background()

	@pyqtSlot(result=list)
	def get_dock_items(self):
		dock_items_list = json.loads(config.get_dock_items())
		results = []

		for entry in self.apps_list:
			if entry['EntryName'] in dock_items_list:
				results.append([entry['Name'], entry['EntryName'], entry['IconPath']])

		return results

	@pyqtSlot(str, result=list)
	def get_windows(self, workspace):
		ids = wm.get_window_ids(int(workspace) - 1)
		results = []

		for index, w_id in enumerate(ids):
			if wm.get_window_name(w_id) not in ['qoverview.py', 'Desktop — Plasma']:
				results.append([wm.get_window_name(w_id), wm.get_window_screenshot(w_id, str(index)), w_id])

		return results

	@pyqtSlot(result=list)
	def get_workspaces(self):
		return [str(x + 1) for x in range(wm.get_num_workspaces())]

	@pyqtSlot(str)
	def workspace_clicked(self, num):
		print(num)
		wm.switch_workspace(int(num) - 1)
		sp.Popen('python3 {}'.format(__file__), shell=True, preexec_fn=os.setpgrp)
		# Restarting!
		sys.exit()

	@pyqtSlot(str, str)
	def dropped_on_workspace(self, workspace, w_id):
		print((workspace, w_id))

	@pyqtSlot(result=str)
	def get_current_workspace(self):
		return str(wm.get_current_workspace() + 1)

	@pyqtSlot(result=bool)
	def is_workspaces_enabled(self):
		return self.options.get('workspaces-sidebar', True)

	@pyqtSlot(result=bool)
	def	is_dock_enabled(self):
		return bool(json.loads(config.get_dock_items()))


if __name__ == "__main__":

	os.makedirs(tmp_dir, exist_ok=True)

	# DBUS Setup
	try:
		bus = dbus.SessionBus()
		session = bus.get_object('org.qoverview.config', '/org/qoverview/config')
		config = dbus.Interface(session, 'org.qoverview.config.iface')

	except:
		print('config-server is (probably) not running! (Unable to connect to it via DBUS)')
		print('Start it and try again. The command is "qoverview-config-server"')
		sys.exit(1)

	app = QGuiApplication(sys.argv)

	qmlview = QQuickView()
	qmlview.setSource(QUrl('ui.qml'))

	qmlview.setResizeMode(qmlview.SizeRootObjectToView)

	root = qmlview.rootObject()
	context = qmlview.rootContext()

	interface = PythonQMLInterface(view=qmlview)

	context.setContextProperty('Python', interface)

	qmlview.showFullScreen()

	app.exec_()
