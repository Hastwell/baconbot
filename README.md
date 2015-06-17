# baconbot
Python-powered FTB Server Watchdog

BaconBot is a Python-based tool used to maintain smooth operations on FTB and other Forge-based modded Minecraft servers. It is designed to report on a variety of actions, including new whitelist requests, excessive chunkloading, and players handling creative items when they're not supposed to.

BaconBot functions out-of-band to the Minecraft instance, and must be periodically invoked by McMyAdmin (which pipes STDOUT to the console allowing the script to send console commands)

It is rather hackish in it's current state as it was designed with the sole purpose of running my own server (Bacon Gaming, running the TPPI modpack)

Dependencies:
  * pyNBT
  * SQLite and associated Python libraries
  * MySQL and associated Python libraries
  * McMyAdmin (script invocation and console redirection)
  * Prism (Minecraft block/item logging, turned up to 9000)
