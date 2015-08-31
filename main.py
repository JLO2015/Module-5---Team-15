import webapp2
import jinja2
import os
import urllib
import logging
import json
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'
def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)

class Thesis(ndb.Model):
    username = ndb.StringProperty(indexed=True)
    userId = ndb.StringProperty(indexed=True)
    Year = ndb.StringProperty(indexed=True)
    Title = ndb.StringProperty(indexed=True)
    Abstract = ndb.StringProperty(indexed=True)
    Adviser = ndb.StringProperty(indexed=True)
    Section = ndb.StringProperty(indexed=True)
    date = ndb.DateTimeProperty(auto_now_add=True)

#For User Model
class User(ndb.Model):
    email = ndb.StringProperty(indexed=True)
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    phone_number = ndb.StringProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)

class RegisterHandler(webapp2.RequestHandler):
    def get(self):
        loggedin_user = users.get_current_user()  #use users.get_current_user().user_id() as key ID
        #template_value = {
        #    'register' : users.create_login_url(self.request.uri)
        #}
        if loggedin_user:
            user_key = ndb.Key('User',loggedin_user.user_id())  #for Thesis.created_by should be ndb.KeyProperty() field
            user = user_key.get()
            if user:
                self.redirect('/success')
            else:
                if loggedin_user:
                    template = JINJA_ENVIRONMENT.get_template('register.html')
                    logout_url = users.create_logout_url('/login')
                    template_value = {
                        'logout_url' : logout_url
                    }
                    self.response.write(template.render(template_value))
                    
                else:
                    login_url = users.create_login_url('/register')
                    self.redirect(login_url)
        else:
            self.redirect('/login')

    def post(self):
        loggedin_user = users.get_current_user()
        user =  User(id=loggedin_user.user_id(), email=loggedin_user.email(), first_name=self.request.get('first_name'), last_name=self.request.get('last_name'), phone_number=self.request.get('phone_number'))
        user.put()
        self.redirect('/')

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)

        template_value = {
            'user' : user,
            'url' : url,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('create.html')
            self.response.write(template.render(template_value))
        else:
            self.redirect('/login')

class LoginPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        template_value = {
            'login' : users.create_login_url(self.request.uri)
        }
        if user:
            self.redirect('/register')
        else:
            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_value))

#Not in the scope of Module 5 instruction
class Delete(webapp2.RequestHandler):
    def get(self, thesisId):
        d = Thesis.get_by_id(int(thesisId))
        d.key.delete()
        self.redirect('/')

class Edit(webapp2.RequestHandler):
    def get(self,thesisId):
        s = Thesis.get_by_id(int(thesisId))
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        template_value = {
            'thesis': s,
            'user': user,
            'url': url,
        }
        template = JINJA_ENVIRONMENT.get_template('edit.html')
        self.response.write(template.render(template_value))
    
    def post(self,thesisId):
        thesis = Thesis.get_by_id(int(thesisId))      
        thesis.Year = self.request.get('Year')
        thesis.Title = self.request.get('Title')
        thesis.Abstract = self.request.get('Abstract')
        thesis.Adviser = self.request.get('Adviser')
        thesis.Section = self.request.get('Section')
        thesis.put()
        self.redirect('/')

class APIThesisHandler(webapp2.RequestHandler):
    def get(self):
        thesis = Thesis.query().order(-Thesis.date).fetch()
        thesis_list = []

        for th in thesis:
            author = th.userId
            created_by = ndb.Key('User', author)  
            thesis_list.append({
                    'id' : th.key.id(),
                    'Year' : th.Year,
                    'Title' : th.Title,
                    'Abstract' : th.Abstract,
                    'Adviser' : th.Adviser,
                    'Section' : th.Section,
                    'username' : th.username,
                    'first_name' : created_by.get().first_name,
                    'last_name' : created_by.get().last_name
                })
        response = {
            'result' : 'OK',
            'data' : thesis_list
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(response))

    def post(self):
        user = users.get_current_user()
        th = Thesis()
        th.Year = self.request.get('Year')
        th.Title = self.request.get('Title')
        th.Abstract = self.request.get('Abstract')
        th.Adviser = self.request.get('Adviser')
        th.Section = self.request.get('Section')
        th.username = user.nickname()
        th.userId = user.user_id()
        th.put()

        author = th.userId
        created_by = ndb.Key('User', author)

        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'result' : 'OK',
            'data': {
                'id' : th.key.id(),
                'Year' : th.Year,
                'Title' : th.Title,
                'username' : th.username,
                'first_name' : created_by.get().first_name,
                'last_name' : created_by.get().last_name,
            }
        }
        self.response.out.write(json.dumps(response))

class Success(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('success.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/home', MainPage),
    ('/login', LoginPage),
    ('/register', RegisterHandler),
    ('/api/thesis', APIThesisHandler),
    ('/success', Success),
    ('/thesis/delete/(.*)', Delete),
    ('/thesis/edit/(.*)', Edit)
], debug=True)
