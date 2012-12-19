from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.utils import simplejson

import traceback, pprint, unicodedata, random, cStringIO, Image, urllib2, re
from operator import attrgetter, itemgetter
from decimal import Decimal
from tempfile import NamedTemporaryFile
import urlparse

from django.utils.decorators import decorator_from_middleware

from jotjournal_utils import JsonResponse, get_facebook_api, get_ticket, get_facebook_access_token, retrieve_facebook_cookie
from jjmaker.models import get_system_profile, get_user_profile, new_user_profile, unsubscribe, mget_fid, create_shipping, create_order, get_coupon, set_journal_title, set_activity, Journal

from jjmaker.renderers import JSONRenderer, CSSRenderer, PDFRenderer, format_title
from jjmaker.shop import purchase

from datetime import datetime, timedelta

from django.core.mail import send_mail


# http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
control_chars = ''.join(map(unichr, range(0,32) + range(127,255)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))
def remove_control_chars(s):
    return control_char_re.sub('', s)


uco_re = re.compile('\\\u\d*')
def squash_unicode_ref(s):
    return uco_re.sub('', s)


# http://wiki.python.org/moin/EscapingHtml
html_escape_table = {
	"&": "&amp;",
	'"': "&quot;",
	#"'": "&#39;",
	">": "&gt;",
	"<": "&lt;",
}
def html_escape(text):
	"""Produce entities within text."""
	return "".join(html_escape_table.get(c,c) for c in text)


def sanitize_message(message, no_html_escape=False):
	# possible unicode or bad chars in message
	if type(message) == 'unicode':
		message = unicodedata.normalize('NFKD', message).encode('ASCII', 'ignore')
	# by force, if necessary
	message = remove_control_chars(message)
	if not no_html_escape:
		# escape html characters
		message = html_escape(message)
	return squash_unicode_ref(message)


def setup_access_token(request):
	if not request.session.get('access_token', None):
		request.session['access_token'] = request.REQUEST.get('access_token', None)


def default_view(template):
	"""
		This decorator wraps up all of the global context set-up.
	"""
	t = loader.get_template(template)
	def wrap(view_function):
		def view(request, *args, **kwargs):
			if settings.PROMOTION_ONLY and not request.session.get('promotion', None):
				return HttpResponseRedirect('https://myjotjournal.com')
			setup_access_token(request)
			try:
				access_token = get_facebook_access_token(request)
			except:
				access_token = None
			c = Context({ 'settings': settings, 'access_token': access_token })
			if access_token:
				fb = get_facebook_api(request)
			else:
				fb = None
			userprofile = get_user_profile(request)
			systemuserprofile = get_system_profile()
			view_function(request, context=c, cookie=retrieve_facebook_cookie(request), template=t, facebook=fb, userprofile=userprofile, systemuserprofile=systemuserprofile, **kwargs)
			return HttpResponse(content=t.render(c))
		return view
	return wrap


def json_view(view_function):
	"""
		Like default_view, but since no template, no arguments-style decorator needed.
	"""
	def view(request, *args, **kwargs):
		if settings.PROMOTION_ONLY and not request.session.get('promotion', None):
			return HttpResponseRedirect('https://myjotjournal.com')
		setup_access_token(request)
		try:
			access_token = get_facebook_access_token(request)
		except:
			access_token = None
		c = Context({ 'settings': settings, 'access_token': access_token })
		try:
			fb = get_facebook_api(request)
		except:
			fb = None
		userprofile = get_user_profile(request)
		systemuserprofile = get_system_profile()
		content = view_function(request, context=c, cookie=retrieve_facebook_cookie(request), facebook=fb, userprofile=userprofile, systemuserprofile=systemuserprofile, **kwargs)
		return JsonResponse(content, request)
	return view


######################################################################## Flow pages ###############################################################################
def promotion(request):
	"""
		Set up the session for a free journal.
	"""
	referer = request.META.get('HTTP_REFERER', '')
	if referer.find("blog.myjotjournal.com") != -1 or request.REQUEST.get('klute', '') == 'elements':
		request.session['promotion'] = 1
		return HttpResponseRedirect('/jjmaker/?promotion=1')
	else:
		return HttpResponseRedirect('/jjmaker/?promotion=0')


