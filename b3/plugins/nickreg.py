# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Plugin for registering nicknames
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
# 14/01/09
# Added !remnick and !findnick to remove nicks (by an admin) and find who is using a nick
# 25/08/09
# Escape player's nicks
# 25/07/09
# Initial version

__version__ = '1.2'
__author__  = 'Ismael'

import b3
import b3.plugin
from b3 import clients
import b3.cron

class NickregPlugin(b3.plugin.Plugin):
	_adminPlugin = None

	_watched = []

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
		
		minlevel = self.config.getint('settings', 'min_level_reg')
		
		self._adminPlugin.registerCommand(self, 'registernick', minlevel, self.cmd_regnick,  'regnick')
		self._adminPlugin.registerCommand(self, 'deletenick', minlevel, self.cmd_delnick,  'delnick')
                
                minlevel_adm = self.config.getint('settings', 'min_level_nick_manage')
                self._adminPlugin.registerCommand(self, 'findnick', minlevel_adm, self.cmd_findnick,  'findnick')
		self._adminPlugin.registerCommand(self, 'removenick', minlevel_adm, self.cmd_remnick,  'remnick')

		self.registerEvent(b3.events.EVT_CLIENT_NAME_CHANGE)

	def onEvent(self,  event):
		if not event.client:
			return #No client
		if not event.client.authed:
			return #Not authed, don't know its real ID
		client = event.client
		if client.id not in self._watched:
			cursor = self.console.storage.query("""
			SELECT n.id
			FROM nicks n 
			WHERE n.name = '%s'
			""" % (client.name.replace("""'""", """''"""))) #Have to escape quotes (')
			if cursor.rowcount > 0: #This nick is registered
				r = cursor.getRow()

				if int(r['id']) != int(client.id):
					self._watched.append(client.id)
					#This nick isn't yours!
					name = client.name
					id = client.id
					client.message("^2First warn: ^7Please change your ^7nickname, ^7this nick (^3%s^7) belongs to someone else" % name)
					
					#Messy logic ahead! Each defined function adds a cron for the next one, defined inside of them.
					def warn():
						client.message("^2Second warn: ^7Please change your ^7nickname, ^7this nick (^3%s^7) belongs to someone else" % name)
						def warn2():
							if  name == client.name:
								client.message("^1LAST warn: ^7Please change your ^7nickname, ^7this nick (^3%s^7) belongs ^7to someone else. ^7You will be ^1KICKED!" % name)
								def kick():
									if  name == client.name:
										client.kick("This nickname (%s) isn't yours!" % name,  None)
									self._watched.remove(client.id)
								self.console.cron + b3.cron.OneTimeCronTab(kick,  "*/4")
						self.console.cron + b3.cron.OneTimeCronTab(warn2,  "*/3")
					self.console.cron + b3.cron.OneTimeCronTab(warn,  "*/4")
			cursor.close()
		

	def cmd_regnick(self, data, client, cmd=None):
		"""\
		Register your current name as yours
		"""
		
		#Todo: Strip the colors from the names?
		#Todo: Strip the spaces?
		
		cursor = self.console.storage.query("""
		SELECT n.name
		FROM nicks n 
		WHERE n.name = '%s'
		""" % (client.name.replace("""'""", """''"""))) #Have to escape quotes (')
		
		if cursor.rowcount > 0:
			client.message('^7That nick is already registered')
			return False
		cursor.close()

		cursor = self.console.storage.query("""
		SELECT n.id
		FROM nicks n 
		WHERE n.id = %s
		""" % (client.id))
		
		if cursor.rowcount > 0:
			client.message('^7You already have a registered nickname')
			return False
		cursor.close()


		cursor = self.console.storage.query("""
		INSERT INTO nicks
		VALUES (%s, '%s')
		""" % (client.id,  client.name.replace("""'""", """''"""))) #Have to escape quotes (')

		cursor.close()
		client.message('^7Your nick is now registered')
	
	def cmd_delnick(self,  data,  client,  cmd=None):
                """\
		Delete your current nick
		"""
		cursor = self.console.storage.query("""
		SELECT n.name
		FROM nicks n 
		WHERE n.id = %s
		""" % (client.id))
		
		if cursor.rowcount == 0:
			client.message("^7You don't have a registered nickname")
			return False
		cursor.close()
		
		cursor = self.console.storage.query("""
		DELETE FROM nicks
		WHERE id = %s
		""" % (client.id))
		cursor.close()
		client.message("^7Nick deleted")

        def cmd_remnick(self, data, client, cmd=None):
                """\
		Delete a users nick from the DB.
		"""

                m = self._adminPlugin.parseUserCmd(data)
                if not m[0]:
                    client.message('^7Invalid parameters')
                    return False

                cid = m[0]
		sclient = self._adminPlugin.findClientPrompt(cid, client)

		cursor = self.console.storage.query("""
		DELETE FROM nicks
		WHERE id = %s
		""" % (sclient.id))
		cursor.close()
		client.message("^7User ^2@%s ^7nick deleted" % sclient.id)

        def cmd_findnick(self, data, client, cmd=None):
                """\
		Find if a nick is registered.
		"""
                m = self._adminPlugin.parseUserCmd(data)
                if not m[0]:
                    client.message('^7Invalid parameters')
                    return False
                name = m[0]

                cursor = self.console.storage.query("""
                SELECT c.id, n.name
                FROM clients c, nicks n
                WHERE c.id = n.id &&
                n.name LIKE '%%%s%%'"""%(name))

		if cursor.rowcount == 0:
                    client.message("^7Nobody has a nick like that registered")
                    cursor.close()
                    return False
                else:
                    while not cursor.EOF:
                        r = cursor.getRow()
                        msg = "^7[^2@%s^7] has ^7%s" % (r['id'],  r['name'])
			cmd.sayLoudOrPM(client,  msg)
                        cursor.moveNext()
                    cursor.close()
