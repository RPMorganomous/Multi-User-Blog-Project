

def users_key(group = 'default'):
    return ndb.Key('users', group)