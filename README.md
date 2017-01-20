Rick's Blog
==============

Usage
--------------

 - Clicking the main title, "Rick's Blog" will return you to the front page of the blog with an ordered list of posts.
 - Clicking on any post will take you to the post's page where it can be commented on, edited by the author, and liked/unliked by another user.
 - Comments are ordered and can be edited/deleted by their author.
 - Deleting a post deletes all associate comments.

### Multi-User Blog

The goal of this project is to create a simple multi-user blog. 

Users should be able to create an account with login/logout functionality, and create/edit/delete posts and comments.

Checkout the [live](https://basicblog-153422.appspot.com/blog) version of this project.

### Frameworks/technologies used
- [Google App Engine](https://cloud.google.com/appengine/docs)
- [Python 2.7](https://www.python.org/doc/)
- [HTML/CSS](https://google.github.io/styleguide/htmlcssguide.xml)
- [GitHub](https://github.com/)

### Project specifications

Blog must include the following features:
- Front page that lists blog posts.
- A form to submit new entries.
- Blog posts have their own page.

Registration must include the following features:
- A registration form that validates user input, and displays the error(s) when necessary.
- After a successful registration, a user is directed to a welcome page with a greeting, “Welcome, *name*” where *name* is a name set in a cookie.
- If a user attempts to visit a restricted page without being signed in (without having a cookie), then redirect to the Signup page.

Login must include the following features:
- Have a login form that validates user input, and displays the error(s) when necessary.

Users must include the following features:
- Users should only be able to edit/delete their posts. They receive an error message if they disobey this rule.
- Users can like/unlike posts, but not their own. They receive an error message if they disobey this rule.
- Users can comment on posts. They can only edit/delete their own posts, and they should receive an error message if they disobey this rule.

Code must conform to the [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
