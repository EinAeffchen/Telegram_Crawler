# Tele_Learn

## Description:
A yet simple script to join groups based on group mentions and collect the data for further analysis.

## Requirements:
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [Anaconda](https://anaconda.org/anaconda/python) 3.6.4

## Installing:
- If not yet done, download Telethon  ```pip install telethon```
- Download the zip
- Fill the config.txt
- **Do not!** use the bot api keys for the config. To run the program you will need the Telegram API
	available here: [Creating your Telegram Application](https://core.telegram.org/api/obtaining_api_id)
- Join some active Telegram groups


## Usage
Run ```python Connector.py -m <0/1> (0=single-, 1=multiprocessing) -t <time in seconds> -r <repetitions> -l <0/1>```
	<br/>for exmaple ```python Connector.py -m 1 -t 900 -r 50 -l 1```  
	<br/>that would run the code in a multiprocessed way every 900seconds for 50 times, while leaving inactive groups


## Changelog
28.01.2018
- Connector.run() got an alternative method. One that works normally and one that works with multiprocessing (Connector.run_multi())
- Fixed a bug where files with certain names cause problems with mergin the group metadata
- Added extra comments, exported some code to own functions for better readability

02.02.2018
- Small fix in the before changelog to clear up misconceptions 
- Edited the join_group() function to better prevent flooderrors by skipping unnecessary group join tries.
- reactivated group leave due to inactivity
- Added a few variables in the TelethonB instantiation for join_group improvement
- Removed highest_msg_id. It was redundant because the self.unread amount limitation in get_message_history
	already limits the retrieved messages to new ones.
- Massively improved speed and reduced api calls by using ReadHistoryRequest() for the whole channel instead of
	sending individual send_read_acknowledge()s

11.02.2018
**Version 2.0**
The whole code structure got changed. Single TelethonB/Channel Objects don't write data by themselfes anymore. The whole data handling
is done by the Connector.py. This highly increased accuracy and speed and also reduced API calls to further prevent flood detection.
- automatically leaving groups available and working correctly
- added Automatical run() call every interval x
- Channel Blacklist can be saved and loaded
- Restructured metadata a little

14.02.2018
- Fixed data memory error. Old chat data won't appear in new chat_blocks anymore
- ported runtime setting from config.txt to program call argument
- Added arguments for starting the script

23.02.2018
- Added switch to leave groups
- Fixed bug with mode 0
- Fixed bug where group metadata was not written anymore

## TODO
- [x] Be able to join new groups
- [x] Automatically leave inactive groups (Has to be tested still)
- [x] Automatically call run on Channel objects in time interval x
- [x] Read in List of blocked groups 
- [x] Add further info to the group metadata like Member count etc.
- [x] Improve flood detection prevention
- [x] Add Switch to leave groups
