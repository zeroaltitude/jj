from django.db import models
from django.conf import settings
from django.utils import simplejson

from tempfile import NamedTemporaryFile
import constants
import traceback
from datetime import datetime
from decimal import *

from jjmaker.renderers import format_title


#
# I use the term 'quadrant' to mean 'any of a number of uniform page rectangles in which things float rather than are sized to.'  Distinguished from mold, a thing into which a photo is sized and 
# likely cropped.
#

def get_coupon(coupon_code):
	"""
		Get the coupon referenced by the code.
	"""
	try:
		return Coupon.objects.filter(code=coupon_code)[0]
	except:
		return None


def create_shipping(firstname=None, middlename=None, lastname=None, addr1=None, addr2=None, city=None, state=None, zip=None, country=None, telephone=None):
	"""
		Create a shipping record.
	"""
	shipping = Shipping(firstname=firstname, middlename=middlename, lastname=lastname, addr1=addr1, addr2=addr2, city=city, state=state, zip=zip, country=country, telephone=telephone)
	shipping.save()
	return shipping


def create_order(userprofile=None, shipping=None, journal_id=0, quantity=0, status=None, ccauth=None, notes=None, unitprice=None, shippingprice=None, tax=None, coupon_id=None):
	"""
		Create an order record.
	"""
	product = Product.objects.filter(pk=1)[0]
	coupon = get_coupon(coupon_id)
	coupon_o_id = None
	if coupon:
		coupon_o_id = coupon.id
	order = Order(user=userprofile, product=product, shipping=shipping, journal_id=journal_id, quantity=quantity, status=status, ccauth=ccauth, notes=notes, unitprice=unitprice,
					shippingprice=shippingprice, tax=tax, coupon_id=coupon_o_id)
	order.save()
	return order


def set_journal_title(journal_id, title, subtitle, change_cover=False):
	"""
		Set a journal's title.
	"""
	j = Journal.objects.filter(pk=journal_id)[0]
	if title:
		j.title = title
	if subtitle:
		j.subtitle = subtitle
	j.save()
	if change_cover:
		j.set_itembased_title(title, subtitle)
	return 'OK'


def mget_fid(journal_id, quadrant_id):
	"""
		Gets the Facebook item id at a journal's quadrant
	"""
	item = JournalItem.objects.filter(journal_page__journal__pk=journal_id).filter(positional_thing=quadrant_id)[0]
	return item.fb_id


def unsubscribe(email):
	"""
		Convenience function.
	"""
	unsubscriber = Unsubscriber(email=email)
	unsubscriber.save()


def get_system_profile():
	"""
		Convenience function.
	"""
	return UserProfile.objects.filter(pk=1)[0]


def get_user_profile(request, pid=None):
	"""
		Convenience function.
	"""
	print "get_user_profile 1: %s" % pid
	if not pid:
		pid = request.session.get('userprofile_id', request.COOKIES.get('userprofile_id', None))
		print "get_user_profile 2: %s" % pid
	if pid:
		try:
			pid = int(pid)
			request.session['userprofile_id'] = pid
			print "get_user_profile 3: %s" % pid
			return UserProfile.objects.filter(fb_id=pid)[0]
		except IndexError:
			return None
	else:
		loggy = NamedTemporaryFile(suffix='.txt', prefix="userprofile_failure_", dir='/tmp/', delete=False)
		loggy.write("Failed to find a userprofile: %s, %s, %s" % (request.session.get('userprofile_id', None), request.COOKIES.get('userprofile_id', None), pid))
		loggy.close()


def new_user_profile(uid, first_name, last_name, name, profile_url, token, email):
	"""
		Convenience function.
	"""
	userprofile = UserProfile(fb_id=uid, fb_fname=first_name, fb_lname=last_name, fb_name=name, fb_url=profile_url, token=token, email=email)
	userprofile.save()
	return userprofile


def set_activity(userprofile=None, fb_id=None, metadata=None):
	"""
		Convenience function.
	"""
	a = Activity(	user=userprofile, 
					atype=constants.ACTIVITY_TYPES[8][0],
					metadata=simplejson.dumps(metadata),
					foreign_type=constants.MODEL_TYPES[4][0],
					foreign_id=fb_id
	)
	a.save()


