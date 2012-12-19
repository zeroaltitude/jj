from django.http import HttpResponse
from django.core.serializers import json, serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.conf import settings

from base64 import urlsafe_b64encode, urlsafe_b64decode

import urlparse, hashlib, hmac, traceback, urllib2

from facebook import Facebook

def get_ticket(journal_id):
	"""
		Create valid order ticket.
	"""
	md5 = hashlib.new('md5')
	md5.update("%s%s" % (settings.SHOP_SECRET, journal_id))
	return md5.hexdigest()


# Django-snippets:
class JsonResponse(HttpResponse):
	def __init__(self, object, request):
		if isinstance(object, QuerySet):
			content = serialize('json', object)
		else:
			content = simplejson.dumps(
				object, indent=2, cls=json.DjangoJSONEncoder,
				ensure_ascii=False)
		if request and request.REQUEST.get('callback', None):
			content = '%s(%s);' % (request.REQUEST['callback'], content)
		super(JsonResponse, self).__init__(
			content, content_type='application/x-javascript')


def retrieve_facebook_cookie(request):
	"""
		Get the FB 3rd-party+ login cookie
	"""
	return request.COOKIES.get("fbsr_%s" % settings.FACEBOOK_APP_ID, None)


def get_facebook_code(request):
	"""
		Grab a facebook access token from the request.
	"""
	cook = retrieve_facebook_cookie(request)
	tok_obj = parse_facebook_cookie(cook)
	print "Found tok_obj: %s" % tok_obj
	return tok_obj['code']


def get_facebook_uid(request):
	"""
		Grab a facebook access token from the request.
	"""
	cook = retrieve_facebook_cookie(request)
	tok_obj = parse_facebook_cookie(cook)
	return tok_obj['user_id']


def get_facebook_access_token(request):
	"""
		Grab a facebook access token from the request.
	"""
	if request.session.get("access_token", None):
		return request.session['access_token']
	else:
		# get it from the cookie if possible
		return request.COOKIES.get("jj_access_token", None)


def parse_facebook_cookie(facebook_cookie):
	"""
		Verify and return an object with the plaintext values from the cookie.
	"""
	encoded_sig, payload = facebook_cookie.split('.')
	decoded_sig = uri_b64decode(encoded_sig)
	decoded_data = uri_b64decode(payload)
	data_obj = simplejson.loads(decoded_data)
	if data_obj['algorithm'].upper() != 'HMAC-SHA256':
		raise Exception("Unknown algorithm: %s; expected: HMAC-SHA256" % data_obj['algorithm'])
	# check sig
	calculated_sig = hmac.new(settings.FACEBOOK_SECRET_KEY, msg=payload, digestmod=hashlib.sha256).digest()
	if calculated_sig != decoded_sig:
		raise Exception("Bad Signed JSON signature: %s, expected: %s!" % (decoded_sig, calculated_sig))
	return data_obj


# http://fi.am/entry/urlsafe-base64-encodingdecoding-in-two-lines/
def uri_b64encode(s):
     return urlsafe_b64encode(s).strip('=')


def uri_b64decode(s):
     return urlsafe_b64decode(s + '=' * (4 - len(s) % 4))


def get_facebook_api(request):
	"""
		This will return None on failure (we call this from places where we know there's no API -- responsible for checking None condition on other IFs)
	"""
	from jjmaker.models import get_user_profile, new_user_profile
	fb = Facebook(settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)

	# Use the data from the cookie if present
	try:
		auth_token = get_facebook_access_token(request)
	except:
		auth_token = request.GET.get('auth_token', None)

	try:
		fb.auth_token = auth_token
		userprofile_id = get_facebook_uid(request)
	except KeyError, MultiValueDictKeyError:
		traceback.print_exc()
		fb = None

	if not userprofile_id:
		userprofile_id = request.session.get('userprofile_id', request.COOKIES.get('userprofile_id', None))
	print "uid is %s, fb is (%s)" % (userprofile_id, fb)
	if userprofile_id:
		userprofile = get_user_profile(request, pid=userprofile_id)
	else:
		raise Exception("Failed to find a userprofile_id anywhere")

	if fb and not userprofile:
		# make a userprofile if none already:
		tok = fb.auth_token or fb.auth.createToken()
		# getinfo: http://developers.facebook.com/docs/reference/rest/users.getInfo
		# * uid
		# * first_name
		# * middle_name
		# * last_name
		# * name
		# * locale
		# * current_location
		# * affiliations (regional type only)
		# * pic_square
		# * profile_url
		# * sex
		values = fb.users.getInfo([userprofile_id], ['uid', 'first_name', 'last_name', 'name', 'profile_url', 'pic_square', 'is_app_user', 'has_added_app'])[0]
		userprofile = new_user_profile(values['uid'], values['first_name'], values['last_name'], values['name'], values['profile_url'], tok, 'unknown@unknown.com')
		userprofile_id = values['uid']
	request.session['userprofile_id'] = userprofile_id
	return fb


