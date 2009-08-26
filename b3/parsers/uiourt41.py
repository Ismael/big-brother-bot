#
# Uiourt41 Parser for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2009 Ismael (http://www.bigbrotherbot.com/forums/index.php?action=profile;u=597)
#
#
# v1.0.1 - 18/08/2009 -Ismael 
#   * http://www.bigbrotherbot.com/forums/index.php?topic=797.msg7711#msg7711
#

__author__  = 'Ismael'
__version__ = '1.0.1'

import b3.parsers.iourt41

from threading import Thread
import time

class PlayerDict(object):
  #A Singleton which holds the output from /rcon status (which we believe is always accurate)
  __instance = None

  def __init__(self):
    if PlayerDict.__instance is None:
      PlayerDict.__instance = PlayerDict.__impl()
    object.__setattr__(self, '_PlayerDict__instance', PlayerDict.__instance)
    #self.__dict__['_PlayerDict__instance'] = PlayerDict.__instance
    
  def __getattr__(self, attr):
    """ Delegate access to implementation """
    return getattr(self.__instance, attr)
  def __setattr__(self, attr, value):
    """ Delegate access to implementation """
    return setattr(self.__instance, attr, value)

  class __impl(object):
    def __init__(self):
      #Every 5 minutes the player list is refreshed by another thread
      self.t = PlayerDict.SchedUp(self.upddict)
      self.d = {}

    def init(self,  upd):
      """Assign the function to run to get the player dict (getPlayerList)"""
      self.upd = upd
      self.upddict()
      
      #Now we know the update function, if the Thread isn't running, start it
      if not self.t._Thread__started: 
        self.t.start()
      
    def upddict(self):
      """Update the info on the players"""
      self.d = {}
      a = self.upd()
      for k in a:
        self.d[a[k]['name'][:-2]] = int(a[k]['slot'])

    def lookup(self,  name):
      """Get the correct ID for a player"""
      try:
        return self.d[name]
      except:
        self.upddict()
        return self.d[name]

  class SchedUp(Thread):
    def __init__(self,  func):
      Thread.__init__(self)
      self.func = func
    def run(self):
      while 1:
        self.func()
        time.sleep(5*60)

class ProxyMatch(object):
  def __init__(self, match):
    object.__setattr__(self, 'm', match)
    #self.m = m

  #If the method isn't defined here, it will look into the m object
  def __getattr__(self, attr):
    return getattr(self.m, attr)
  def __setattr__(self, attr, value):
    return setattr(self.m, attr, value)

  def group(self, attr):
    if attr != 'cid':
      return self.m.group(attr)
    
    #cid gets replaced by correct one by our PlayerDict
    pd = PlayerDict()
    try:
      name = self.m.group('name')
      cid = pd.lookup(name)
      return cid
    except: #Got no info about the name of the player (hit or kill event), leave unchanged (and wrong)
      return self.m.group(attr)
    

#----------------------------------------------------------------------------------------------------------------------------------------------
class Uiourt41Parser(b3.parsers.iourt41.Iourt41Parser):
  gameName = 'iourt41'

  def startup(self):
    super(Uiourt41Parser, self).startup() #call the parser startup()
    
    #Init the player dict
    p = PlayerDict()
    p.init(self.getPlayerList)

  def getLineParts(self,  line):
    m = super(Uiourt41Parser, self).getLineParts(line)
    if not m:
      return False

    match, action, data, client, target = m
    
    #These events alter the connected players, better update our knowledge of connected users now
    if action in ["clientuserinfo",  "clientuserinfochanged",  "clientdisconnect"]:
      PlayerDict().upddict()

    match = ProxyMatch(match) #Mask the match regexp by our own
    return (match, action, data, client, target)
