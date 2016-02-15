from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from main.forms import GroupProfileForm, GroupReadOnlyForm, UpdateProfilePictureForm
from .models import UserProfile, GroupProfile, PendingInvite, UserActivityLog
import json
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User

import hashlib
import random
import re

# Create your views here.
def index(request):
    return render(request, 'main/index.html', {})

def profile(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Update that @user_profile has viewed this page
    new_log = UserActivityLog()
    new_log.user = request.user
    new_log.page_viewed = UserActivityLog.PROFILE
    new_log.save()

    #send_mail("try", "message", 'mathfeud@psychstat.org', ['xwang29@nd.edu'], fail_silently=False)
    if request.method == 'POST':
        p = request.POST
        form = UpdateProfilePictureForm(p, request.FILES)
        if form.is_valid():
            newPic = form.cleaned_data['newPic']
            user_profile.picture = newPic            
            user_profile.save()
    else:
        form = UpdateProfilePictureForm()

    context_dict = {}
    context_dict['user'] = request.user
    context_dict['user_profile'] = user_profile
    context_dict['group'] = user_profile.group
    context_dict['form'] = form
    context_dict['is_admin'] = request.user.groups.filter(name='groupAdmin').exists()
    if (context_dict['is_admin']):
        context_dict['group_members'] = UserProfile.objects.filter(group=user_profile.group)
        context_dict['pending_invite'] = PendingInvite.objects.filter(group=user_profile.group)
    return render(request, 'main/profile.html', context_dict)

def create_activation_key():
    #salt = hashlib.sha1(six.text_type(random.random()).encode('ascii')).hexdigest()[:5]
    #salt = salt.encode('ascii')
    #activation_key = hashlib.sha1(salt).hexdigest()
    return get_random_string(length=12, allowed_chars=u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

def is_valid_email(invite_email):
	pending_invites = PendingInvite.objects.filter(email = invite_email)
	registered_users = User.objects.filter(email = invite_email)
	if (pending_invites.exist()):
		return False, "Invitation already sent!"
	if (registered_users.exist()):
		return False, "Email already registered!"

def send_invite(request):
	invite_email = None
	if request.method == 'POST':
		invite_email = request.POST.get('invite_email')
		response_data = {}

		subject = "Mathfeud Invite"
		user_profile = UserProfile.objects.get(user=request.user)
		activation_key = create_activation_key()
		#activation_key = "1"
		message = "Active your account for group " + user_profile.group.name + "at " + request.build_absolute_uri(reverse('member_register')) + "?group_name=" +  activation_key
		#test if the email address is valid
		is_valid, email_error_message = is_valid_email(invite_email)
		if (not is_valid):
			response_data['result'] = email_error_message
			response_data['status'] = '0'
			return HttpResponse(
				json.dumps(response_data),
				content_type = "application/json"
			)
		try:	
			send_mail(subject, message, 'mathfeud@psychstat.org', [invite_email], fail_silently=False)
			response_data['result'] = 'Get email successfully!'
			response_data['status'] = '1'
			pending_invite = PendingInvite.objects.create(group=user_profile.group, email=invite_email, activation_key=activation_key)
			pending_invite.save()
		except:
			response_data['result'] = 'Did not sent out email!'
			response_data['status'] = '0'
		response_data['group'] = user_profile.group.name
		return HttpResponse(
			json.dumps(response_data),
			content_type = "application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type = "application/json"
		)

def jsonView(request):
	response_data = {
    "activities-heart": [
        {
            "dateTime": "2015-08-04",
            "value": {
                "customHeartRateZones": [],
                "heartRateZones": [
                    {
                        "caloriesOut": 740.15264,
                        "max": 94,
                        "min": 30,
                        "minutes": 593,
                        "name": "Out of Range"
                    },
                    {
                        "caloriesOut": 249.66204,
                        "max": 132,
                        "min": 94,
                        "minutes": 46,
                        "name": "Fat Burn"
                    },
                    {
                        "caloriesOut": 260,
                        "max": 160,
                        "min": 132,
                        "minutes": 20,
                        "name": "Cardio"
                    },
                    {
                        "caloriesOut": 135,
                        "max": 220,
                        "min": 160,
                        "minutes": 5,
                        "name": "Peak"
                    }
                ],
                "restingHeartRate": 68
            }
        }
    ]
}
 
	return HttpResponse(json.dumps(response_data), content_type="application/json")