@default_view('jjmaker/tos.html')
def tos(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		Terms of service page.
	"""
	pass


@default_view('jjmaker/popunder.html')
def popunder(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		Popunder page.
	"""
	if request.method == 'POST':
		r = request.REQUEST.getlist("r")
		if type(r) == tuple or type(r) == list:
			r = ",".join(r)
		o = request.REQUEST.get("lr", '')
		text = "Answer r: %s\n\nAnswer o: %s\n" % (r, o)
		send_mail("JotJournal Popunder", text, "jotjournal@myjotjournal.com", ["jotjournal@myjotjournal.com"], fail_silently=False)
		context['posted'] = 1
	pass


@default_view('jjmaker/debug_create_flow_page1.html')
def create_debug(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		This is the debugging path of the create a journal flow.
	"""
	pass


@default_view('jjmaker/landing.html')
def landing(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		Unconnected to FB landing.
	"""
	pass


@default_view('jjmaker/create.html')
def create(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		After connect, you can create.
	"""
	userprofile.token = get_facebook_access_token(request)
	userprofile.save()


@default_view('jjmaker/review.html')
def review(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Review what you did.
	"""
	journal = userprofile.get_journal(journal_id)
	context['journal_id'] = journal_id
	context['journal_title'] = journal.get_title().replace('<br>', ' ').replace('<br/>', ' ')
	context['journal_subtitle'] = journal.get_subtitle()
	context['commands'] = JSONRenderer(journal).render()
	context['shop_prefix'] = settings.SHOP_PREFIX # in production sends user to https


@default_view('jjmaker/thanks.html')
def thanks(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Post order landing.
	"""
	ticket = request.REQUEST.get('ticket', None)
	test_ticket = get_ticket(journal_id)
	journal = userprofile.get_journal(journal_id)
	context['journal_id'] = journal_id
	context['order_id'] = journal_id
	context['app_host'] = settings.APP_HOST
	context['promotion'] = request.session.get('promotion', 0)
	if ticket != test_ticket:
		settings.SHOP_LOGGER.info("Failed to validate journal order for journal id %s (%s vs %s) -- showing normal thanks page with no indication of failure (happens in normal case of person submitting through Facebook form)" % (journal_id, ticket, test_ticket))
	else:
		send_mail("JotJournal Order number %s%s" % (journal_id, settings.DEVELOPMENT_TAG), "The following journal was ordered: %s" % journal_id, "jotjournal@myjotjournal.com", ["jotjournal@myjotjournal.com"], fail_silently=False)
		if userprofile.email:
			send_mail("JotJournal Order number %s%s" % (journal_id, settings.DEVELOPMENT_TAG), settings.THANKS_EMAIL % (userprofile.fb_name, journal_id), "jotjournal@myjotjournal.com", [userprofile.email], fail_silently=False)


@default_view('jjmaker/shop.html')
def shop(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Shopping cart.
	"""
	try:
		journal = userprofile.get_journal(journal_id)
	except:
		# no idea -- reverse initialize:
		journal = Journal.objects.filter(pk=journal_id)[0]
		userprofile = journal.user
		# verify that this facebook user's ID is secure (matches this userprofile's facebook ID)
		if facebook.uid != userprofile.fb_id:
			raise Exception("Fatal: cannot access this journal (%s) from this user profile (%s/%s); fbid: %s" % (journal_id, userprofile.id, userprofile.fb_id, facebook.uid))
	context['journal_id'] = journal_id
	context['journal_title'] = journal.get_title().replace('<br>', ' ').replace('<br/>', ' ')
	context['promotion'] = request.session.get('promotion', 0)


@default_view('jjmaker/unsubscribe.html')
def unsubscribe_view(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Begin shopping cart.
	"""
	email = request.REQUEST.get('email', None)
	if email:
		context['unsubscribed'] = "%s unsubscribed" % email
		unsubscribe(email)
######################################################################## /Flow pages ##############################################################################


######################################################################## View pages ###############################################################################
def journal_1_pdf(request, journal_id):
	"""
		A PDF viewer for journal templates 1 and 2 (should work for any gravity template with 33 pages).
	"""
	access_token = get_facebook_access_token(request)
	c = Context({ 'settings': settings, 'access_token': access_token })
	fb = get_facebook_api(request)
	userprofile = get_user_profile(request)
	systemuserprofile = get_system_profile()
	journal = userprofile.get_journal(journal_id)
	my_io = cStringIO.StringIO()
	PDFRenderer(journal).render(my_io, for_shipping=True)
	http_response = HttpResponse(my_io.getvalue())
	http_response['Content-Type'] = 'application/pdf'
	http_response['Content-Disposition'] = 'attachment; filename="my_journal.pdf"'
	return http_response


@default_view('jjmaker/journal_1_view.html')
def journal_1_view(request, context=None, cookie=None, template=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		An HTML viewer for journal templates 1 and 2 (should work for any gravity template with 33 pages).
	"""
	journal = userprofile.get_journal(journal_id)
	context['journal_id'] = journal_id
	context['commands'] = JSONRenderer(journal).render()


def journal_stylesheet(request, journal_id=None):
	"""
		A css render for this journal.
	"""
	userprofile = get_user_profile(request)
	journal = userprofile.get_journal(journal_id)
	stylesheet = CSSRenderer(journal).render()
	return HttpResponse(content=stylesheet, content_type='text/css')


def journal_1_popimg(request, journal_id, upload=False):
	"""
		Returns a small image representing a small collection of popular images from the journal.
	"""
	access_token = get_facebook_access_token(request)
	c = Context({ 'settings': settings, 'access_token': access_token })
	fb = get_facebook_api(request)
	userprofile = get_user_profile(request)
	systemuserprofile = get_system_profile()
	## this should be secured a bit more -- leaks a photo to the public
	journal = systemuserprofile.get_journal(journal_id)
	my_io = get_popular_images_repr_2(journal)
	http_response = HttpResponse(my_io.getvalue())
	http_response['Content-Type'] = 'image/jpg'
	#
	#
	if request.REQUEST.get('share', None):
		fb.uid = request.session['userprofile_id']
		fb.photos.upload(my_io.getvalue(), filename='test.jpg', caption='Hello, fbWorld!')
	#
	#
	return http_response
######################################################################## /View pages ##############################################################################


def get_popular_images_repr_2(journal):
	"""
		Alternate image render function.
	"""
	photo = journal.get_popular_photos()[0]
	p = Image.open(cStringIO.StringIO(urllib2.urlopen(photo.fb_source).read()))
	b = Image.open(cStringIO.StringIO(urllib2.urlopen("https://myjotjournal.com/static/images/journal_images/shareback.png").read()))

	s = p.size
	if s[0] < s[1]:
		# crop image from top and bottom
		diff = s[1] - s[0]
		p = p.crop([0, diff/2, s[0], s[1] - diff/2])
	elif s[1] < s[0]:
		# crop image from left and right
		diff = s[0] - s[1]
		p = p.crop([diff/2, 0, s[0] - diff/2, s[1]])
	else:
		# nothing to be done -- straight resizing to 100x100 will work
		pass
	p = p.resize([323, 323])

	dest = Image.new('RGB', [600, 452])
	# draw onto dest
	dest.paste(b, [0, 0, 600, 452])
	dest.paste(p, [14, 12, 337, 335])

	io = cStringIO.StringIO()
	dest.save(io, "JPEG")
	return io


def get_popular_images_repr(journal):
	"""
		The actual image rendering function.
	"""
	photos = journal.get_popular_photos()[0:16] # could be multiple copies of each due to the popular_photos block(s)
	already_sources = []
	p = []
	pr = []
	# thread this later
	for photo in photos:
		if not photo.fb_source in already_sources:
			p.append(Image.open(cStringIO.StringIO(urllib2.urlopen(photo.fb_source).read())))
			already_sources.append(photo.fb_source)
		if len(p) == 4:
			break
	# crop each element in p to a 300x300 box
	for photo in p:
		s = photo.size
		if s[0] < s[1]:
			# crop image from top and bottom
			diff = s[1] - s[0]
			photo = photo.crop([0, diff/2, s[0], s[1] - diff/2])
		elif s[1] < s[0]:
			# crop image from left and right
			diff = s[0] - s[1]
			photo = photo.crop([diff/2, 0, s[0] - diff/2, s[1]])
		else:
			# nothing to be done -- straight resizing to 100x100 will work
			pass
		pr.append(photo.resize([300, 300]))
	dest = Image.new('RGB', [600, 600])
	# draw onto dest
	dest.paste(pr[0], [0, 0, 300, 300])
	dest.paste(pr[1], [300, 0, 600, 300])
	dest.paste(pr[2], [0, 300, 300, 600])
	dest.paste(pr[3], [300, 300, 600, 600])
	io = cStringIO.StringIO()
	dest.save(io, "JPEG")
	return io


def have_enough_content(need, have_photos, have_texts):
	"""
		Do we have enough texts and photos to make a journal?  Let's say we do when the photos plus
		texts are at least 125 percent of what is needed for the book (a normal case is a paucity of
		texts, which we'll treat as OK).
	"""
	print "Need: %s, have_photos: %s, have_texts: %s" % (need, have_photos, have_texts)
	return (((have_photos + have_texts) * 0.9) > need)


def setup_firstpass_metadata(pages):
	"""
		Here, we are going to go from database to memory so we can collect data and then work through
		the content-fitting piece.  Iterate the pages of the journal to find out how many photos and
		texts are needed and where the quadrants are.

		{	
			'photos_needed': #,
			'texts_needed': #,
			'total_needed': #,
			'journal': [
				{
					'page_number': 1,
					'photos_needed': #,
					'texts_needed': #,
					'total_needed': #,
					'quadrants': [
						{ 'coordinate_x': #, 'coordinate_y': #, 'units_x': #, 'units_y': #, 'filled_by': <text or photo> }, #<-- fill in
						...
					]
				},
				...
			]
		}
	"""
	ptdict = {
		'photos_needed': 0,
		'texts_needed': 0,
		'popular_photos_needed': 0,
		'popular_texts_needed': 0,
		'total_needed': 0,
		'journal': []
	}

	for page in pages:
		template = page.page_template
		style = page.page_style
		qs = template.get_quadrants()
		#print "Page %s, got %s quadrants, %s desired photos, %s desired texts" % (page.page_number, len(qs), template.total_photos, template.total_texts)
		pagedict = {
			'page_number': page.page_number,
			'photos_needed': template.total_photos,
			'texts_needed': template.total_texts,
			'total_needed': template.total_photos + template.total_texts,
			'quadrants': []
		}
		ptdict['photos_needed'] += template.total_photos
		ptdict['texts_needed'] += template.total_texts
		ptdict['total_needed'] += template.total_photos + template.total_texts
		for q in qs:
			#print "Quadrant %s x %s, units %s x %s" % (q.coordinate_x, q.coordinate_y, q.units_x, q.units_y)
			pagedict['quadrants'].append({
				'coordinate_x': q.coordinate_x,
				'coordinate_y': q.coordinate_y,
				'units_x': q.units_x,
				'units_y': q.units_y,
				'filled_by': None
			})
			if q.content_type == 'popular:photo':
				ptdict['popular_photos_needed'] += 1
			elif q.content_type == 'popular:message':
				ptdict['popular_texts_needed'] += 1
				
		ptdict['journal'].append(pagedict)

	return ptdict


def set_next_photo(plist, pindex, picked_photo_id, receipt_file=None):
	"""
		Rearrange plist so that the next item in the list (pindex) is picked_photo_id.
	"""
	if receipt_file:
		receipt_file.write("\t\t\tLooking at photo index %s and examining %s, %s\n" % (pindex, plist[pindex]['id'], picked_photo_id))
	if plist[pindex]['id'] == picked_photo_id:
		# nothing to do
		if receipt_file:
			receipt_file.write("\t\t\tNo swap\n")
		return
	for r in range(pindex, len(plist)):
		photo = plist[r]
		if photo['id'] == picked_photo_id:
			# swap
			tmp = plist[pindex]
			if receipt_file:
				receipt_file.write("\t\t\tSwapping %s (%s) for %s (%s)\n" % (photo['id'], r, tmp['id'], pindex))
			plist[pindex] = photo
			plist[r] = tmp


def battle(page, plist, tlist, pindex, tindex, coordx, coordy, receipt_file=None):
	"""
		We're iterating the photos list and text list.  At every choice point, the travelling-indexed photo battles the
		travelling-indexed text to determine which one goes in this slot of the journal.
	"""
	linked = None
	winner = None
	picked_type = ''
	skip_text = 0

	# if someone has run out (e.g. no more photos), select winner:
	if tindex >= len(tlist):
		if receipt_file:
			receipt_file.write("\t\tBattle won by photo (no text left)!\n")
		winner = plist[pindex]
		picked_type = 'photo'
	else:
		titem = tlist[tindex]

	if not winner:
		if pindex >= len(plist):
			if not titem:
				if receipt_file:
				 	receipt_file.write("\t\t!! UH OH -- no text, no photos, bailing\n")
				winner = None
				picked_type = 'none'
			else:
				if receipt_file:
					receipt_file.write("\t\tBattle won by text!  No photos left!  Winner: %s\n" % titem['id'])
				winner = titem
				picked_type = "text"
		else:
			pitem = plist[pindex]

		if not winner:
			photo_date = datetime.strptime(pitem['mysql_date'] or '1970-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
			text_date = datetime.strptime(titem['mysql_date'] or '1970-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
			if text_date >= photo_date:
				# check linking: require linked photos to be "above" linked text
				# if position doesn't allow that, reset winner to the photo, put it in place
				# then *link the text*, forcing it to be below.
				if titem['linked_to']:
					set_next_photo(plist, pindex, titem['linked_to'], receipt_file=receipt_file)
					# indexed item may have changed:
					pitem = plist[pindex]
					if coordy > 0:
						#####################################
						if pitem['id'] == titem['linked_to']:
							# link the photo:
							if receipt_file:
								receipt_file.write("\t\tLinked the photo %s\n" % pitem)
							linked = pitem
						#####################################
						if receipt_file:
							receipt_file.write("\t\tText won %s\n" % titem)
						winner = titem
						picked_type = 'text'
					else:
						#####################################
						if titem['linked_to'] == pitem['id']:
							# winner is photo, *link the text*
							if receipt_file:
								receipt_file.write("\t\tSwitching it up.  Photo wins (%s), text linked (%s)\n" % (pitem, titem))
							linked = titem
						#####################################
						if receipt_file:
							receipt_file.write("\t\tPhoto won %s\n" % pitem)
						winner = pitem
						picked_type = 'photo'
				else:
					if receipt_file:
						receipt_file.write("\t\tText was later. No linking.  Set winner to text %s\n" % titem)
					winner = titem
					picked_type = "text"
			else:
				if receipt_file:
					receipt_file.write("\t\tPhoto was later. Set winner to photo %s\n" % pitem)
				winner = pitem
				picked_type = "photo"

	if receipt_file:
		receipt_file.write("\tBattle result; winner: %s, linked_item: %s\n" % (winner['id'], linked))

	return winner, linked, picked_type, skip_text


@json_view
def promotion_checkout(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Set up the completion of a free journal order.
	"""
	firstname = request.REQUEST['firstname']
	middlename = request.REQUEST['middlename']
	lastname = request.REQUEST['lastname']
	street = request.REQUEST['street']
	street2 = request.REQUEST['street2']
	city = request.REQUEST['city']
	state = request.REQUEST['state']
	zip = request.REQUEST['zip']
	country = request.REQUEST['country']
	email = request.REQUEST['email']
	userprofile.email = email
	userprofile.save()
	phone = request.REQUEST['phone']
	quantity = request.REQUEST['quantity']
	if request.session.get('promotion', 0) == 1:
		# create order-related db entries
		shipping = create_shipping(firstname=firstname, middlename=middlename, lastname=lastname, addr1=street, addr2=street2, city=city, state=state, zip=zip, country=country, telephone=phone)
		# XXX unitprice: replace with product's unit price HACK TODO FIXME
		order = create_order(userprofile=userprofile, shipping=shipping, journal_id=journal_id, quantity=quantity, status='promotion', ccauth='OK', notes='promotional journal:email:%s' % email,
							 unitprice=0.0, shippingprice=0.0, tax=0.0, coupon_id=None)
		# create validation ticket
		return { 'ticket': get_ticket(journal_id) }
	else:
		return { 'silly': 'rabbit' }


@json_view
def get_fid(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None, quadrant_id=None):
	"""
		Gets the Facebook ID associated with a journal's quadrant
	"""
	return { 'fid': mget_fid(journal_id, quadrant_id) }


@json_view
def set_title(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Set a journal title.
	"""
	return { 'status': set_journal_title(journal_id, request.REQUEST['title'], request.REQUEST['subtitle'], change_cover=True) }


@json_view
def apply_coupon(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Tests a coupon code and on success sets certain price modifiers.
	"""
	c = get_coupon(request.REQUEST['coupon'])
	if c:
		return { 'ctype': c.ctype, 'amount': c.amount }
	else:
		return {}


@json_view
def disconnect(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Clears the session.
	"""
	request.session['userprofile_id'] = None
	return { 'status': 'OK' }


@json_view
def too_little_content(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		This user had too little content as detected by the client; note it in the logs
	"""
	photo_count = request.REQUEST['photoCount']
	text_count = request.REQUEST['textCount']
	settings.SHOP_LOGGER.exception("Facebook uid %s had too little content (%s, %s) at %s" % (request.session['userprofile_id'], photo_count, text_count, str(datetime.now())))
	set_activity(userprofile=userprofile, fb_id=request.session['userprofile_id'], metadata={ 'photo_count': photo_count, 'text_count': text_count })
	return { 'status': 'OK' }


@json_view
def share(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Shares the popular photos representative image to Facebook.
	"""
	message = request.REQUEST.get('message', 'My newest JotJournal')
	journal = userprofile.get_journal(journal_id)
	my_io = get_popular_images_repr_2(journal)
	facebook.uid = request.session['userprofile_id']
	facebook.photos.upload(my_io.getvalue(), filename='share.jpg', caption=message)
	return { 'status': 'OK' }


@json_view
def checkout(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None, journal_id=None):
	"""
		Credit card order through Paypal.
	"""
	journal = userprofile.get_journal(journal_id)
	context['journal_id'] = journal_id
	amt = request.REQUEST['amt']
	shipping = request.REQUEST['shipping']
	tax = request.REQUEST['tax']
	firstname = request.REQUEST['firstname']
	middlename = request.REQUEST['middlename']
	lastname = request.REQUEST['lastname']
	street = request.REQUEST['street']
	street2 = request.REQUEST['street2']
	city = request.REQUEST['city']
	state = request.REQUEST['state']
	zip = request.REQUEST['zip']
	ccnum = request.REQUEST['ccnum']
	cctype = request.REQUEST['cctype']
	ccexp_mo = request.REQUEST['ccexp_mo']
	ccexp_yr = request.REQUEST['ccexp_yr']
	csc = request.REQUEST['csc']
	phone = request.REQUEST['phone']
	countrycode = request.REQUEST['countrycode']
	currencycode = request.REQUEST['currencycode']
	email = request.REQUEST['email']
	userprofile.email = email
	userprofile.save()
	quantity = request.REQUEST['quantity']
	coupon = request.REQUEST['coupon']
	return {
		'ticket': purchase(userprofile=userprofile, amt=amt, shippingprice=shipping, tax=tax, cctype=cctype, ccnum=ccnum, expdate="%s%s" % (ccexp_mo, ccexp_yr), csc=csc, firstname=firstname, middlename=middlename,
					lastname=lastname, street=street, street2=street2, city=city, state=state, zip=zip, phone=phone,
					countrycode=countrycode, currencycode=currencycode, journal_id=journal_id, email=email, ipaddress=request.META['REMOTE_ADDR'], quantity=quantity, coupon=coupon)
	}


def get_captions(photos, texts):
	"""
		Gets the caption texts out of the list of captions.
	"""
	ret = []
	for photo in photos:
		done = False
		id = photo['id']
		#print 'Scanning for %s' % id
		for text in texts:
			#print 'testing %s' % text['linked_to']
			if text['linked_to'] == id:
				done = True
				ret.append(text)
				texts.remove(text)
		if not done:
			d = datetime.strptime(photo['mysql_date'], '%Y-%m-%d %H:%M:%S')
			x = "%s %d, %s" % (d.strftime('%B')[0:3], int(d.strftime('%d')), d.strftime('%Y'))
			ret.append(
				{
					'id': 't_d_r_%s' % id,
					'link': photo['link'],
					'mysql_date': photo['mysql_date'],
					'type': 'text',
					'event': 0,
					'score': 0,
					'message': x
				}
			)
	return ret


def get_popular_texts(popular_texts, num_needed):
	retarr = []
	numfound = 0
	for p in popular_texts:
		if numfound == num_needed:
			break
		if p['type'] == "status":
			retarr.append(p)
			numfound += 1
	return retarr


@json_view
def journal(request, context=None, cookie=None, facebook=None, userprofile=None, systemuserprofile=None):
	"""
		Responsible for making a journal and populating it with chosen items (by score, event grouping, etc).
	"""
	try:
		texts = simplejson.loads(request.REQUEST['texts'])
		texts.reverse()
		photos = simplejson.loads(request.REQUEST['photos'])
		photos.reverse()
		template = request.REQUEST.get('template', 1)
		metadata = request.REQUEST.get('metadata', '')

		sufficient = False

		journal_template = systemuserprofile.get_journal_template(template)
		pages = journal_template.get_pages()
		print "Using template journal %s, got %s pages" % (template, len(pages))

		ptdict = setup_firstpass_metadata(pages)
		#pprint.PrettyPrinter().pprint(ptdict)

		# now limit the popular dictionaries to the first NEEDED entries:
		popular_photos = sorted(photos, key=itemgetter('score'), reverse=True)
		popular_photos = popular_photos[0:ptdict['popular_photos_needed']]
		# remove popular captions from texts list before calculating popular texts
		popular_captions = get_captions(popular_photos, texts)
		# now the popular texts list will only try to find texts that were not already removed for the popular photos' captions list
		popular_texts = sorted(texts, key=itemgetter('score'), reverse=True)
		# filter by correct type (status, not caption) and limit to number we need
		popular_texts = get_popular_texts(popular_texts, ptdict['popular_texts_needed'])

		# now, remove the popular items from the larger list of things
		for _i in popular_photos:
			photos.remove(_i)
		for _i in popular_texts:
			texts.remove(_i)

		new_journal = None
		earliest = None
		latest = None
		njid = 0
		exc = ''

		if (have_enough_content(ptdict['total_needed'], len(photos), len(texts))):
			sufficient = True
			p_lindex = 0
			t_lindex = 0
			# make a new journal for this user:
			new_journal = userprofile.new_journal('My new journal', journal_template)
			njid = new_journal.id
			#
			#
			# Receipt: a decision tree file
			receipt = NamedTemporaryFile(suffix='.txt', prefix="manifest_journal_%s_" % new_journal.id, dir='/tmp/', delete=False)
			receipt.write("\nmetadata\n%s\n" % metadata)
			debug_dump(receipt, popular_photos, photos, popular_texts, texts, popular_captions)
			#
			#
			# populate the pages backwards:
			# Temporarily adding unconditional outer try/except in order to track down customer problems.  Probably should be removed later. -EA
			try:
				ptdict['journal'].reverse()
				for ppage in ptdict['journal']:
					page = new_journal.get_page(ppage['page_number'])
					page_dimension_x, page_dimension_y = page.get_grid_dimensions()
					page_quadrant_native_aspect = Decimal(page_dimension_y)/Decimal(page_dimension_x)
					receipt.write("\n\nPage %s (%s) -- photo_index: %s, text_index: %s\n" % (ppage['page_number'], page.page_number, p_lindex, t_lindex))
					# backwards, remember
					ppage['quadrants'].reverse()
					for pquadrant in ppage['quadrants']:
						x = pquadrant['coordinate_x']
						y = pquadrant['coordinate_y']
						receipt.write("\t****Quadrant x y %s, %s -- photo_index: %s, text_index: %s****\n" % (x, y, p_lindex, t_lindex))
						# Skip if already filled
						if pquadrant['filled_by'] == None:
							ptat = page.positional_thing_at(x, y)
							receipt.write("\t\tQuadrant id %s, type %s\n" % (ptat.id, ptat.content_type))
							#
							# Battle!
							skip_text = 0
							normal_increment = 1
							if ptat.content_type:
								normal_increment = 0
								if ptat.content_type == 'message':
									chosen_item, linked_item, picked_type = texts[t_lindex], None, 'text'
									receipt.write("\t\t\thit special content_type=message case, picked %s\n" % chosen_item)
								elif ptat.content_type == 'photo':
									chosen_item, linked_item, picked_type = photos[p_lindex], None, 'photo'
									receipt.write("\t\t\thit special content_type=photo case, picked %s\n" % chosen_item)
								elif ptat.content_type == 'popular:message':
									if popular_texts == None or len(popular_texts) == 0:
										chosen_item = None
										linked_item = None
										picked_type = None
										receipt.write("\t\t\thit special content_type=popular:message case, picked nothing from empty list")
									else:
										chosen_item, linked_item, picked_type = popular_texts.pop(), None, 'text'
										receipt.write("\t\t\thit special content_type=popular:message case, picked %s\n" % chosen_item)
								elif ptat.content_type == 'popular:photo':
									if popular_photos == None or len(popular_photos) == 0:
										chosen_item = None
										linked_item = None
										picked_type = None
										receipt.write("\t\t\thit special content_type=popular:photo case, picked nothing from empty list")
									else:
										chosen_item, linked_item, picked_type = popular_photos.pop(), None, 'photo'
										receipt.write("\t\t\thit special content_type=popular:photo case, picked %s\n" % chosen_item)
								elif ptat.content_type == 'popular:caption':
									if popular_captions == None or len(popular_captions) == 0:
										chosen_item = None
										linked_item = None
										picked_type = None
										receipt.write("\t\t\thit special content_type=popular:caption case, picked nothing from empty list")
									else:
										chosen_item, linked_item, picked_type = popular_captions.pop(), None, 'text'
										receipt.write("\t\t\thit special content_type=popular:caption case, picked %s\n" % chosen_item)
								elif ptat.content_type == 'title:with_date':
									receipt.write("\t\t\thit special content_type=title:with_date\n")
									picked_type = 'text'
									linked_item = None

									new_journal.set_meta("%s's<br/>JotJournal" % userprofile.fb_name, earliest, latest)
									new_journal.set_subtitle(None)
									message = format_title("%s's<br/>JotJournal" % userprofile.fb_name, new_journal.subtitle)

									chosen_item = {
										'id': ptat.content_type,
										'link': url,
										'mysql_date': '2010-09-29 07:57:00',
										'type': 'text',
										'event': 0,
										'score': 0,
										'message': message,
										'no_html_escape': True
									}
								elif ptat.content_type.startswith('static:'):
									receipt.write("\t\t\thit static content_type case (%s)\n" % ptat.content_type)
									prefix, url = ptat.content_type.split(':')
									url = 'https://myjotjournal.com/static/images/journal_images/%s' % url
									picked_type = 'photo'
									# ugh
									size = Image.open(cStringIO.StringIO(urllib2.urlopen(url).read())).size
									chosen_item = {
										'id': ptat.content_type,
										'link': url,
										'mysql_date': '2010-09-29 07:57:00',
										'type': 'photo',
										'event': 0,
										'score': 0,
										'width': size[0],
										'height': size[1],
										'picture': url,
										'source': url
									}
								else:
									receipt.write("\t\t\thit unknown content_type, doing nothing (%s)\n" % ptat.content_type)
									chosen_item = None
							else:
								chosen_item, linked_item, picked_type, skip_text = battle(page, photos, texts, p_lindex, t_lindex, x, y, receipt_file=receipt)
								if chosen_item and not latest:
									latest = chosen_item['mysql_date']
								earliest = chosen_item['mysql_date']

							if skip_text:
								t_lindex += skip_text
							#
							#
							if chosen_item:
								receipt.write("Chosen: %s,\n\tlinked: %s,\n\ttype: %s\n" % (chosen_item['id'], linked_item, picked_type))
								# create the item
								pquadrant['filled_by'] = chosen_item['id']
								if picked_type == 'text':
									receipt.write("\tPICKED TYPE: text (%s)\n" % chosen_item)
									t_lindex += normal_increment # will be 0 for special content types
									_message = sanitize_message(chosen_item['message'], no_html_escape=chosen_item.get('no_html_escape', False))
									try:
										page.add_item(item_type="text", positional_thing=ptat, fb_id=chosen_item['id'], fb_url=chosen_item['link'], 
											item_date=chosen_item['mysql_date'], fb_item_type=chosen_item['type'], event_id=chosen_item['event'], 
											score=chosen_item['score'], message=_message, length_chars=len(_message))
									except:
										# sanitize failed -- insert blank
										page.add_item(item_type="text", positional_thing=ptat, fb_id=chosen_item['id'], fb_url=chosen_item['link'], 
											item_date=chosen_item['mysql_date'], fb_item_type=chosen_item['type'], event_id=chosen_item['event'], 
											score=chosen_item['score'], message=' ', length_chars=1)
									if linked_item:
										receipt.write("Linked photo (%s)\n" % linked_item)
										p_lindex += 1 # linking only for normal content types
										# choose earlier row:
										if y > 0 and not page.get_journalitem_at(x, y - 1):
											lptat = page.positional_thing_at(x, y - 1)

											for tpquadrant in ppage['quadrants']:
												receipt.write("\tScanning quadrants for earlier row: %s, %s\n" % (tpquadrant['coordinate_x'], tpquadrant['coordinate_y']))
												if tpquadrant['coordinate_x'] == x and tpquadrant['coordinate_y'] == (y - 1):
													tpquadrant['filled_by'] = linked_item['id']
											receipt.write("Adding linked photo\n")
											if not linked_item.get('width', None):
												# ugh
												size = Image.open(cStringIO.StringIO(urllib2.urlopen(linked_item['source']).read())).size
												linked_item['width'] = size[0]
												linked_item['height'] = size[1]
											page.add_item(item_type="photo", positional_thing=lptat, fb_id=linked_item['id'], fb_url=linked_item['link'],
															item_date=linked_item['mysql_date'], fb_item_type=linked_item['type'], event_id=linked_item['event'],
															score=linked_item['score'], dimension_x=linked_item['width'], dimension_y=linked_item['height'],
															fb_picture=linked_item['picture'], fb_source=linked_item['source'])
										else:
											receipt.write("!! hit error case where we should have been able to link a photo to a quadrant never yet scanned %s, %s, %s\n" % (linked_item, y, x))
								else:
									p_lindex += normal_increment # will be 0 for special content types
									if not chosen_item.get('width', None):
										# ugh
										size = Image.open(cStringIO.StringIO(urllib2.urlopen(chosen_item['source']).read())).size
										chosen_item['width'] = size[0]
										chosen_item['height'] = size[1]
									page.add_item(item_type="photo", positional_thing=ptat, fb_id=chosen_item['id'], fb_url=chosen_item['link'], 
													item_date=chosen_item['mysql_date'], fb_item_type=chosen_item['type'], event_id=chosen_item['event'], 
													score=chosen_item['score'], dimension_x=chosen_item['width'], dimension_y=chosen_item['height'], 
													fb_picture=chosen_item['picture'], fb_source=chosen_item['source'])
									if linked_item:
										# linked text goes in next row
										t_lindex += 1 # linking only for normal content types
										# choose next row: (override, so no use checking "whether something's in the next row")
										lptat = page.positional_thing_at(x, y + 1)
										receipt.write("CLOBBERING WHAT IS AT %s (%s, %s)\n" % (lptat, x, y + 1))
										# if this is a 1-up, or any case with no next row, we can abort and not show this caption
										if lptat:
											for tpquadrant in ppage['quadrants']:
												receipt.write("\tScanning quadrants for later row: %s, %s\n" % (tpquadrant['coordinate_x'], tpquadrant['coordinate_y']))
												if tpquadrant['coordinate_x'] == x and tpquadrant['coordinate_y'] == (y + 1):
													tpquadrant['filled_by'] = linked_item['id']
											receipt.write("DELETING OLD TEXT\n")
											item = page.get_journalitem_at(x, y + 1)
											if item:
												item.delete()
											else:
												receipt.write("!! NO ITEM TO DELETE?\n")
											receipt.write("ADDING LINKED TEXT\n")
											_message = sanitize_message(linked_item['message'], no_html_escape=linked_item.get('no_html_escape', False))
											try:
												page.add_item(item_type="text", positional_thing=lptat, fb_id=linked_item['id'], fb_url=linked_item['link'], 
																item_date=linked_item['mysql_date'], fb_item_type=linked_item['type'], event_id=linked_item['event'], 
																score=linked_item['score'], message=_message, length_chars=len(_message))
											except:
												# sanitize failed, insert blank
												page.add_item(item_type="text", positional_thing=lptat, fb_id=linked_item['id'], fb_url=linked_item['link'], 
													item_date=linked_item['mysql_date'], fb_item_type=linked_item['type'], event_id=linked_item['event'], 
													score=linked_item['score'], message=' ', length_chars=1)
							else:
								# if there was no chosen item, we're just going to skip this quadrant and complain
								receipt.write("Problem: no item chosen for page %s, quadrant %s x, %s y -- %s, %s\n" % (page.page_number, x, y, p_lindex, t_lindex))

						else:
							receipt.write("Found pre-filled item at %s, %s (page %s)\n" % (x, y, page.page_number))
			except Exception as e:
				traceback.print_exc(file=receipt)
				sufficient = False
				exc = str(e)
			finally:
				receipt.close()

	except Exception as e:
		exc_receipt = NamedTemporaryFile(suffix='.txt', prefix="exception_create_journal_%s_" % str(datetime.now()), dir='/tmp/', delete=False)
		traceback.print_exc(file=exc_receipt)
		sufficient = False
		exc = str(e)
		exc_receipt.close()

	return { 'sufficient': sufficient, 'texts': texts, 'photos': photos, 'id': njid, 'exc': exc }


def debug_dump(receipt, arr1, arr2, arr3, arr4, arr5):
	try:
		receipt.write("POPULAR PHOTOS")
		for item in arr1:
			receipt.write("id:%s, event:%s, picture:%s, name:%s, mysql_date:%s, score:%s, created_time:%s, date:%s, updated_time:%s, type:%s\n"
				% (item['id'], item['event'], item['picture'], item.get('name', ''), item['mysql_date'], item['score'], item['created_time'], item['date'], item['updated_time'], item['type']))
		receipt.write("\n")
		receipt.write("PHOTOS")
		for item in arr2:
			receipt.write("id:%s, event:%s, picture:%s, name:%s, mysql_date:%s, score:%s, created_time:%s, date:%s, updated_time:%s, type:%s\n"
				% (item['id'], item['event'], item['picture'], item.get('name', ''), item['mysql_date'], item['score'], item['created_time'], item['date'], item['updated_time'], item['type']))
		receipt.write("\n")
		receipt.write("POPULAR TEXTS")
		for item in arr3:
			receipt.write("%s\n" % item)
		receipt.write("TEXTS")
		for item in arr4:
			receipt.write("%s\n" % item)
		receipt.write("POPULAR CAPTIONS")
		for item in arr5:
			receipt.write("%s\n" % item)
	except Exception as e:
		traceback.print_exc(file=receipt)



