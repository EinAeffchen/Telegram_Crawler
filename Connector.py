# -*- coding:utf-8 -*-
import codecs
import datetime
import json
import sched
import optparse
import os
import time
import TelethonB
import threading
import sys

from telethon import TelegramClient
from telethon import errors
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.channels import JoinChannelRequest



class TelegramOperator:

    
    #Debugging Methods & co
    def return_values(self, objekt):
        for thing in dir(objekt):
            print(thing+" : "+str(getattr(objekt, thing)))


    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    #end of debugging

    def __init__(self):
        #self.print_lock = threading.Lock()
        settings = self.read_settings()
        try:
            settings["telegram_api"] = int(settings["telegram_api"])
        except ValueError:
            print("[!] API Code is incorrect. Please check config.txt and correct the error!")
            sys.exit()
        self.client = TelegramClient(settings["username"], settings["telegram_api"], settings["api_hash"])
        self.client.start()
        self.msg_avg_deviation = settings["min_activity"]
        self.msg_average = self.calc_average()
        self.groups = list()
        self.leftout_groups = set()
        self.dialog_names = set()
        self.blacklist = self.load_blocked_groups()
        self.initialize_run()
        self.leave = False


    def create_settings(self):
        default = {"telegram_api":"Your api here",
                   "api_hash": "Your hash here",
                   "username":"Your username here",
                   "#1/Xth ot the average activity(messages per runtime) required to not be marked as inactive. default: 1/3th":"",
                   "min_activity":"3",
                  }
        with codecs.open("config.txt", "w", encoding="utf-8") as config:
            for key in default:
                if default[key] != "":
                    config.write("{}={}\n".format(key, default[key]))
                else:
                    config.write("{}\n".format(key))
        print("[*] Please fill in your api data into the config.txt")


    def read_settings(self):
        settings = dict()
        try:
            with codecs.open("config.txt", "r", encoding="utf-8") as config:
                data = config.readlines()
                for entry in data:
                    if "#" not in entry:
                        entry = [entry.strip() for entry in entry.split("=")]
                        settings[entry[0]] = entry[1]
                config.close()
        except FileNotFoundError:
            print("[!] config.txt not found. Creating it...")
            self.create_settings()
            sys.exit()
        return settings


    def write_data(self, data, filename):
        with codecs.open(filename, "w", encoding="utf-8") as output:
            for dataset in data:
                if len(dataset) > 0:
                    if isinstance(dataset, list):
                        temp = ""
                        for ele in dataset:
                            temp += ele+";"
                            dataset = temp[:-2]
                            print(dataset)
                    output.write(str(dataset)+"\n")


    def get_highest_chatblock(self):
        try:
            block_number = max([int(filename.split("-")[1]) for filename in os.listdir() if "chat_block" in filename])+1
            return block_number
        except ValueError:
            return 0


    def join_groups(self, groups, blacklist):
        """Tries to join groups if it is not blacklisted"""
        floodwait = False
        for group in groups:
            if group not in blacklist and group not in self.dialog_names:
                if not floodwait:
                    print("[*] Trying to join {}..".format(group))
                    try:
                        channel = self.client.get_entity(group)
                        self.client(JoinChannelRequest(channel))
                        self.dialog_names.add(group) #avoid trying to join the same group twice
                        print("     [+]->Succesfully joined {} ".format(group))
                    except errors.rpc_error_list.FloodWaitError as e:
                        floodwait = True
                        self.leftout_groups.add(group)
                        date = datetime.datetime.now()
                        self.block =  date + datetime.timedelta(seconds = e.seconds) #adds waittime to current time to determine the date when the block ends
                        print("     [!]->"+str(e))
                    except errors.rpc_error_list.UsernameInvalidError as e:
                        self.blacklist.add(group)
                        print("     [!]->"+str(e))
                    except errors.rpc_error_list.UsernameNotOccupiedError as e:
                        self.blacklist.add(group)
                        print("     [!]->"+str(e))
                    except TypeError as e:
                        self.blacklist.add(group)
                        print("     [!]->"+str(e))
                    except errors.rpc_error_list.InviteHashExpiredError as e:
                        self.blacklist.add(group)
                        print("     [!]->"+str(e))
                else:
                    self.leftout_groups.add(group)

    def collect_data(self):
        """Gathers the saved data from each channel and writes it to files"""
        chatoutput = list()
        blacklist = set()
        join_groups = self.read_leftout_groups()
        metadata = list()
        for channel in self.groups:
            if channel.active:
                self.blacklist = self.blacklist.union(channel.groups_blocked)
                join_groups = join_groups.union(channel.groups)
                chatoutput.append(channel.output)
                metadata.append(channel.metadata)
            else:
                if self.leave:
                    self.leavechannel(channel.dialog)
        self.join_groups(join_groups, blacklist)
        self.write_data(self.blacklist, "blocked_groups")
        self.write_data(metadata, "groups.meta")
        block_number = self.get_highest_chatblock()
        self.write_data(chatoutput, "chat_block-{}".format(block_number))
        self.write_leftout_groups()


    def leavechannel(self, dialog):
        try:
            self.client(LeaveChannelRequest(dialog.entity))
            self.blacklist.add(dialog.name)
            print("[*] Left Channel: {}".format(dialog.name))
        except RuntimeError as e:
            print(e)
    

    def calc_average(self):
        try:
            with codecs.open("groups.meta", "r", encoding="utf-8") as readfile:
                numbers = [entry.split(";")[1] for entry in readfile.readlines() if len(entry) > 6]
                readfile.close()
            if len(numbers) == 0:
                return 0
            sum = 0
            for number in numbers:
                sum += int(number)
            return sum/len(numbers)
        except FileNotFoundError:
            return 0


    def check_groups(self):
        dialogs = self.client.get_dialogs(limit=5000)
        for dialog in dialogs:
            print(dialog.name)


    def load_blocked_groups(self):
        """Loads the blacklisted groups into the memory"""
        print("     ->[*] Loading group blacklist...")
        blacklist = set()
        if os.access("blocked_groups", os.F_OK):
            with codecs.open("blocked_groups", "r", encoding="utf-8") as groups:
                blocked_groups = groups.readlines()
                for group in blocked_groups:
                    blacklist.add(group)
        return blacklist


    def initialize_run(self):
        """Loads dialogs and starts them one after the other"""
        dialogs = self.client.get_dialogs(limit=5000)
        self.groups = list()
        for dialog in dialogs:
            try:
                self.groups.append(TelethonB.Channel(dialog, self.msg_average, self.msg_avg_deviation, self.client)) #Creates list of channel objects
                self.dialog_names.add(dialog.name)
            except TypeError as e:
                print(e)
                continue
            except RuntimeError as e:
                print(e)
                continue
        print("[+] All groups successfully initialized!")


    def run_multi(self, count, leave):
        self.leave = leave
        threads = list()
        for channel in self.groups:
            thread = threading.Thread(target=channel.run, args=(count,))
            threads.append(thread)
        for thread in threads: #Starts Threads
            thread.start()
        for thread in threads: #Joins threads so further action will be made, after all Threads are finished
            print("[*] Joining {}/{}".format(thread.name, str(len(threads))))
            thread.join()
        self.collect_data()
        threads = [] #empty thread list
        print("_--------------------all finished-------------------_")


    def write_leftout_groups(self):
        with codecs.open("leftout_groups", "w", encoding="utf-8") as output:
            for group in self.leftout_groups:
                output.write(group+"\n")

    def read_leftout_groups(self):
        if os.access("leftout_groups", os.F_OK):
            with codecs.open("leftout_groups", "r", encoding="utf-8") as input:
                groups = input.readlines()
                return set(groups)
        else:
            return set()


    def run(self, count, leave):
        self.read_leftout_groups()
        self.leave = leave
        for channel in self.groups:
            print("[+] Running Channel: {}".format(channel.name))
            channel.run(count)
        self.collect_data()
        print("_--------------------all finished-------------------_")


