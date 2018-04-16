#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Tesla Control plugin for indigo
#
# This plugin was written and published by Gregg Glockner
# https://github.com/gglockner/indigo-teslacontrol
# https://github.com/gglockner/teslajson
#
# No updates to the plugin have been made in over 12 months, including no provision of data/states from the vehicle,
# so i've taken it on and developed it further.
#
# Based on sample code that is:
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo
import teslajson

## TODO
# 1. Exception handling
# 2. Method to set temperature (with menu for F/C)
# 3. Events and refreshing

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.vehicles = []
		self.debug = True
		
		self.states = {}

	########################################
	def startup(self):
		self.debugLog("Username: %s" % self.pluginPrefs.get("username","(Not yet saved)"))

	def getDeviceStateList(self, dev): #Override state list
		stateList = indigo.PluginBase.getDeviceStateList(self, dev)      
		if stateList is not None:
			for key in self.states.iterkeys():
				dynamicState1 = self.getDeviceStateDictForStringType(key, key, key)
				stateList.append(dynamicState1)
		return stateList

	def getVehicles(self):
		if not self.vehicles:
			connection = teslajson.Connection(self.pluginPrefs['username'],
											  self.pluginPrefs['password'])
			self.vehicles = dict((unicode(v['id']),v) for v in connection.vehicles)
			indigo.server.log("%i vehicles found" % len(self.vehicles))
		return self.vehicles

	# Generate list of cars	
	def carListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
		cars = [(k, "%s (%s)" % (v['display_name'], v['vin']))
				for k,v in self.getVehicles().items()]
		self.debugLog("carListGenerator: %s" % str(cars))
		return cars

	### ACTIONS
	def validateActionConfigUi(self, valuesDict, typeId, actionId):
		if typeId=='set_charge_limit':
			try:
				percent = int(valuesDict['percent'])
				if percent > 100 or percent < 50:
					raise ValueError
				valuesDict['percent'] = percent
			except ValueError:
				errorsDict = indigo.Dict()
				errorsDict['percent'] = "A percentage between 50 and 100"
				return (False, valuesDict, errorsDict)
		return (True, valuesDict)
	
	def vehicleCommand(self, action, dev):
		vehicleId = dev.pluginProps['car']
		commandName = action.pluginTypeId
		indigo.server.log("Tesla command %s for vehicle %s" % (commandName, vehicleId))
		vehicle = self.getVehicles()[vehicleId]
		if commandName == "wake_up":
			vehicle.wake_up()
			return
		data = action.props
		vehicle.command(commandName, data)

	def vehicleStatus(self, action, dev):
		vehicleId = dev.pluginProps['car']
		statusName = action.pluginTypeId
		indigo.server.log("Tesla request %s for vehicle %s" % (statusName, vehicleId))
		vehicle = self.getVehicles()[vehicleId]
		#data = action.props
		response = vehicle.data_request(statusName)
		self.debugLog(str(response))
		for k,v in response.items():
			self.states[k] = v
			dev.stateListOrDisplayStateIdChanged()
			if k in dev.states:
				dev.updateStateOnServer(k,v)
			else:
				self.debugLog("Not found: %s" % str(k))
			if (k == dev.ownerProps.get("stateToDisplay","")):
				dev.updateStateOnServer("displayState",v)

