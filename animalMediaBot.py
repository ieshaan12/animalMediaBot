import praw
import csv
import os
import re
import time
import json
import sys
import argparse
import logging


class animalMediaBot:
    def __init__(self):
        '''
        Initiating animalMediaBot instance.
        '''
        self.reddit = None
        self.daily_message_beg = "Hello your daily quota of posts is here" + \
            "as follows\n\n\n"
        self.daily_message_end = "Sent with love from /u/animalMediaBot " + \
            "by /u/ieshaan12"
        self.subject = "Your daily digest from r/"
        self.subDoesNotExist = "This subreddit doesn't exist/ it is private - "
        self.noSubReplySubject = "Invalid Message"
        self.subAddedReplySubject = "Subs added with the bot"
        self.noSubReplyMessage = "Hey /u/{}\n\n The subs couldn't be added" + \
            " with the bot, because you didn't send them in the required " + \
            "format.\n\n"
        self.subAddedReplyMessage = "Hey /u/{}\n\n These subs - {} have" + \
            " been added with the bot.\n\n"
        self.endMessage = "Follow this format 'r/soccer,r/aww,r/memes' if " + \
            "you want to add more subreddits.\n\nThank you for using " + \
            "this bot! Don't forget it to share it with your friends!\n\n"
        self.conclusiveMessage = self.endMessage + self.daily_message_end
        self.messageWait = 75
        self.metaMessageWait = 60

        logging.debug('Successfully created animalMediaBot object')

    def getFiles(self, fileData='fileData.txt'):
        '''
        Retrieving these files in this particular directory -
        1. workingDirectory
        2. credentialFile
        3. userFile
        4. trialFile
        5. newDataFile
        '''
        with open(fileData) as csvFile:
            csvData = csv.reader(csvFile, delimiter=',')
            for row in csvData:
                workingDirectory = row[0]
                credentialFile = row[1]
                userFile = row[2]
                trialFile = row[3]
                newDataFile = row[4]
        return workingDirectory, credentialFile, userFile,\
            trialFile, newDataFile

    def getCredentials(self, credentialFile):
        '''
        Obtaining credentials from credentials.txt and sending them back
        for login
        '''
        f = open(credentialFile)
        self.client_id, self.client_secret, self.username, \
            self.password, self.user_agent = f.readline().split(',')
        f.close()

    def login(self):
        '''
        Login function
        '''
        self.reddit = praw.Reddit(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  username=self.username,
                                  password=self.password,
                                  user_agent=self.user_agent)

        if self.reddit is not None:
            logging.debug('Reddit Object created successfully')

    def getUserData(self, userFile):
        '''
        Getting user data from the csv file, in the future this can be
        saved into a JSON file.
        (maybe actually better idea to do JSON, didn't consider before)
        A PR would be appreciated. This would have to be changed in getInbox().
        '''
        self.subredditDict = dict()
        self.allSubs = set()

        with open(userFile) as csvFile:
            csvData = csv.reader(csvFile, delimiter=',')
            for row in csvData:
                try:
                    username = row.pop(0)
                    subreddits = set(row)
                    if username not in self.subredditDict:
                        self.subredditDict[username] = subreddits
                    else:
                        self.subredditDict[username].update(subreddits)
                    self.allSubs.update(subreddits)
                except Exception as e:
                    logging.info(e + '\n\nEmpty Row in UserCSV File')

    def getAllMessageData(self):
        '''
        Making API calls to download the data from the subreddits, of course
        this is a long task, and needs to be logged. Logging PRs can also be
        very helpful. Feel free to make an issue for this.
        '''
        self.subredditMessageData = dict()

        for i in self.allSubs:
            subreddit = self.reddit.subreddit(i)
            counter = 1
            Message = self.daily_message_beg
            try:
                for submission in subreddit.hot(limit=12):
                    if not submission.stickied:
                        newLine = str(
                            counter) + ': ' + submission.permalink + '\n\n'
                        Message += newLine
                        counter += 1
                    if counter > 10:
                        break
                Message += '\n' + self.conclusiveMessage

                self.subredditMessageData[i] = Message
            except Exception as e:
                logging.info(e + '\n\n' + self.subDoesNotExist + i)
                self.subredditMessageData[i] = self.subDoesNotExist + i

        with open('subredditUserData.json', 'w') as jsonFile:
            json.dump(self.subredditMessageData, jsonFile, indent=4)

        logging.debug('Subreddit User Data written successfully')

    def sendMessageData(self):
        '''
        Pretty self-explanatory. Just sending messages based
        on the user's subreddits.
        '''
        with open('subredditUserData.json', 'r') as jsonFile:
            self.subredditMessageData = json.load(jsonFile)

        logging.debug('Read subredditUserData.json file successfully')

        for username, subreddits in self.subredditDict.items():
            for subreddit in subreddits:
                try:
                    self.reddit.redditor(username).message(
                        self.subject + subreddit,
                        self.subredditMessageData[subreddit])
                    time.sleep(self.messageWait)
                except Exception as e:
                    logging.error(
                        e + '\n\nTime' +
                        'needs to be increased for sending subreddit data')

    def getInbox(self, newDataFile='newUsers.csv'):
        '''
        Retreiving data and storing it back in a csvFile,
        this can be altered to a JSON file as mentioned in getUserData().
        '''
        newUserData = dict()
        for item in self.reddit.inbox.unread(limit=None):
            subreddits = re.findall(r"r/([^\s,]+)", item.body)
            if len(subreddits) == 0:
                logging.warning(
                    'This user:{} may have put subreddits in a wrong'.format(
                        item.author.name))
            subs = []
            for i in subreddits:
                try:
                    subs.append(i)
                except Exception as e:
                    logging.error(e + '\n\nNo subreddits')
            newUserData[item.author.name] = subs

            if len(subs) == 0:
                message = self.noSubReplyMessage.format(
                    item.author.name) + self.conclusiveMessage
                self.reddit.redditor(item.author.name).message(
                    self.noSubReplySubject, message)
            else:
                message = self.subAddedReplyMessage.format(
                    item.author.name, ', '.join(subs)) + self.conclusiveMessage
                self.reddit.redditor(item.author.name).message(
                    self.subAddedReplySubject, message)

        os.remove(newDataFile)

        with open(newDataFile, 'w', newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            rows = []
            for username, subreddits in newUserData.items():
                subreddits.insert(0, username)
                rows.append(subreddits)
            csvWriter.writerows(rows)

        logging.debug('New users data has been written now')

    def mergeCSV(self, newUserFile='newUsers.csv', userFile='userCSV.csv'):
        '''
        Merging the CSV files, to add new users to the old ones.
        '''
        with open(userFile, 'a') as csvWriteFile:
            content = None
            with open(newUserFile, 'r') as csvReadFile:
                content = csvReadFile.read()
            csvWriteFile.write('\n')
            csvWriteFile.write(content)

        logging.info('Merging {} into {}'.format(newUserFile, userFile))

    def sendMetaMessage(self, metaFile='MetaMessage.txt'):
        '''
        Function to send a meta message.
        '''
        time.sleep(180)
        f = open(metaFile)
        MetaMessage = '\n\n'.join(f.readlines())
        f.close()
        openingSalutation = "Dear /u/{}\n\n"
        ignoreMessage = "REQUEST: PLEASE IGNORE ANY META MESSAGE BEFORE" + \
            " THIS\n\n"
        MetaSubject = "Meta Message"
        for username in self.subredditDict.keys():
            messageToBeSent = ignoreMessage + openingSalutation.format(
                username) + MetaMessage + '\n\n' + self.conclusiveMessage
            try:
                self.reddit.redditor(username).message(MetaSubject,
                                                       messageToBeSent)
                time.sleep(self.metaMessageWait)
            except Exception as e:
                logging.error(e + '\n\nMeta Message delay needs to be updated')

        logging.debug('Sent all Meta Messages successfully')


if __name__ == "__main__":
    # Setting up logger
    logFile = 'animalMediaBot.log'
    logForm = '%(asctime)s.%(msecs)03d %(levelname)s %(module)s -\
%(funcName)s: %(message)s'

    print(logForm)
    os._exit(0)

    logging.basicConfig(filename=logFile,
                        filemode='a',
                        format=logForm,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    # Parsing Arguments for Files and Tasks
    parser = argparse.ArgumentParser(description='animalMediaBot parser')
    parser.add_argument('-f',
                        '--file',
                        type=int,
                        help="1 for userCSV.csv, 0 for trial.csv",
                        required=True)
    parser.add_argument(
        '-t',
        '--task',
        type=int,
        help="1 for getMessageData, 2 for sendMessageData, 3 for MetatMessage,"
        + " 4 for parsing inbox data, 5 for merging csv data",
        required=True)
    args = parser.parse_args()
    arguments = vars(args)
    argFile, argTask = arguments['file'], arguments['task']

    # Creating the bot instance
    BOT = animalMediaBot()

    # Setting paths and getting path files
    workingDirectory, credentialFile, userFile, trialFile, newDataFile \
        = BOT.getFiles()
    os.chdir(workingDirectory)

    # Getting credentials
    BOT.getCredentials(credentialFile)

    # Choosing the csvFile for user-subreddit mapping
    csvFile = None
    if argFile == 1:
        csvFile = userFile
    elif argFile == 0:
        csvFile = trialFile
    else:
        print("Invalid file value")
        logging.critical('No file for this argFile : {}'.format(argFile))
        os._exit(0)

    # Retrieving data from the csvFiles
    BOT.getUserData(csvFile)

    # Bot login
    BOT.login()
    '''
    Options for argTask
    1 : getAllMessageData()
    2 : sendAllMessageData()
    3 : sendMetaMessage()
    4 : getInbox()
    5 : mergeCSV()
    '''

    # Choosing the task based on the arguments
    if argTask == 1:
        BOT.getAllMessageData()
    elif argTask == 2:
        BOT.sendMessageData()
    elif argTask == 3:
        BOT.sendMetaMessage()
    elif argTask == 4:
        BOT.getInbox()
    elif argTask == 5:
        BOT.mergeCSV()
    else:
        print("Invalid argTask value, now exiting")
        logging.critical('No task for this argTask: {}'.format(argTask))
        os._exit(0)
