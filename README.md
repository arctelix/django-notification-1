=============================
django-notification-automated
=============================

Many sites need to notify users when certain events have occurred and to allow
configurable options as to how those notifications are to be received.

The project aims to provide a Django app for this sort of functionality. This
includes:

* Submission of notification messages by other apps.
* Automated generation of notice types defined in your settings.
* Automated Notification settings view.
* Automated Notification settings view for each type of observed object.
* Automated Notification messages with Automated hyperlink integration.
* Automated Notification message modification for observed objects.
* Automated deletion of Notification messages when observed object is deleted.
* Automated mark notice as seen when link is clicked.
* Unsubscribe links.
* Optional Notification Queuing.
* Optional Notification Threading.
* Pluggable backbends (configurable by user):
  -Notification messages via website.
  -Notification messages via email.

## Installation:
See the docs for installation help and all base django-notification features.

## How to (automated):

####1. Create notification types in your settings file:  
No need to mess with management files in this version, its automated!  

    NOTICE_TYPES = [("commented","New Comment", "has commented on your pin"),]
***Automation Note:***
Notice descriptions should take the form "has ***action*** on your ***object***" where the object = content_type.name. The resulting notification will look like 
***Username*** has commented on your ***object***.  Username & object will be converted to hyperlinks and clicking the object link will mark the notice as seen.
However, the settings below will help you compensate when that is not possible.
####2. Configure other settings (see code for more details on how these work):  
***NOTIFICATION_CONTENT_TYPE_TRANSLATIONS:*** Provide the system any translations between content_type.name and the message text. 
IE: convert "profile_picture" to a hyperlink.  
    
    {'user':['profile picture', None(url if not = /content_type.name/)]}  
***NOTIFICATION_OTHER_KEY_WORDS:*** Provide the system any other key words in message text that should be converted to hyperlinks. 
IE: convert "word" to a hyperlink.  

    {'word':'/url/'}
***NOTIFICATION_CHECK_FOR_SENDER_NAMES:*** Provide the system any content_types that my mascarade as a variable word not rendered by default. 
IE: Given content_object.name = "post" will convert post.submitter to a hyperlink.  
    
    {'post':['submitter','/url/']}
***OBSRVATION_DELETE_CONTENT_TYPES:*** Provide the system any content_type objects that are properties of the model. 
IE: Given content_object.name = "object" will delete the object object.propery1 and object.propery2 when any associated observations are deleted.  
    
    {'object':['property1', 'property2']}
***OBSRVATION_AUTO_DELETE:*** True/False 
####3. Send notifications to users (based on example code):

    notification.send([target.submitter], "commented", {"from_user": user}, sender=target)
####4. Make some users observe the notification_type you created from some emitter (based on example code):  

    notification.observe(target, user, "commented")
####5. Send the notifications to users who are observing the sender (based on example code):  

    notification.send_observation_notices_for(target, "commented", {"from_user": user, "alter_desc":True, "owner":target.submitter}, [user, target.submitter], sender=target)
####6. Change the templates for each notification type to send personalized notifications:  
This is not required if you use the automated features but feasible in certain cases.  
####7. Display the notifications to the user:  
Provide links to all the views provided.  
####8. The code is heavily commented so please look thoght the code for more information.  
   
## Example code:

	@receiver(post_save, sender=Comment, dispatch_uid='comment.user')
	def pin_comment_handler(sender, *args, **kwargs):
		comment = kwargs.pop('instance', None)
		user = comment.user
		target = comment.content_object
		from notification import models as notification
		#notify post's followers
		sent = notification.send_observation_notices_for(target, "commented", {"from_user": user, "alter_desc":True, "owner":target.submitter}, [user, target.submitter], sender=target)
		#notify user's followers
		notification.send_observation_notices_for(user, "commented", {"from_user": user, "alter_desc":True, "owner":target.submitter}, [user, target.submitter]+sent, sender=target)
		if user != target.submitter:
			#notify post's owner
			notification.send([target.submitter], "commented", {"from_user": user}, sender=target)
			#make comment user observe new comments for post.
			notification.observe(target, user, "commented")

	
The MIT License (MIT)

Copyright (c) Arctelix and all prior contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
