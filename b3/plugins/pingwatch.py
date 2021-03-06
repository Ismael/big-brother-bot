#
# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# CHANGELOG
#    11/30/2005 - 1.1.3 - ThorN
#    Use PluginCronTab instead of CronTab
#    8/29/2005 - 1.1.0 - ThorN
#    Converted to use new event handlers

__author__  = 'ThorN'
__version__ = '1.1.4'



import b3, time, thread
import b3.events
import b3.plugin
import b3.cron

#--------------------------------------------------------------------------------------------------
class PingwatchPlugin(b3.plugin.Plugin):
    _interval = 0
    _maxPing = 0
    _maxPingDuration = 0
    _ignoreTill = 0
    _cronTab = None

    def onStartup(self):
        self.registerEvent(b3.events.EVT_GAME_EXIT)

        # dont check pings on startup
        self._ignoreTill = self.console.time() + 120

    def onLoadConfig(self):
        self._interval = self.config.getint('settings', 'interval')
        self._maxPing = self.config.getint('settings', 'max_ping')
        self._maxPingDuration = self.config.getint('settings', 'max_ping_duration')

        if self._cronTab:
            # remove existing crontab
            self.console.cron - self._cronTab

        self._cronTab = b3.cron.PluginCronTab(self, self.check, '*/%s' % self._interval)
        self.console.cron + self._cronTab

    def onEvent(self, event):
        if event.type == b3.events.EVT_GAME_EXIT:
            # ignore ping watching for 2 minutes
            self._ignoreTill = self.console.time() + 120

    def check(self):        
        if self.isEnabled() and (self.console.time() > self._ignoreTill):        
            for cid,ping in self.console.getPlayerPings().items():
                #self.console.verbose('ping %s = %s', cid, ping)
                if ping > self._maxPing:                
                    client = self.console.clients.getByCID(cid)
                    if client:
                        if client.var(self, 'highping', 0).value > 0:
                            self.console.verbose('set high ping check %s = %s (%s)', cid, ping, client.var(self, 'highping', 0).value)
                            if self.console.time() - client.var(self, 'highping', 0).value > self._maxPingDuration:
                                if ping == 999:                            
                                    #client.kick('^7Connection interupted')
                                    self.console.say('^7%s ^7ping detected as Connection Interrupted (CI)' % client.name)
                                else:
                                    #client.kick('^7Ping too high %s' % ping)
                                    self.console.say('^7%s ^7ping detected as too high %s' % (client.name, ping))
                        else:
                            self.console.verbose('set ping watch %s = %s', cid, ping)
                            client.setvar(self, 'highping', self.console.time())