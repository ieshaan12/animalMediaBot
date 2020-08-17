import praw
import csv

class animalMediaBot:
    def __init__(self):
        self.reddit = None
        self.daily_message_beg = "Hello your daily quota of posts is here as follows\n\n\n"
        self.daily_message_end = "Sent with love from /u/animalMediaBot by /u/ieshaan12"
        self.subject = "Your daily digest from r/"      
    
    def getCredentials(self):
        f = open('credentials.txt')
        self.client_id, self.client_secret, self.username, self.password, self.user_agent = f.readline().split(',')
        f.close()

    def login(self):
        self.reddit = praw.Reddit(client_id = self.client_id, 
                    client_secret = self.client_secret, 
                    username = self.username, 
                    password = self.password, 
                    user_agent = self.user_agent)
    
    def getUserData(self):
        self.subredditDict = dict()
        self.allSubs = set()

        with open('userCSV.csv') as csvFile:
            csvData = csv.reader(csvFile,delimiter=',')
            for row in csvData:
                username = row.pop(0)
                subreddits = set(row)
                self.subredditDict[username] = subreddits
                self.allSubs.update(subreddits)

    def getAllMessageData(self):
        self.subredditMessageData = dict()

        for i in self.allSubs:
            subreddit = self.reddit.subreddit(i)
            counter = 1
            Message = self.daily_message_beg
            for submission in subreddit.hot(limit=12):
                if not submission.stickied:
                    newLine = str(counter) + ': ' + submission.permalink + '\n\n'
                    Message += newLine
                    counter += 1
                if counter > 10:
                    break
            Message += '\n' + self.daily_message_end

            self.subredditMessageData[i] = Message
    
    def sendMessageData(self):
        
        for username,subreddits in self.subredditDict.items():
            for subreddit in subreddits:
                self.reddit.redditor(username).message(self.subject + subreddit, self.subredditMessageData[subreddit])

if __name__ == "__main__":
    BOT = animalMediaBot()
    BOT.getCredentials()
    BOT.getUserData()
    BOT.login()
    BOT.getAllMessageData()
    BOT.sendMessageData()
        