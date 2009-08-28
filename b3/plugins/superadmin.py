# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Plugin for extra admin utilities
# Copyright (C) 2009 Ismael Garrido
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# CHANGELOG
# 29/05/09
# Added !listids , Lists all players IDs
# Changes in cmd_delnotice as suggested by xlr8or
# Bugfixes in notices comands
# 10/04/09
# Changed !pastbans shortcut to !pab
# On connect and on ban only tell number of past bans instead of all history
# 22/03/09
# Renamed to SuperAdmin
# New command !pastbans: see past player bans
# Added functions for manipulating notices
# !listbans changes format: !listbans [<admin>] [<type>]
# !listbans will only show tempbans by default
# 24/02/09
# !listbans now takes (optionally) admin name and shows only bans by that admin
# !allaliases now has optional <detailed> parameter which shows more info on each alias
# 23/02/09
# Changed !slookup to look for aliases containing the substring instead of only exact matches
# New command !listbans (or !lb). Lists all the active bans
# New command !superbaninfo (or !sbaninfo). Gives more information about the ban than !baninfo.
# 21/02/09 
# Initial version

 
__version__ = '1.4.7'
__author__  = 'Ismael'

import b3
import b3.plugin
import b3.events
import datetime
import thread,  time

#--------------------------------------------------------------------------------------------------
class SuperadminPlugin(b3.plugin.Plugin):
	_adminPlugin = None
	_minLevel_sl = None
	_minLevel_allalias = None
	_minLevel_sban = None
	_minLevel_lb = None
	_minLevel_notices = None
	_minLevel_pastbans = None
	_minLevel_listids = None

	def startup(self):
		"""\
		Initialize plugin settings
		"""

		# get the plugin so we can register commands
		self._adminPlugin = self.console.getPlugin('admin')
		if not self._adminPlugin:
			# something is wrong, can't start without admin plugin
			self.error('Could not find admin plugin')
			return False
		
		# get the minium level allowed to use this plugin
		self.verbose('Getting config options')
		self._minLevel_sl = self.config.getint('settings', 'min_level_superlookup')
		self._minLevel_allalias = self.config.getint('settings', 'min_level_allaliases')
		self._minLevel_sban = self.config.getint('settings', 'min_level_superbaninfo')
		self._minLevel_lb = self.config.getint('settings', 'min_level_listbans')
		self._minLevel_listids = self.config.getint('settings', 'min_level_listids')

		# register our commands
		self.verbose('Registering commands')
		self._adminPlugin.registerCommand(self, 'superlookup', self._minLevel_sl, self.cmd_superlookup,  'slookup')
		self._adminPlugin.registerCommand(self, 'allaliases', self._minLevel_allalias, self.cmd_allaliases,  'allalias')
		self._adminPlugin.registerCommand(self, 'superbaninfo', self._minLevel_sban, self.cmd_superbaninfo,  'sbaninfo')
		self._adminPlugin.registerCommand(self, 'listbans', self._minLevel_lb, self.cmd_listbans,  'lb')
		self._adminPlugin.registerCommand(self, 'listids', self._minLevel_listids, self.cmd_listids,  'lids')

		self.Load_supernotice()
		self.Load_banwatcher()
		
		self.debug('Started')

	def onEvent(self,  event):
		if event.type == b3.events.EVT_CLIENT_AUTH:
			self.tell_notices(event.client)
		elif event.type == b3.events.EVT_CLIENT_BAN_TEMP or event.type == b3.events.EVT_CLIENT_BAN:
			self.tell_bans(event.client)

	def  Load_banwatcher(self):
		self._minLevel_pastbans= self.config.getint('banwatcher', 'min_level_pastbans')
		
		self._adminPlugin.registerCommand(self, 'pastbans', self._minLevel_notices, self.cmd_pastbans,   'pab')

		if self.config.getboolean('banwatcher',  'enabled'):
			self.registerEvent(b3.events.EVT_CLIENT_BAN)
			self.registerEvent(b3.events.EVT_CLIENT_BAN_TEMP)
			
	def get_player_bans(self,  client):
		cursor = self.console.storage.query(
		"""SELECT a.name, p.reason, p.time_expire  FROM penalties p, clients a
		WHERE a.id = p.admin_id AND (p.type = "tempban" OR p.type = "ban") AND p.client_id = %s """%(client.id))
		bans = []
		if cursor.rowcount > 0:
			while not cursor.EOF:
				r = cursor.getRow()
				bans.append("^2%s ^7for ^4%s ^7until ^3%s" %(r['name'],  r['reason'],  self.console.formatTime(r['time_expire'])))
				cursor.moveNext()
		cursor.close()
		return bans
	
	def tell_bans(self, client):
		a = self._adminPlugin.getAdmins()
		bans = self.get_player_bans(client)

		if len(a) > 0 and len(bans) > 0:
			for adm in a:
				adm.message("^7%s has ^4%s ^7past bans"  %(client.name,  len(bans)))

	
	def cmd_pastbans(self, data, client, cmd=None):
		"""\
		<name> - list all player's past bans
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False		
		
		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			client.message('^7Invalid parameters')
			return False
	
		cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)
		if not sclient:
			return
		
		bans = self.get_player_bans(sclient)
		
		if len(bans) == 0:
			cmd.sayLoudOrPM(client, "^7%s^7 hasn't been banned" % sclient.exactName)
			return True
			
		cmd.sayLoudOrPM(client, "^7%s past bans:" %(sclient.exactName))
		for b in bans:
			cmd.sayLoudOrPM(client,  b)
		

	def  Load_supernotice(self):
		self._minLevel_notices = self.config.getint('supernotice', 'min_level_supernotice')
		
		self._adminPlugin.registerCommand(self, 'lookupnotices', self._minLevel_notices, self.cmd_lookupnotice,  'lnot')
		self._adminPlugin.registerCommand(self, 'deletenotice', self._minLevel_notices, self.cmd_delnotice,  'delnot')
		
		if self.config.getboolean('supernotice',  'lookup_on_login'):
			self.registerEvent(b3.events.EVT_CLIENT_AUTH)

	def tell_notices(self, client):
		a = self._adminPlugin.getAdmins()
		notices = self.get_player_notices(client)

		if len(a) > 0 and len(notices) > 0:
			for adm in a:
				adm.message("^7%s has notices:"  %(client.name))
				for n in notices:
					adm.message(n)

	def get_player_notices(self,  client):
		cursor = self.console.storage.query("""SELECT name, reason, p.time_add FROM penalties p, clients a WHERE type = "Notice" AND a.id = p.admin_id AND p.inactive = 0 AND p.client_id = %s """%(client.id))
		notices = []
		if cursor.rowcount > 0:
			i = 1
			while not cursor.EOF:
				r = cursor.getRow()
				notices.append("^7(^1#%s^7)^2%s^7(^3%s^7): ^7%s" % (i,  r['name'], self.console.formatTime(r['time_add']),   r['reason']))
				cursor.moveNext()
				i += 1
		cursor.close()
		return notices

	def cmd_delnotice(self, data, client, cmd=None):
		"""\
		<name> <number> - mark notice <number> as inactive in DB
		"""
		
		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			client.message('^7Invalid parameters')
			return False
		if not m[0] and m[1]:
			client.message('^7Invalid parameters')
			return False
		
		cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)
		
		cursor = self.console.storage.query("""SELECT p.id FROM penalties p WHERE type = "Notice" AND inactive = 0 AND p.client_id = %s """%(sclient.id))

		to_delete = int(m[1])
		
		if cursor.rowcount < to_delete:
			client.message('^7Number too high!')
			return False

		_needUpdate = False

		if cursor.rowcount > 0:
			i = 1
			while not cursor.EOF or i > to_delete:
				r = cursor.getRow()
				if i == to_delete:
					# we found the notice, let's build the updateQuery  
					_needUpdate = True
					_updateQuery = 'UPDATE penalties SET inactive=1 WHERE id = %s' %(r['id'])
					# We found the correct notice, break out of the loop
					break
				cursor.moveNext()
				i += 1
		cursor.close()

		if _needUpdate:
			c = self.console.storage.query(_updateQuery)
			c.close()
			cmd.sayLoudOrPM(client,  "^7Notice marked inactive")
		else:
			cmd.sayLoudOrPM(client,  "^7Notice not found")


	def cmd_lookupnotice(self, data, client, cmd=None):
		"""\
		<name> - lookup player's notices
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False		
			
		thread.start_new_thread(self._lookupnotice, (data, client,  cmd))
	
	def _lookupnotice(self, data, client, cmd=None):
		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			client.message('^7Invalid parameters')
			return False
			
		cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)
		if not sclient:
			return
		
		notices = self.get_player_notices(sclient)
		
		if len(notices) == 0:
			cmd.sayLoudOrPM(client, '^7%s^7 has no notices' % sclient.exactName)
			return True
		
		cmd.sayLoudOrPM(client,  '^7%s^7 notices:' %sclient.exactName)
		for n in notices:
			cmd.sayLoudOrPM(client,  n)
			time.sleep(1)
	

	def cmd_superlookup(self,  data,  client,  cmd=None):
		"""\
		<name> - search players that have used or are using that name
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False
		if not len(data):
			client.message('^7You must supply a player to lookup')
			return False
		
		thread.start_new_thread(self._superlookup, (data, client,  cmd))
		
	def  _superlookup(self,  data,  client,  cmd=None):
	#Get all players that are currently using that name
		clients = self.console.clients.lookupByName(data)
		
		#Get all players that have used the alias
		cursor = self.console.storage.query("""SELECT c.id, c.name, a.time_edit FROM clients c, aliases a WHERE c.id = a.client_id && a.alias LIKE '%%%s%%'"""%(data))

		if cursor.rowcount == 0 and len(clients) == 0:
			cmd.sayLoudOrPM(client,  "No players have used the alias")
			return
		
		ids = []
		
		if len(clients) > 0:
			cmd.sayLoudOrPM(client, "Players that are currently using %s: " % (data))
			for c in clients:
				cmd.sayLoudOrPM(client, "^7[^2@%s^7] %s (^3%s^7)" % (c.id,  c.exactName,  self.console.formatTime(c.timeEdit)))
				ids.append(c.id)
				time.sleep(1)
		else:
			cmd.sayLoudOrPM(client, "No players are currently using %s" % (data))
		
		if cursor.rowcount > 0:
			cmd.sayLoudOrPM(client, "Players that have used %s: " % (data))
			while not cursor.EOF:
				msg = ""
				r = cursor.getRow()
				if not (int(r['id'] ) in ids):
					msg += "^7[^2@%s^7] %s (^3%s^7)" % (r['id'],  r['name'],  self.console.formatTime(r['time_edit']))
					cmd.sayLoudOrPM(client,  msg)
					ids.append(int(r['id']))
					time.sleep(1)
				cursor.moveNext()
		else:
			cmd.sayLoudOrPM(client, "No players have used %s" % (data))

		cursor.close()
		
	def cmd_allaliases(self, data, client=None, cmd=None):
		"""\
		<name> [<detailed>] - list all player's aliases (no 10 alias limit), if <detailed> = y alias creation and modification time are shown
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False		
		
		thread.start_new_thread(self._allaliases, (data, client,  cmd))
	
	def _allaliases(self, data, client, cmd):
		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			client.message('^7Invalid parameters')
			return False
		
		cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)
		if not sclient:
			return
		
		cursor = self.console.storage.query("""SELECT a.alias, a.time_add, a.time_edit, a.num_used FROM aliases a WHERE a.client_id = %s """%(sclient.id))
		if cursor.rowcount == 0:
			cmd.sayLoudOrPM(client, '^7%s^7 has no aliases' % sclient.exactName)
			return True
			
		if not m[1]:
			aliases = []
			while not cursor.EOF:
				r = cursor.getRow()
				aliases.append("^7%s" % r['alias'])
				cursor.moveNext()

			cmd.sayLoudOrPM(client, "^7%s aliases: %s" %(sclient.exactName, ', '.join(aliases)))
		else:
			cmd.sayLoudOrPM(client, "^7%s aliases:" %(sclient.exactName))
			while not cursor.EOF:
				r = cursor.getRow()
				cmd.sayLoudOrPM(client, "^7%s, added ^3(%s) ^7last ^7modified ^3(%s) ^7used ^3%s ^7times" %(r['alias'], self.console.formatTime(r['time_add']), self.console.formatTime(r['time_edit']),  r['num_used']+1))
				time.sleep(1)
				cursor.moveNext()
		
		cursor.close()

	def cmd_superbaninfo(self, data, client=None, cmd=None):
		"""\
		<name> - Give information about player's active bans
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False

		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			client.message('^7Invalid parameters')
			return False

		sclient = self._adminPlugin.findClientPrompt(m[0], client)
		if sclient:
			numbans = sclient.numBans
			if numbans:
				cmd.sayLoudOrPM(client, '^7%s ^7has %s active bans' % (sclient.exactName, numbans))
				bans = sclient.bans
				for b in bans:
					admin = self.console.storage.getClientsMatching({ 'id' : b.adminId })[0].name					
					cmd.sayLoudOrPM(client,  '^7Banned by ^7%s ^7until ^3%s ^7for ^7reason ^7%s' % (admin,   self.console.formatTime(b.timeExpire),  b.reason))
				
			else:
				cmd.sayLoudOrPM(client, '^7%s ^7has no active bans' % sclient.exactName)

		
	def cmd_listbans(self, data, client=None, cmd=None):
		"""\
		[<name>] [<type>] - list all active bans, if name specified, list all active bans by that admin; type can be 'ban' or 'tempban', tempban is the default.
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False
		thread.start_new_thread(self._listbans, (data, client,  cmd))

	def _listbans(self, data, client=None,  cmd=None):
		adm = ""
		ban = "TempBan"
		if data:
			m = self._adminPlugin.parseUserCmd(data)
			
			if m[0]:
				cid = m[0]
				sclient = self._adminPlugin.findClientPrompt(cid, client)
			
				adm = "AND p.admin_id = %s" % sclient.id
			
			if m[1]:
				if m[1] == "ban":
					ban = "Ban"
				elif m[1] == "tempban":
					ban = "TempBan"
				else:
					cmd.sayLoudOrPM(client, "^7Wrong type of ban, must be 'ban' or 'tempban'")
					return False
		
		#Get all players that have active bans
		cursor = self.console.storage.query("""
		SELECT c.id, c.name, p.time_expire, p.reason
		FROM penalties p, clients c 
		WHERE p.client_id = c.id AND
		p.inactive = 0 AND 
		type='%s' AND
		p.time_expire >= UNIX_TIMESTAMP() %s""" % (ban, adm))

		if cursor.rowcount == 0:
			cmd.sayLoudOrPM(client, "No active bans")
			return
		
		cmd.sayLoudOrPM(client, "There are %s active bans" % cursor.rowcount)
		while not cursor.EOF:
			r = cursor.getRow()
			msg = "^7[^2@%s^7] %s (until ^3%s^7) ^7for ^7%s" % (r['id'],  r['name'],  self.console.formatTime(r['time_expire']),  r['reason'])
			cmd.sayLoudOrPM(client,  msg)
			time.sleep(1)

			cursor.moveNext()

		cursor.close()
		
	def cmd_listids(self,  data, client, cmd=None):
		"""\
		[name] - Lists all player's IDs or name's ID
		"""
		if not self.console.storage.status():
			cmd.sayLoudOrPM(client, '^7Cannot lookup, database apears to be ^1DOWN')
			return False

		m = self._adminPlugin.parseUserCmd(data)
		if not m:
			clientes = []
			for c in self.console.clients.getList():
				clientes.append("^7%s: ^2@%d^7" %(c.exactName,  c.id))
			cmd.sayLoudOrPM(client,  ", ".join(clientes))
			return True
	
		cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)
		if not sclient:
			return
		cmd.sayLoudOrPM(client,  "^7%s: ^2@%d" % (sclient.exactName, sclient.id))
