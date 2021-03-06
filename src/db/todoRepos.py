from datetime import datetime

import todoRedis
from src.todoLogging import log, WarningLevels

class RepoQueues:
    Cloning = "queues::cloning"
    Parsing = "queues::parsing"
    Posting = "queues::posting"
    RepoGY = "queues::repogy"
    TodoGY = "queues::todogy"

KEY_FORMAT = '%s::todo::%s/%s'

class Repo:
    def __init__(self):
        self.userName = ''
        self.repoName = ''
        self.gitUrl = ''
        self.status = 'New'
        self.errorCode = 0
        self.Todos = []
        self.branch = u''
        self.commitSHA = ''
        self.tagDate = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        self.lastTodoPosted = ''
        self.lastTodoPostDate = ''

    def key(self):
        return 'repos::%s/%s' % (self.userName, self.repoName)
    
    def save(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and
                                                 not attr.startswith("__") and
                                                 not attr == "Todos"]
        r = todoRedis.connect()
        
        r.sadd('repos', self.key())

        for m in members:
            r.hset(self.key(), m, getattr(self, m))

        for td in self.Todos:
            td.save(self)
        
    def load(self):
        return self.loadFromKey(self.key())
        

    def loadFromKey(self, key):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and
                                                 not attr.startswith("__") and
                                                 not attr == "Todos"]
        r = todoRedis.connect()

        if r.hlen(key) > 0:
            for m in members:
                setattr(self, m, r.hget(key, m))
        else:
            # "No keys found"
            return False

        for m in r.smembers(key+"::todo"):
            td = Todo()
            td.loadFromKey(m)
            self.Todos.append(td)

        return True
           
    
    #Looks through the branches on github itself to get the 
    #latest commit SHA for the default branch
    def getGithubSHA(self, gh):
        
        try:
            branches = gh.repos.list_branches(self.userName, self.repoName)
            for branch in branches.all():
                if branch.name == self.branch:
                    return branch.commit.sha
        except:
            log(WarningLevels.Warn, "Failed to get SHA for %s/%s"%(self.userName, self.repoName))         
        
                
        return None


class Todo:
    def __init__(self):
        self.filePath = ''
        self.lineNumber = ''
        self.commentBlock = ''
        self.blameUser = ''
        self.blameDate = ''
        self.issueURL = ''
        self.blameDateEuro = ''
        self.commitSHA = ''

    def save(self, parent):
        key = KEY_FORMAT % (parent.key(), self.filePath.rsplit('/',1)[1], self.lineNumber)
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

        # Save into the Repo's set
        r = todoRedis.connect()
        r.sadd('%s::todo' % (parent.key()), key)

        for m in members:
            r.hset(key, m, getattr(self, m))

    def key(self, parent):
        return KEY_FORMAT % (parent.key(), self.filePath.rsplit('/',1)[1], self.lineNumber)
    
    def load(self, parent):
        key = KEY_FORMAT % (parent.key(), self.filePath.rsplit('/',1)[1], self.lineNumber)
        self.loadFromKey(key)
        
    def loadFromKey(self, key):
        r = todoRedis.connect()
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

        if r.hlen(key) > 0:
            for m in members:
                setattr(self, m, r.hget(key, m))
        

def repoCount():
    r = todoRedis.connect()
    return r.scard('repos')

#takes a github.repo
def addNewRepo(ghRepo):
    r = todoRedis.connect()
    repo = Repo()
    repo.userName = ghRepo.owner.login
    repo.repoName= ghRepo.name
    repo.gitUrl = ghRepo.git_url
    repo.branch = ghRepo.default_branch
    
    repo.save()
    
    return repo
    
def repoExists(userName, repoName):
    r = todoRedis.connect()
    return r.sismember('repos', 'repos::%s/%s' % (userName, repoName))

def getRepos():
    r = todoRedis.connect()
    repoList = []
    
    for key in r.smembers('repos'):
        repo = Repo()
        repo.loadFromKey(key)
        repoList.append(repo)
        
    return repoList
    
    
def getPostedIssues(page = 0, recent = True, pageSize = 25):
    r = todoRedis.connect()
    
    issueCount = r.llen(RepoQueues.TodoGY)
    issues = r.lrange(RepoQueues.TodoGY, 0, issueCount - 1)
    pageCount = int(issueCount / pageSize)
    if issueCount % pageSize > 0:
        pageCount += 1
    
    if page >= pageCount:
        page = pageCount - 1
        
    if recent:
        issues.reverse()
    
    issues = issues[page * pageSize : min(issueCount,(page + 1) * pageSize )]        
        
    todoList = []
    for issue in issues:
        todo = Todo()
        todo.loadFromKey(issue)
        todoList.append(todo.issueURL)
        
    pageData = {}
    pageData['pageNumber'] = page
    pageData['pageCount'] = pageCount
    pageData['todoList'] = todoList
        
    return pageData
    
    
def getQueueStats():
    r = todoRedis.connect()

    data = {}
    data['cloneCount'] = r.llen(RepoQueues.Cloning)
    data['parseCount'] = r.llen(RepoQueues.Parsing)
    data['postCount'] = r.llen(RepoQueues.Posting)
    data['postedIssueCount'] = r.llen(RepoQueues.RepoGY)
    data['repoCount'] = len(r.keys('repos::*')) - len(r.keys('repos::*:todo*'))
    
    return data
    
        
    
        

    
    
    

    
    