class UserProfile(models.Model):
	"""
		We are using Facebook for user auth.  But we should keep a local cache of some of the information.
		System is id 1 fb_id 1, and we reserved through user 20
	"""
	fb_id = models.CharField(max_length=64, unique=True)
	fb_fname = models.CharField(max_length=64)
	fb_lname = models.CharField(max_length=64)
	fb_name = models.CharField(max_length=132)
	fb_url = models.CharField(max_length=1024, null=True)
	token = models.CharField(max_length=256, null=True)
	email = models.CharField(max_length=256, null=True)

	def get_journal_template(self, template):
		"""
			This is a convenience function: select a (the) journal template for a new journal.
		"""
		return JournalTemplate.objects.filter(pk=template)[0]

	def get_journal(self, journal_id):
		"""
			Convenience func.
		"""
		if self.fb_id in settings.FB_ADMINS or settings.INSECURE_APP:
			return Journal.objects.filter(pk=journal_id)[0]
		else:
			return self.journal_set.filter(pk=journal_id)[0]

	def new_journal(self, title, journal_template):
		"""
			Make a user journal.
		"""
		page_count = journal_template.page_count

		j = Journal(user=self, title=title, status=constants.JOURNAL_STATUSES[0][0], page_count=page_count) # status=active
		j.save()
		template_pages = journal_template.get_pages()
		# associate the pages
		for i in range(0, page_count):
			page_template = template_pages[i].page_template
			page_style = template_pages[i].page_style
			p = j.make_page(i + 1, page_template, page_style)
		return j

	def new_order(self, quantity, product_id, shipping_dict):
		pass

	def set_latest_order_status(self, status=None, ccauth=None, notes=None, unitprice=None, shippingprice=None, tax=None, coupon_id=None):
		"""
			Change an order status.  Use latest for this user.
		"""
		order = self.order_set.all().order_by('-created')[0]
		order.status = status
		order.ccauth = ccauth
		order.notes = notes
		order.save()
		return order


class Product(models.Model):
	"""
		What we sell.
	"""
	name = models.CharField(max_length=128)
	price = models.DecimalField(max_digits=6, decimal_places=2)
	line_description = models.CharField(max_length=1024, null=True)
	full_description = models.CharField(max_length=1024, null=True)


class Shipping(models.Model):
	"""
		Shipping information.  Duplicates allowed.  Might fix this later.
	"""
	firstname = models.CharField(max_length=64)
	middlename = models.CharField(max_length=64, null=True)
	lastname = models.CharField(max_length=64)
	addr1 = models.CharField(max_length=128)
	addr2 = models.CharField(max_length=128, null=True)
	city = models.CharField(max_length=128)
	state = models.CharField(max_length=128)
	zip = models.CharField(max_length=128)
	country = models.CharField(max_length=128)
	telephone = models.CharField(max_length=64)


