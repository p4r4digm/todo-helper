import random
from datetime import datetime

from jinja2 import Template
from pygithub3 import Github
from dateutil.relativedelta import relativedelta

from db.todoRepos import Todo

titleTemplate = 'Unresolved TODO in {{ FileName }}:{{ LineNumber }}'
issueHeaderTemplate = 'File: {{ FilePath }}\nLine: {{ LineNumber }}\n\n```\n{{ CommentBlock }}\n```'

# Builds a template and renders it with the passed-in data
def renderTemplate(tempString, data):
    return Template.render(Template(tempString), data)


# Returns a list of complain templates
def buildComplaintTemplatesList():
    templates = []
    
    templates.append('This has been sitting here since {{ BlameDate }}...a little unprofessional don\'t you think?')
    templates.append('I don\'t get it, {{ BlameUserName }} added this {{ TimeSinceBlameDate }} ago!')
    templates.append('Why was {{ BlameUserName }} allowed to leave this here?')
    templates.append('We\'ve had no traction on this since {{ BlameDate}}.')
    templates.append('I thought {{ FileName }} was in {{ BlameUserName }}\'s hands?')
    templates.append('It\'s been {{ TimeSinceBlameDate }}.')
    
    return templates
    
# Returns a list of emphasis templates
def buildEmphasisTemplatesList():
    templates = []
    
    templates.append('Seriously.')
    templates.append('Is there ever going to be any progress on this?')
    templates.append('I\'m confused as to why this is still a TODO...')
    templates.append('Couldn\'t you just go ahead and implement this?')
    templates.append('I find it pretty hilarious that this continues to go unresolved.')
    templates.append('Will there be resolution on this in the project\'s lifetime?')
    templates.append('I think I speak for many when I say that the lack of update on this is non-trivially detrimental.')
    templates.append('How can we expect to have full-featured release when the code itself is fragmented and incomplete?')
    
    return templates

# Builds and returns the dictionary to popuate templates with
# Takes a db.todoRepo.Todo()
def buildTemplateData(todo):
    data = {}
    
    data['BlameUserName'] = todo.blameUser.split(' ')[0]
    data['BlameDate'] = todo.blameDate.split(' ')[0]
    data['TimeSinceBlameDate'] = buildDatePhrase(todo.blameDate)
    data['FileName'] = todo.filePath.rsplit('/', 1)[1].split('.')[0]
    data['FilePath'] = todo.filePath
    data['LineNumber'] = todo.lineNumber
    data['CommentBlock'] = todo.commentBlock
    
    return data

    
# Builds a string describing the passed date relative to the current date 
# in a human-readable phrase
# Passed in data shoud be in 'yyyy-mm-dd HH::MM:SS' and be UTC
def buildDatePhrase(dateString):
    date = datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')
    currDate = datetime.utcnow()

    # Gives a helpful elapsed date/time structure
    delta = relativedelta(currDate, date)

    # Need to do weeks manually though
    delta.weeks = delta.days / 7
    delta.days -= delta.weeks * 7

    # List of dictionaries that contain lambdas for determining the condition 
    # and building the string
    conditions = [
        {'func':(lambda d: d.years >= 2), 'result':(lambda d: 'over %i years' % (d.years))},
        {'func':(lambda d: d.years == 1), 'result':(lambda d: 'over a year')},
        {'func':(lambda d: d.months >= 10), 'result':(lambda d: 'almost a year')},
        {'func':(lambda d: d.months >= 2), 'result':(lambda d: 'over %i months' % (d.months))},
        {'func':(lambda d: d.months == 1), 'result':(lambda d: 'over a month')},
        {'func':(lambda d: d.weeks >= 3), 'result':(lambda d: 'almost a month')},
        {'func':(lambda d: d.weeks >= 2), 'result':(lambda d: 'over %i weeks' % (d.weeks))},
        {'func':(lambda d: d.weeks == 1), 'result':(lambda d: 'over a week')},
        {'func':(lambda d: d.days >= 5), 'result':(lambda d: 'almost a week')},
        {'func':(lambda d: d.days >= 2), 'result':(lambda d: '%i days' % (d.days))},
        {'func':(lambda d: d.days == 1), 'result':(lambda d: 'over 24 hours')},
        {'func':(lambda d: d.hours >= 1), 'result':(lambda d: 'crucial hours')},
        {'func':(lambda d: True), 'result':(lambda d: 'mere moments')}
    ]

    for c in conditions:
        if c['func'](delta):
            return c['result'](delta)        

    # This is unreachable
    return ''
    
# Compiles the different parts of the issue's body and returns the final string
# Takes the data dictionary to render the templates with
def buildIssueBody(data):
    emphasisList = buildEmphasisTemplatesList()
    complaintList = buildComplaintTemplatesList()
    
    emphasisTemplate = emphasisList[random.randint(0, len(emphasisList) - 1)]
    complaintTemplate = complaintList[random.randint(0, len(complaintList) - 1)]
    
    header = renderTemplate(issueHeaderTemplate, data)
    emphasis = renderTemplate(emphasisTemplate, data)
    complaint = renderTemplate(complaintTemplate, data)
    
    return '%s\n\n%s  %s' % (header, complaint, emphasis)


# Builds an issue from the passed db.todoRepos.Todo
# returns a dictionary containing title and body ready to pass to github
def buildIssue(todo):
    # Create Issues format
    # repo.create(dict(title='My test issue', body='This needs to be fixed ASAP.'))
    
    # Build Title
    # Build First line containing filename and line#
    # Quote the todo comment block
    # Message (Build dict to send to templates), message consists of Complaint followed by Emphasis
    # Return {title, body}
    
    data = buildTemplateData(todo)
    ret = {}
   
    try: 
        ret['title'] = renderTemplate(titleTemplate, data)
        ret['body'] = buildIssueBody(data)
    except:
        pass
    
    return ret
    

