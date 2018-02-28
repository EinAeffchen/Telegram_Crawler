import codecs
import Connector
import datetime
import os
import time
import sys

from telethon import errors
from telethon.tl import types

from telethon.tl.functions.channels import ReadHistoryRequest

class Channel:

    #debugging Methods & co
    def return_values(self, objekt):
        for thing in dir(objekt):
            print(thing+" : "+str(getattr(objekt, thing)))


    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')


    def return_name(self):
        return self.dialog.name

    #end of debugging


    def load_metadata(self):
        """loads previous data from groups.meta by group name"""
        #If too slow, saved data should be sorted, so unnecessary data can be skipped
        settings = dict()
        with codecs.open("groups.meta", "r", encoding="utf-8") as groups:
            data = groups.readlines()
            for line in data:
                if len(line) > 6:
                    info = line.split(";")
                    settings[info[0]] = True
                    settings["average"] = info[1]
                    settings["block"] = datetime.datetime.strptime(info[2][:-2],"%Y-%m-%d %H:%M:%S.%f")  #2018-02-09 21:27:34.131622
            groups.close()
        return settings


    def set_default(self):
        """Sets default values. average messages = 0, highest message id = 0"""
        self.curr_avg = 0 #Average messages per interval x
        self.channel = False
        self.block = datetime.datetime.now() #can be replaced by floodprevention block-time


    def find_tag(self, message):
        """Reads out the tag of a message and returns it"""
        tokenized_sentence = message.split()
        for word in tokenized_sentence:
            if word[0] == "@" or "t.me/" in word and word not in self.groups_blocked:
                self.groups.append(word)


    def contains_group(self, message):
        if "@" in message or "t.me/" in message:
            return True
        else:
            return False


    def group_checker(self, message):
        """Checks for group self.groups in messages and trys to join those groups"""
        if self.contains_group(message):
            self.find_tag(message)


    def is_channel(self):
        if isinstance(self.dialog.entity, types.Channel):
            return True
        else:
            return False


    def save_status(self):
        """Saves the channels metadata"""
        self.metadata = str(self.dialog.name) +";"+ str(self.msg_count) +";"+str(self.block)


    def check_activity(self):
        """Tests if the received messages are below the set limit
            returns false when the group is not active enough"""
        print("Received messages: {}, minimum necessary: {}".format(self.msg_count, self.average_msg_rcvd/self.msg_avg_deviation))
        if self.msg_count <= self.average_msg_rcvd/self.msg_avg_deviation:
            self.groups_blocked.add(self.dialog.name)
            return False
        else:
            return True


    def return_message_history(self):
        try:
            if self.unread != 0:
                messages = self.client.get_message_history(self.dialog.entity, self.unread)
                return messages
            else:
                return None
        except TypeError as e:
            print(e)
            time.sleep(1)
            return self.return_message_history()
        except RuntimeError:
            print("   ->[!] Too many retries skipping {} ".format(self.dialog.name))


    def read_messages(self, entity):
        """Read non-bot messages ordered by date"""
        messages = self.return_message_history()
        if messages != None:
            for i in range(len(messages)-1, -1, -1): #Correcting the output order by reversing it
                message = messages[i]
                try:
                    if message.sender != None and isinstance(message, types.Message) and not message.sender.bot: #only reads messages not send by bots
                        self.group_checker(message.message)  #Checks if group mentions are in messages
                        self.msg_count += 1
                        self.output += "{channel} ~~~ {chatid} {date} {messageid} {user} {reply_to} ~~~ {content} \n".format(
                            channel=self.dialog.name, #Dialog Name
                            chatid=self.dialog.entity.id, #Dialog id
                            date=message.date, #Message date
                            user=message.from_id, #Sender ID
                            messageid=message.id,
                            reply_to=message.reply_to_msg_id if message.reply_to_msg_id != None else 0,
                            content=message.message, #content
                        )
                        self.client.send_read_acknowledge(entity, message=message) #marks messages of whole entity as read
                except AttributeError as e:
                    print(e)
                except errors.rpc_error_list.RpcCallFailError as e: #Telegram internal error
                    print(e)
                    time.sleep(2)
                    self.read_messages(entity)


    def __init__(self, dialog, msg_average, msg_avg_deviation, client):
        self.active = True
        self.average_msg_rcvd = msg_average
        self.client = client
        self.name = dialog.name
        self.dialog = dialog
        self.groups = list() #saves channels that should be joined
        self.groups_blocked = set() #Groups already tried to join are blacklisted
        self.metadata = ""
        self.msg_avg_deviation = int(msg_avg_deviation)
        self.msg_count = 0
        self.output = ""
        self.unread = self.dialog.unread_count
        if self.is_channel():
            print("\n[*] ----- Initializing {} -----".format(dialog.name))
            try:
                data = self.load_metadata()
                self.channel = data[dialog.name] #Causes Keyerror when no data for that channel is available
                self.curr_avg = int(data["average"])
                self.block = data["block"]
                print("   ->[+] Group data successfully loaded!")
            except KeyError:
                print("   ->[!] Hash not found!")
                print("   ->[!] Setting default data...")
                self.set_default()
            except FileNotFoundError:
                print("   ->[!] Group Savefile not found!")
                print("   ->[!] Setting default data...")
                self.set_default()
        else:
            raise TypeError


    def run(self, count):
        self.read_messages(self.dialog.entity)
        if count != 1: #Skips the active check after the first run
            if not self.check_activity():
                self.active = False
            self.save_status()