def main():
    parser = optparse.OptionParser("usage: {} -m <0/1> (0=single-, 1=multiprocessing) -t <time in seconds> -r <repetitions> -l <0/1>".format(os.path.basename(__file__)))
    parser.add_option("-m", dest="tgtMode", type="int", help="choose runmode, 0 for singleprocessed, 1 for multiprocessed")
    parser.add_option("-t", dest="tgtTime", type="int", help="Specify wait time between runs")
    parser.add_option("-r", dest="tgtRep", type="int", help="Specify how often the the software is run")
    parser.add_option("-l", dest="tgtLeave", type="int", help="0 to stay in inactive groups, 1 to leave inactive groups")

    (options, args) = parser.parse_args()

    tgtMode = options.tgtMode
    seconds = options.tgtTime
    tgtRep = options.tgtRep
    tgtLeave = options.tgtLeave


    if (tgtMode == None) | (tgtRep == None) | (seconds == 0 and tgtRep > 1) | (tgtLeave != None and tgtLeave != 0 and tgtLeave != 1) | (tgtMode != 1 and tgtMode != 0):
        print(parser.usage)
        exit(0)

    if tgtLeave == None: #Don't leave groups on default
        print("No arguments for -l -> Default set to False, inactive groups won't be left")
        leave = False
    elif tgtLeave == 1:
        leave = True
    elif tgtLeave == 0:
        leave = False


    count = 0


    while(count<tgtRep):
        top = TelegramOperator() #Object is recreated every time to reset the data
        s = sched.scheduler(time.time, time.sleep)
        if tgtMode == 0:
            s.enter(seconds, 1, top.run, (count,leave,))
        elif tgtMode == 1:
            s.enter(seconds, 1, top.run_multi, (count,leave,))
        print("Running in {} seconds".format(seconds))
        s.run()
        count+=1


if __name__ == "__main__":
    main()
    