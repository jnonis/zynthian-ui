# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Engine (zynthian_engine_puredata)
#
# zynthian_engine implementation for Organele PureData patches
#
# Copyright (C) 2015-2018 Fernando Moyano <jofemodo@zynthian.org>
#
#******************************************************************************
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
#******************************************************************************

import os
import re
import logging
import time
import subprocess
import oyaml as yaml
from collections import OrderedDict
from os.path import isfile,isdir,join
from json import JSONEncoder, JSONDecoder

from . import zynthian_engine
from . import zynthian_controller

#------------------------------------------------------------------------------
# Organelle Engine Class
#------------------------------------------------------------------------------

class zynthian_engine_organelle(zynthian_engine):

	# ---------------------------------------------------------------------------
	# Controllers & Screens
	# ---------------------------------------------------------------------------

	_ctrls=[
		['knob 1',21,64],
		['knob 2',22,64],
		['knob 3',23,64],
		['knob 4',24,64],
		['aux',25,'off',['off','on']],
		['fs',64,'off',['off','on']],
		['expression',26,0],
		['volume',7,96],
		['enc',27,0],
		['enc but',28,'off',['off','on']]
	]

	_ctrl_screens=[
		['control 1',['knob 1','knob 2','knob 3','knob 4']],
		['control 2',['aux','fs','expression','volume']],
		['control 3',['enc','enc but']]
	]

	is_set_preset=False

	#----------------------------------------------------------------------------
	# Initialization
	#----------------------------------------------------------------------------

	def __init__(self, zyngui=None):
		super().__init__(zyngui)

		self.type = "Special"
		self.name="Organelle"
		self.nickname="OR"
		
		self.preset=""
		self.preset_config=None
		self.osc_server_port=4001

		# Show display
		self.zyngui.screens['control'].oled.grid(sticky="wens")
		#self.zyngui.screens['control'].oled.pack()

		self.bank_dirs=[
			('_', os.getcwd()+"/my-data/presets/organelle")
		]

		if self.config_remote_display():
			self.base_command=("/usr/bin/pd", "-jack", "-rt", "-alsamidi", "-mididev", "1")
		else:
			self.base_command=("/usr/bin/pd", "-nogui", "-jack", "-rt", "-alsamidi", "-mididev", "1")

		self.start()
		self.osc_init()
		self.reset()

	# ---------------------------------------------------------------------------
	# Layer Management
	# ---------------------------------------------------------------------------

	def stop(self, wait=0.2):
		logging.info("STOP Organelle")
		super().stop(wait)
		if self.osc_server and not self.is_set_preset:
			self.osc_server.stop()
			self.osc_server.free()
			self.osc_server=None

	#----------------------------------------------------------------------------
	# OSC Managament
	#----------------------------------------------------------------------------

	def osc_add_methods(self):
		self.zyngui.screens['control'].oled.add_osc_methods(self.osc_server)
		super().osc_add_methods()
		logging.info("OSC Added methods")

	# ---------------------------------------------------------------------------
	# MIDI Channel Management
	# ---------------------------------------------------------------------------

	#----------------------------------------------------------------------------
	# Bank Managament
	#----------------------------------------------------------------------------

	def get_bank_list(self, layer=None):
		return self.get_dirlist(self.bank_dirs)

	def set_bank(self, layer, bank):
		pass


	#----------------------------------------------------------------------------
	# Preset Managament
	#----------------------------------------------------------------------------

	def get_preset_list(self, bank):
		return self.get_dirlist(bank[0])

	def set_preset(self, layer, preset, preload=False):
		if preset[0] != self.preset:
			self.is_set_preset=True
			self.start_loading()
			self.load_preset_config(preset)
			self.command=self.base_command + ("-send", ";patch " + self.get_preset_filepath(preset).replace(' ', '\ '), "/zynthian/zynthian-sw/pd-mother-rpi/mother-rpi.pd")
			print('[%s]' % ', '.join(map(str, self.command)))
			self.preset=preset[0]
			self.stop()
			self.start(True,False)
			self.refresh_all()
			self.stop_loading()
			self.is_set_preset=False

	def load_preset_config(self, preset):
		config_fpath = preset[0] + "/zynconfig.yml"
		try:
			with open(config_fpath,"r") as fh:
				yml = fh.read()
				logging.info("Loading preset config file %s => \n%s" % (config_fpath,yml))
				self.preset_config = yaml.load(yml)
				return True
		except Exception as e:
			logging.error("Can't load preset config file '%s': %s" % (config_fpath,e))
			return False

	def get_preset_filepath(self, preset):
		if self.preset_config:
			preset_fpath = preset[0] + "/" + self.preset_config['main_file']
			if isfile(preset_fpath):
				return preset_fpath

		preset_fpath = preset[0] + "/main.pd"
		if isfile(preset_fpath):
			return preset_fpath

		preset_fpath = preset[0] + "/" + os.path.basename(preset[0]) + ".pd"
		if isfile(preset_fpath):
			return preset_fpath

		preset_fpath = join(preset[0],os.listdir(preset[0])[0])
		return preset_fpath


	#----------------------------------------------------------------------------
	# Controllers Managament
	#----------------------------------------------------------------------------

	def get_controllers_dict(self, layer):
		try:
			ctrl_items=self.preset_config['midi_controllers'].items()
		except:
			return super().get_controllers_dict(layer)
		c=1
		ctrl_set=[]
		zctrls=OrderedDict()
		self._ctrl_screens=[]
		logging.debug("Generating Controller Config ...")
		try:
			for name, options in ctrl_items:
				try:
					if isinstance(options,int):
						options={ 'midi_cc': options }
					if 'midi_chan' not in options:
						options['midi_chan']=0
					midi_cc=options['midi_cc']
					logging.debug("CTRL %s: %s" % (midi_cc, name))
					title=str.replace(name, '_', ' ')
					zctrls[name]=zynthian_controller(self,name,title,options)
					ctrl_set.append(name)
					if len(ctrl_set)>=4:
						logging.debug("ADDING CONTROLLER SCREEN #"+str(c))
						self._ctrl_screens.append(['Controllers#'+str(c),ctrl_set])
						ctrl_set=[]
						c=c+1
				except Exception as err:
					logging.error("Generating Controller Screens: %s" % err)
			if len(ctrl_set)>=1:
				logging.debug("ADDING CONTROLLER SCREEN #"+str(c))
				self._ctrl_screens.append(['Controllers#'+str(c),ctrl_set])
		except Exception as err:
			logging.error("Generating Controller List: %s" % err)
		return zctrls

	#--------------------------------------------------------------------------
	# Special
	#--------------------------------------------------------------------------


#******************************************************************************
