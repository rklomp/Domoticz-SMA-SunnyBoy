# SMA Sunny Boy 1.5 Python Plugin v1.0 for Domoticz
#
# Author: merlot
#

"""
<plugin key="SunnyBoy15" name="SMA Sunny Boy 1.5 Solar Inverter" author="merlot" version="1.0.0">
    <description>
        <h2>SMA Sunny Boy 1.5 Solar Inverter Plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Register instant power and dayly generated energy</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true"/>
        <param field="Password" label="User group password" width="200px" required="true" password="true"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import sys
sys.path.append('/usr/local/lib/python3.5/dist-packages/')

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import json
import requests

class BasePlugin:
    enabled = False
    lastPolled = 0
    lastResponse = 0

    def __init__(self):
        return

    def onStart(self):
       Domoticz.Log("onStart called")
       if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
       else:
            Domoticz.Debugging(0)
       if (len(Devices) == 0):
         Domoticz.Device("pv watt", 1, "Custom", Options = { "Custom" : "1;W"}).Create()
         Domoticz.Device("wh today", 2, "Custom", Options = { "Custom" : "1;Wh"}).Create()
         Domoticz.Device("kwh total", 3, "Custom", Options = { "Custom" : "1;kWh"}).Create()
       DumpConfigToLog()
       Domoticz.Log("Plugin is started.")
# If Heartbeat>30 you'll get the error thread seems to have ended unexpectedly
# https://www.domoticz.com/wiki/Developing_a_Python_plugin#Callbacks
       Domoticz.Heartbeat(20)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
      Domoticz.Log("onHeartbeat called "+ str(self.lastPolled))
      ## Read SMA Inverter ##
      url_base="http://" + Parameters["Address"] + "/dyn/"
      url=url_base + "login.json"
      payload = ('{"pass" : "' + Parameters["Password"] + '", "right" : "usr"}')
      headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}

      self.lastPolled = self.lastPolled + 1
      if (self.lastPolled > 3): self.lastPolled = 1
      if (self.lastPolled == 1):
        try:
          r = requests.post(url, data=payload, headers=headers)
        except:
          Domoticz.Log("Error accessing SMA inverter on "+Parameters["Address"])
        else:
          j = json.loads(r.text)
          try:
            sid = j['result']['sid']
          except:
            Domoticz.Log("No response from SMA inverter on "+Parameters["Address"])
          else:
            url = url_base + "getValues.json?sid=" + sid
            payload = ('{"destDev":[],"keys":["6400_00260100","6400_00262200","6100_40263F00"]}')
            headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}

            try:
              r = requests.post(url, data=payload, headers=headers)
            except:
              Domoticz.Log("No data from SMA inverter on "+Parameters["Address"])
            else:
              j = json.loads(r.text)

              sma_pv_watt = j['result']['012F-730B00E6']['6100_40263F00']['1'][0]['val']
              if sma_pv_watt is None:
                sma_pv_watt = 0
              sma_kwh_today = j['result']['012F-730B00E6']['6400_00262200']['1'][0]['val']
              sma_kwh_total = j['result']['012F-730B00E6']['6400_00260100']['1'][0]['val']/1000

#              Domoticz.Log(r.text)
#              Domoticz.Log(str(sma_pv_watt))
#              Domoticz.Log(str(sma_kwh_today))

              Devices[1].Update(nValue=sma_pv_watt, sValue=str(sma_pv_watt))
              Devices[2].Update(nValue=sma_kwh_today, sValue=str(sma_kwh_today))
              sValue="%.2f" % sma_kwh_total
              Devices[3].Update(nValue=0, sValue=sValue.replace('.',','))


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

