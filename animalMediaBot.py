import praw
import csv
import os
import re
import pprint

class animalMediaBot:
    def __init__(self):
        self.reddit = None
        self.daily_message_beg = "Hello your daily quota of posts is here as follows\n\n\n"
        self.daily_message_end = "Sent with love from /u/animalMediaBot by /u/ieshaan12"
        self.subject = "Your daily digest from r/"      
        self.subDoesNotExist = "This subreddit doesn't exist/ it is private - "
        self.noSubReplySubject = "Invalid Message"
        self.subAddedReplySubject = "Subs added with the bot"
        self.noSubReplyMessage = "Hey /u/{}\n\n The subs couldn't be added with the bot, because you didn't send them in the required format.\n\n"
        self.subAddedReplyMessage = "Hey /u/{}\n\n These subs - {} have been added with the bot.\n\n"
        self.endMessage = "Follow this format 'r/soccer,r/aww,r/memes' if you want to add more subreddits.\n\n Thank you for using this bot! Don't forget it to share it with your friends!\n\n"
        self.conclusiveMessage = self.endMessage + self.daily_message_end

    def getFiles(self, fileData = 'fileData.txt'):
        with open(fileData) as csvFile:
            csvData = csv.reader(csvFile,delimiter=',')
            for row in csvData:
                workingDirectory = row[0]
                credentialFile = row[1]
                userFile = row[2]
                newDataFile = row[3]
        return workingDirectory, credentialFile, userFile, newDataFile

    def getCredentials(self, credentialFile):
        f = open(credentialFile)
        self.client_id, self.client_secret, self.username, self.password, self.user_agent = f.readline().split(',')
        f.close()

    def login(self):
        self.reddit = praw.Reddit(client_id = self.client_id, 
                    client_secret = self.client_secret, 
                    username = self.username, 
                    password = self.password, 
                    user_agent = self.user_agent)
    
    def getUserData(self, userFile):
        self.subredditDict = dict()
        self.allSubs = set()

        with open(userFile) as csvFile:
            csvData = csv.reader(csvFile,delimiter=',')
            for row in csvData:
                try:
                    username = row.pop(0)
                    subreddits = set(row)
                    if username not in self.subredditDict:
                        self.subredditDict[username] = subreddits
                    else:
                        self.subredditDict[username].update(subreddits)
                    self.allSubs.update(subreddits)
                except:
                    print("Empty row - ", row)

    def getAllMessageData(self):
        self.subredditMessageData = dict()

        for i in self.allSubs:
            subreddit = self.reddit.subreddit(i)
            counter = 1
            Message = self.daily_message_beg
            try:
                for submission in subreddit.hot(limit=12):
                    if not submission.stickied:
                        newLine = str(counter) + ': ' + submission.permalink + '\n\n'
                        Message += newLine
                        counter += 1
                    if counter > 10:
                        break
                Message += '\n' + self.conclusiveMessage

                self.subredditMessageData[i] = Message
            except:
                self.subredditMessageData[i] = self.subDoesNotExist + i
        
    def sendMessageData(self):
        
        for username,subreddits in self.subredditDict.items():
            for subreddit in subreddits:
                self.reddit.redditor(username).message(self.subject + subreddit, self.subredditMessageData[subreddit])

    def getInbox(self, newDataFile = 'newUsers.csv'):
        newUserData = dict()
        for item in self.reddit.inbox.unread(limit = None):
            subreddits = re.findall(r"r/([^\s,]+)", item.body)
            subs = []
            for i in subreddits:
                try:
                    subs.append(i)
                except:
                    pass
            newUserData[item.author.name] = subs

            if len(subs) == 0:
                message = self.noSubReplyMessage.format(item.author.name) + self.conclusiveMessage
                self.reddit.redditor(item.author.name).message(self.noSubReplySubject, message)
            else:
                message = self.subAddedReplyMessage.format(item.author.name,', '.join(subs)) + self.conclusiveMessage
                self.reddit.redditor(item.author.name).message(self.subAddedReplySubject, message)

        os.remove(newDataFile)

        with open(newDataFile,'w',newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            rows = []
            for username, subreddits in newUserData.items():
                subreddits.insert(0,username)
                rows.append(subreddits)
            csvWriter.writerows(rows)
    
    def mergeCSV(self, newUserFile = 'newUsers.csv', userFile = 'userCSV.csv'):
        with open(userFile,'a') as csvWriteFile:
            content = None
            with open(newUserFile,'r') as csvReadFile:
                content = csvReadFile.read()
            csvWriteFile.write('\n')
            csvWriteFile.write(content)


if __name__ == "__main__":
    BOT = animalMediaBot()
    workingDirectory, credentialFile, userFile, newDataFile = BOT.getFiles()
    os.chdir(workingDirectory)
    BOT.getCredentials(credentialFile)
    BOT.getUserData(userFile)
    BOT.login()
    BOT.getAllMessageData()
    BOT.sendMessageData()
    
    # For updating new users from inbox, call these functions
    # BOT.getInbox()
    # BOT.mergeCSV()