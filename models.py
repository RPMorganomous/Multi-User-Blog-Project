from google.appengine.ext import ndb

class Comment(ndb.Model):
    comment = ndb.StringProperty(required = True)
    post = ndb.KeyProperty() #points to data in another entity
    user = ndb.KeyProperty()
    last_touch_date_time = ndb.DateTimeProperty(auto_now=True)
    