class Coupon(models.Model):
	"""
		A price discount.  Ctypes include:
		   p: percent of book price after discount (that is, .75 means, 25 pct off) (0, 1) where 0 and 1 are BOTH a full discount to 0
		   d: dollars of price of book
		   po: percent, as p, but applied to entire order
		   do: dollars off order
	"""
	ctype = models.CharField(max_length=4)
	amount = models.DecimalField(max_digits=6, decimal_places=2)
	code = models.CharField(max_length=64)

	def calculate(self, quantity, unit_price, shipping, tax):
		"""
			Apply our amount to the existing order and return translated values.
		"""
		# FIXME, TODO: we're only going to deal with some specific cases here
		if self.ctype == 'po':
			if self.amount == Decimal("1.0") or self.amount == Decimal("0"):
				return (Decimal("0"), Decimal("0"), Decimal("0"))
			else:
				subtotal = quantity * unit_price
				return (Decimal(subtotal * self.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 
					Decimal(shipping * self.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 
					Decimal(tax * self.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
		elif self.ctype == 'd':
			unit_price = unit_price - self.amount
			subtotal = quantity * unit_price
			if tax > 0:
				tax = subtotal * settings.MA_TAX
			return (Decimal(subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
				shipping,
				Decimal(tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
		else:
			raise Exception('Unimplemented coupon option: %s' % self.ctype)


class Order(models.Model):
	"""
		An order of a product by a user.
	"""
	# important: we don't delete products, shipping or userprofiles (even if we might remove data associated with them)
	user = models.ForeignKey(UserProfile)
	product = models.ForeignKey(Product)
	shipping = models.ForeignKey(Shipping)
	journal_id = models.IntegerField()
	quantity = models.IntegerField()
	created = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=64, choices=constants.ORDER_STATUSES)
	ccauth = models.CharField(max_length=128, null=True)
	notes = models.CharField(max_length=1024, null=True)
	unitprice = models.DecimalField(max_digits=6, decimal_places=2, null=True)
	shippingprice = models.DecimalField(max_digits=6, decimal_places=2, null=True)
	tax = models.DecimalField(max_digits=6, decimal_places=2, null=True)
	coupon_id = models.IntegerField(null=True)


class Unsubscriber(models.Model):
	"""
		Trivial: list of emails we won't send to.
	"""
	email = models.CharField(max_length=128, unique=True)


class Journal(models.Model):
	"""
		Journals are (mostly) immutable -- never updated.  They are created when a permanence event happens, never otherwise.
	"""
	user = models.ForeignKey(UserProfile)
	created = models.DateTimeField(auto_now_add=True)
	title = models.CharField(max_length=1024)
	subtitle = models.CharField(max_length=1024, null=True)
	status = models.CharField(max_length=64, choices=constants.JOURNAL_STATUSES)
	page_count = models.IntegerField()
	date_range_start = models.DateTimeField(null=True)
	date_range_end = models.DateTimeField(null=True)

	def make_page(self, page_number, page_template, page_style):
		"""
			Create a page for this journal.
		"""
		p = JournalPage(journal=self, page_template=page_template, page_style=page_style, page_number=page_number)
		p.save()
		return p

	def get_pages(self):
		"""
			Convenience function: get ordered pages for a journal.
		"""
		return self.journalpage_set.all().order_by('page_number')

	def get_page(self, page_number):
		"""
			Get a particular page.
		"""
		return self.journalpage_set.filter(page_number=page_number)[0]

	def get_popular_photos(self):
		"""
			Popular ordering.
		"""
		return self.get_photos().order_by("-score")

	def get_photos(self):
		"""
			Get all the photos for this journal.
		"""
		return JournalPhoto.objects.filter(journal_page__journal__pk=self.id)

	def get_subtitle(self):
		"""
			Just a model abstraction function.
		"""
		return self.subtitle

	def get_title(self):
		"""
			Specialized: try our local title, then the itembased title.
		"""
		if self.title and self.title != 'My new journal':
			return self.title
		else:
			t = self.get_itembased_title()
			self.title = t
			self.save()
			return t

	def get_itembased_title(self):
		"""
			Get the title set in a particular item in the journal (hacky: based on the static title type)
		"""
		try:
			return self.journalpage_set.filter(page_number=1).get().get_journalitem_at(0, 1).journalmessage.message
		except:
			return 'My JotJournal'

	def set_itembased_title(self, title, subtitle):
		"""
			Sets the title page item text.
		"""
		try:
			i = self.journalpage_set.filter(page_number=1).get().get_journalitem_at(0, 1).journalmessage
			if not title:
				title = ''
			if not subtitle:
				subtitle = ''
			i.message = format_title(title, subtitle)
			i.save()
		except:
			raise Exception("Couldn't find any itembased title: %s" % self.id)

	def get_order(self):
		"""
			This is more awkward than you'd hope it would be.  Maybe I should have made journal_id a foreign key in orders.
		"""
		return self.user.order_set.filter(journal_id=self.id).order_by('-created')[0]

	def get_shipping(self):
		"""
			Helper function, sort of trivial.
		"""
		return self.get_order().shipping

	def get_date_range_as_pretty_string(self):
		"""
			MON YR to MON YR
		"""
		start = self.date_range_start
		start = "%s %d, %s" % (start.strftime('%B'), int(start.strftime('%d')), start.strftime('%Y'))
		end = self.date_range_end
		end = "%s %d, %s" % (end.strftime('%B'), int(end.strftime('%d')), end.strftime('%Y'))
		return "%s to %s" % (start, end)

	def set_meta(self, title, earliest, latest):
		"""
			Title, journal covers which dates.
		"""
		self.title = title
		self.date_range_start = datetime.strptime(earliest, '%Y-%m-%d %H:%M:%S')
		self.date_range_end = datetime.strptime(latest, '%Y-%m-%d %H:%M:%S')
		self.save()

	def set_subtitle(self, subtitle):
		"""
			Subtitle setter with default.
		"""
		if not subtitle:
			subtitle = self.get_date_range_as_pretty_string()
		self.subtitle = subtitle
		self.save()


class JournalTemplate(Journal):
	"""
		This is a journal, but meant as a template for other journals.  Basically a journal template,
		with pages, templates, styles but no items.  JournalTemplate Journals will belong to user 'system' (1).
	"""
	template_title = models.CharField(max_length=128)


# multi-table inheritance (so pagetemplate can easily have foreignkeys pointed at it)
class PageTemplate(models.Model):
	"""
		Page template: a description of the layout mechanics for this page -- gives placement of items [ex. gives number
		and orientation of images on page]
	"""
	aspect_base_x = models.DecimalField(max_digits=9,decimal_places=7) # inches (8 for journal 1)
	aspect_base_y = models.DecimalField(max_digits=9,decimal_places=7) # inches (8 for journal 1)
	# In _percent of page size_: the safe-printing page margin, 0.0-1.0
	outer_margin_top = models.DecimalField(max_digits=9,decimal_places=7)
	outer_margin_right = models.DecimalField(max_digits=9,decimal_places=7)
	outer_margin_bottom = models.DecimalField(max_digits=9,decimal_places=7)
	outer_margin_left = models.DecimalField(max_digits=9,decimal_places=7)
	# the inner margin
	inner_margin_width = models.DecimalField(max_digits=9,decimal_places=7)
	inner_margin_height = models.DecimalField(max_digits=9,decimal_places=7)
	#
	total_photos = models.IntegerField()
	total_texts = models.IntegerField()
	#
	description = models.CharField(max_length=1024)

	def get_quadrants(self):
		"""
			Convenience function -- get quadrants for this page template.
		"""
		return [pt.quadrant for pt in self.positionalthing_set.all()]


class PageStyle(models.Model):
	"""
		Page styles: a description of the color, art for this page
	"""
	background_image = models.CharField(max_length=1024, null=True)
	background_color = models.CharField(max_length=32, null=True)
	text_color = models.CharField(max_length=32, null=True)
	text_font = models.CharField(max_length=32, null=True)
	text_size = models.CharField(max_length=32, null=True)
	box_color = models.CharField(max_length=32, null=True)
	# this is in percent
	text_box_margin = models.DecimalField(max_digits=9,decimal_places=7,null=True)


class JournalPage(models.Model):
	"""
		A page in a journal.  This is where the action happens.
	"""
	journal = models.ForeignKey(Journal)
	page_template = models.ForeignKey(PageTemplate)
	page_style = models.ForeignKey(PageStyle)
	page_number = models.IntegerField()

	class Meta:
		ordering = ["page_number"]

	def get_quadrants(self):
		"""
			Convenience.
		"""
		return self.page_template.get_quadrants()

	def get_journalitems(self):
		"""
			Convenience.
		"""
		return self.journalitem_set.all()

	def get_grid_dimensions(self):
		"""
			Really for gravity style templates.
		"""
		if self.page_template.pagetemplategravity:
			return (self.page_template.pagetemplategravity.grid_width, self.page_template.pagetemplategravity.grid_height)
		else:
			return (0, 0) # molds aren't on a grid in this system

	def positional_thing_at(self, gridx, gridy):
		"""
			Find a fillable thing at a grid position.
		"""
		things = self.get_quadrants()
		if things:
			for thing in things:
				if thing.coordinate_x == gridx and thing.coordinate_y == gridy:
					return thing
		return None

	def get_journalitem_at(self, gridx, gridy):
		"""
			Does this page have an associated item that is associated with a positional thing at this location.  (Quadrant API only --
			senseless function to call on a moldy template)
		"""
		items = self.get_journalitems()
		if items:
			for item in items:
				try:
					q = item.positional_thing.quadrant
					if q.coordinate_x == gridx and q.coordinate_y == gridy:
						return item
				except:
					# nothing found here or not a quadranty template
					traceback.print_exc()
					pass
		return None

	def add_item(self, item_type='photo', positional_thing=None, fb_id=None, fb_url=None, item_date=None, fb_item_type=None, event_id=0,
					score=0, message=None, length_chars=0, dimension_x=0, dimension_y=0, fb_picture=None, fb_source=None):
		"""
			Create a new JournalItem.
		"""
		if item_type == 'text':
			t = JournalMessage(journal_page=self, positional_thing=positional_thing, fb_id=fb_id, fb_url=fb_url, item_date=item_date, item_visibility_state='visible',
								item_type=fb_item_type, event_id=event_id, score=score, length_chars=length_chars, message=message)
		else:
			t = JournalPhoto(journal_page=self, positional_thing=positional_thing, fb_id=fb_id, fb_url=fb_url, item_date=item_date, item_visibility_state='visible',
								item_type=fb_item_type, event_id=event_id, score=score, dimension_x=dimension_x, dimension_y=dimension_y, fb_picture=fb_picture, fb_source=fb_source)
		t.save()
		return t


class PageTemplateGravity(PageTemplate):
	"""
		This is a gravity-style template.  It lets you specify the quadrants of a page and the centering algorithm, which 
		tells you how to place items in the quadrants.
	"""
	# how many grid units across the page
	grid_width = models.IntegerField()
	# how many grid units down the page
	grid_height = models.IntegerField()
	# NOTE: grid_width * grid_height gives the number of Quadrants on this page (close: some quadrants can have a width or height > 1)


class Gravity(models.Model):
	"""
		This specifies the gravity of a quadrant on a gravity-style template page.  Could be an X gravity or a Y gravity.
	"""
	orientation = models.CharField(max_length=32, choices=constants.GRAVITIES)
	metadata = models.CharField(max_length=1024) # any special params, padding, adjustment, a JSON dict


# multi-table inheritance
class PositionalThing(models.Model):
	"""
		The kind of thing that gives an item's position on a page template.  Quadrant or Mold.
	"""
	page_template = models.ForeignKey(PageTemplate)


class Quadrant(PositionalThing):
	"""
		On a gravity style page template, each grid unit of the page is a quadrant.  Each quadrant can have its own
		item gravity, which specifies how each item drifts inside its container.
	"""
	# where on this page is this quadrant
	coordinate_x = models.IntegerField()
	units_x = models.IntegerField(default=1) # number of grid units taken by this quadrant in the x-dimension
	coordinate_y = models.IntegerField()
	units_y = models.IntegerField(default=1) # ditto, y
	# how are inner items aligned horizontally
	grid_gravity_x = models.ForeignKey(Gravity, related_name='grid_gravity_x')
	# ... vertically
	grid_gravity_y = models.ForeignKey(Gravity, related_name='grid_gravity_y')
	# overrides page settings (in page, boxcolor is used for all quadrants/molds)
	background_color = models.CharField(max_length=32, null=True)
	text_color = models.CharField(max_length=32, null=True)
	# content type lets you say nothing (anything can go here), "message" (only a message can go here), "photo" (only a photo can go here),
	# "popular:photo" (only a popular photo can go here, descending popularity going forward in the book), "popular:caption" -- the caption of a popular_photo, "popular:message" (only a popular message),
	# "static:..." (to create a page with a static resource) ??? perhaps just page sized single images
	content_type = models.CharField(max_length=32, null=True)

	class Meta:
		ordering = ["coordinate_x", "coordinate_y"]


################################# Above: stuff that's static-ish, system inserted into dbs, etc
################################# Below: all dynamic -- items, activites, etc
################################# Below: exception is pagetemplateposition and mold, which we're not using yet


# multi-table inheritance
class JournalItem(models.Model):
	"""
		The base item.  Subclasses are JournalPhoto and JournalMessage.
		These items are associated with JournalPages (because every new journal gets a set of new pages)
		*and* positional things (because PTs are associated with the template, and are sparse, and give the location
		of the item).  It could be a quadrant.  Equivalently, it could be associated with a Mold.  So that's why both
		Mold and Quadrant extend PositionalThing.
		
				I	-	-	-	-	-	-	-	-	|
				I	-	-	-	-	-	-	-	-	|
				I	-	-	-	-	-	-	-	-	|
				|									|
				|									|
		J	-	P	-	-	-	-	-	-	|		|
			-	P	-	-	-	-	|		|		|
			-	P	-	-	|		|		|		|
							PT3		PT2		PT1	-	Q/M=PT
							|		|		|	-	Q/M=PT
		J	-	P	-	-	|		|		|	-	Q/M=PT
		|	-	P	-	-	-	-	|		|		|
		|	-	P	-	-	-	-	-	-	|		|
				|									|
				I	-	-	-	-	-	-	-	-	|
				I	-	-	-	-	-	-	-	-	|
				I	-	-	-	-	-	-	-	-	|

	"""
	journal_page = models.ForeignKey(JournalPage)
	positional_thing = models.ForeignKey(PositionalThing)
	fb_id = models.CharField(max_length=64)
	fb_url = models.CharField(max_length=1024)
	item_date = models.DateTimeField()
	item_visibility_state = models.CharField(max_length=32, choices=constants.ITEM_VISIBILITY_STATES)
	# the facebook item type
	item_type = models.CharField(max_length=32, choices=constants.FB_ITEM_TYPES) # photo, caption, wall, status
	# the event_id lets you group journalitems together -- arbitrary integer, though you should make them go from 0-n as event date approaches the present
	event_id = models.IntegerField()
	# a calculated score for an item giving it an overall weight for display purposes
	score = models.IntegerField()

	def is_photo(self):
		"""
			Convenience.
		"""
		return self.item_type == 'photo'

	def is_text(self):
		"""
			Convenience.
		"""
		return self.item_type != 'photo'


class JournalPhoto(JournalItem):
	"""
		A photo on a page in a journal.
	"""
	dimension_x = models.IntegerField() # pixels
	dimension_y = models.IntegerField() # pixels
	fb_picture = models.CharField(max_length=1024)
	fb_source = models.CharField(max_length=1024)


class JournalMessage(JournalItem):
	"""
		A message on a page in a journal.
	"""
	length_chars = models.IntegerField()
	message = models.CharField(max_length=1024)


class Activity(models.Model):
	"""
		Most date-based things that happen in the system will go into this single table.  This prevents us from worrying about
		putting times on everything else.
	"""
	user = models.ForeignKey(UserProfile)
	atype = models.CharField(max_length=100, choices=constants.ACTIVITY_TYPES)
	occurred = models.DateTimeField(auto_now_add=True) #auto_now=False
	metadata = models.CharField(max_length=1024) # the item id acted on, etc, a JSON dict
	foreign_type = models.CharField(max_length=64, choices=constants.MODEL_TYPES) # Journal, UserProfile, etc
	foreign_id = models.IntegerField() # the ID this activity is for, in the listed foreign_type

	class Meta:
		ordering = ["-occurred"]


class PageTemplatePosition(PageTemplate):
	"""
		This is a position based template.  It lets you specify the positions of a list of typed-molds (photo- or message-) on a page.
	"""
	mold_count = models.IntegerField()


class Mold(PositionalThing):
	"""
		Positions are expressed as percentages to sidestep the question of pixels, points, and whatnot.  Positions expressed as an
		offset from the top left.  Width and height are also percentages.  All percentages expressed as percent of page width (for
		mold width, mold x position offset) and height (for mold height, mold y position offset).
	"""
	offset_top = models.DecimalField(max_digits=9, decimal_places=7) # 0.10
	offset_left = models.DecimalField(max_digits=9, decimal_places=7) # 0.10
	width = models.DecimalField(max_digits=9, decimal_places=7) # 0.50
	height = models.DecimalField(max_digits=9, decimal_places=7) # 0.35
	mtype = models.CharField(max_length=32, choices=constants.MOLD_TYPES)


