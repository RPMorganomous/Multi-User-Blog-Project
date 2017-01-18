import os
import re
import random
import hashlib
import hmac
import webapp2
import jinja2
import time

from string import letters
#from models import Comment, Post, User
from google.appengine.ext import ndb


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'flatulance'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

def filterName(id):
    user_obj = User.by_id(id)
    if user_obj:
        print user_obj.name
        return user_obj.name
    else:
        print "invalid obj"
        
jinja_env.filters['filterName'] = filterName
        
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key.id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

class MainPage(BlogHandler):
    def get(self):
        self.write('Hello, Udacity!')

##### user stuff

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return ndb.Key('users', group)

class User(ndb.Model):
    name = ndb.StringProperty(required = True)
    pw_hash = ndb.StringProperty(required = True)
    email = ndb.StringProperty()
  
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())
  
    @classmethod
    def by_name(cls, name):
        u = User.query().filter(User.name == name).get()
        return u
  
    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)
  
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

##### blog stuff

PARENT_KEY = ndb.Key("blogs", "default")

def blog_key(name = 'default'):
    return ndb.Key('blogs', name)

class Post(ndb.Model):
    subject = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    author = ndb.StringProperty()
    likedby = ndb.KeyProperty(kind=User, repeated=True)
 
    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self) #makes it easy to fill in call from front.html
 
    @property    #used to compute a variable
    def comments_query(self):
        print "inside comments"
        print Comment.query().filter(Comment.post == self.key)
        print Comment.query().filter(Comment.post == self.key).order(-Comment.last_touch_date_time)
        #return Comment.query().filter(Comment.post == self.key)
        return Comment.query().filter(Comment.post == self.key).order(-Comment.last_touch_date_time)

    @property
    def num_comments(self):
        return Comment.query().filter(Comment.post == self.get()).size()
        
    @property #access num_likes as if it is a variable
    def num_likes(self):
        return len(self.likedby)
        
    @classmethod
    def get_by_id(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()
        return post
          
class Comment(ndb.Model):
    comment = ndb.StringProperty(required = True)
    post = ndb.KeyProperty(kind=Post) #points to data in another entity
    user = ndb.KeyProperty(kind=User)
    last_touch_date_time = ndb.DateTimeProperty(auto_now=True)
    
class BlogFront(BlogHandler):
    def get(self):
        posts = Post.query().order(-Post.created) #- new school way
        self.render('front.html', posts = posts)
        
    def post(self):
        self.redirect('/blog/newpost')

class PostPage(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(post_id) # ??? how to order comments
        
        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)
      
    def post(self, post_id): #this adds a comment from leave a comment to the comment model
        
        #get the comment from the form
        comment = self.request.get('comment') #+ " - user: " + self.user.name

        #get the post key for the blog post
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()
        
        #create an instance of Comment class and then add that to the model
        comment = Comment(comment=comment, post=post.key, user=self.user.key) # ??? why/how does self.user.key work
        comment.put() #parent not working for delayed update
        
        
        self.redirect('/blog/%s' % str(post.key.id())) # back to permalink
        
        #put comment functionality into it's own handler    

class UnlikePost(BlogHandler):
    def get(self, post_id):
        if not self.user:
            self.redirect('/blog')    

        else:
            key = ndb.Key('Post', int(post_id), parent=blog_key())
            post = key.get()
    
            post.likedby.remove(self.user.key)
            post.put()
          
            self.redirect('/blog/%s' % str(post.key.id()))
    
    def post(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        post.likedby.remove(self.user.key)
        post.put()
      
        self.redirect('/blog/%s' % str(post.key.id()))
    
class LikePost(BlogHandler): #add number of likes
    def get(self, post_id):
        print ("inside get")
        if not self.user:
            self.redirect('/blog')
          
        else:
            key = ndb.Key('Post', int(post_id), parent=blog_key())
            post = key.get()
    
            post.likedby.append(self.user.key)
            post.put()
          
            self.redirect('/blog/%s' % str(post.key.id()))
            
    def post(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        post.likedby.append(self.user.key)
        post.put()
      
        #self.redirect('/blog/%s' % str(post.key.id()))
        self.redirect(self.request.referrer) #another way to do it
        
class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect('/blog')

    def post(self):
        if not self.user:
            return self.redirect('/blog')

        subject = self.request.get('subject')
        content = self.request.get('content')
        user = self.user.name 

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content, author = user)
            p.put()
            self.redirect('/blog/%s' % str(p.key.id())) #to permalink
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class EditPost(BlogHandler):
    def get(self, post_id):
        if not self.user:
            self.redirect('/blog')
        
        else:
            key = ndb.Key('Post', int(post_id), parent=blog_key())
            post = key.get()
        
        if self.user.name == post.author:  #follow with else etc. add to post also
            self.render("editme.html", p=post)

    def post(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()
        
        subject = self.request.get("subject")
        content = self.request.get("content")
        
        post.subject = subject
        post.content = content
        
        post.put()
        
        self.redirect('/blog/%s' % str(post.key.id())) #to permalink

class DeleteMe(BlogHandler):
    def get(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        self.render("deleteme.html", p=post)

    def post(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())

        key.delete() #does not remove comments related to this post
        #time.sleep(2) - parent key not working
        self.redirect('/blog')

class DeleteComment(BlogHandler):
    def get(self, comment_id):
        comment_obj = Comment.get_by_id(int(comment_id))
        #key = ndb.Key('Comment', int(comment_id))
        #comment_obj = key.get()
        print comment_obj
        if comment_obj:
            print "comment"
            self.render("deleteComment.html", comment_var=comment_obj)
        else:
            error = "no comment"
            self.render("deleteComment.html", comment_var=None, error=error)

    def post(self, comment_id):
        key = ndb.Key('Comment', int(comment_id), parent=blog_key())
        comment_obj = key.get()
        post_id = comment_obj.post.id()
        key.delete()
        self.redirect('/blog/%s' % str(post_id)) #to permalink
#         key = ndb.Key('Comment', int(post_id), parent=blog_key())
#         #comment_obj = Comment.get_by_id(comment_id)
#         comment_obj.key.delete() 
    
        #time.sleep(2) - parent key not working
        
class EditComment(BlogHandler):
    def get(self, comment_id):
        if not self.user:
            self.redirect('/blog')
        
        else:
            key = ndb.Key('Post', int(post_id), parent=blog_key())
            post = key.get()
        
        if self.user.name == post.author:  #follow with else etc. add to post also
            self.render("editme.html", p=post)

    def post(self, post_id):
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()
        
        subject = self.request.get("subject")
        content = self.request.get("content")
        
        post.subject = subject
        post.content = content
        
        post.put()
        
        self.redirect('/blog/%s' % str(post.key.id())) #to permalink
        
###### Unit 2 HW's
class Rot13(BlogHandler):
    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render('rot13-form.html', text = rot13)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Unit2Signup(Signup):
    def done(self):
        self.redirect('/unit2/welcome?username=' + self.username)

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/blog')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

class Unit3Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/unit2/rot13', Rot13),
                               ('/unit2/signup', Unit2Signup),
                               ('/unit2/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/unlike_post/([0-9]+)', UnlikePost),
                               ('/blog/like_post/([0-9]+)', LikePost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/unit3/welcome', Unit3Welcome),
                               ('/blog/deleteme/([0-9]+)', DeleteMe),
                               ('/blog/deletecomment/([0-9]+)', DeleteComment),
                               ('/blog/editcomment/([0-9]+)', EditComment)
                               ],
                              debug=True)
