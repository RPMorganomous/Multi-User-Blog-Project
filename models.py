from google.appengine.ext import ndb
from utils import 

class Comment(ndb.Model):
    comment = ndb.StringProperty(required = True)
    post = ndb.KeyProperty() #points to data in another entity
    user = ndb.KeyProperty()
    last_touch_date_time = ndb.DateTimeProperty(auto_now=True)
    
class Post(ndb.Model):
    subject = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    author = ndb.StringProperty()
    likedby = ndb.KeyProperty(kind='User', repeated=True)

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
