from django.conf import settings
from django.utils import simplejson

from decimal import *

import traceback
import pprint
import urllib2
import cStringIO
import Image

from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


# utility
def rgb_from_hex(hexstring):
	r = hexstring[1:3]
	g = hexstring[3:5]
	b = hexstring[5:7]
	return int(r, 16)/255.0, int(g, 16)/255.0, int(b, 16)/255.0


def format_title(title, subtitle):
	"""
		Silliness for the title page title.
	"""
	return "%s<br/><br/>%s" % (title, subtitle)


class DrawingContext(object):
	"""
		Handy place to store drawing state, such as containing document.
	"""
	def __init__(self):
		"""
			Initialize state variables.
		"""
		self.instructions = []


class Renderer(object):
	"""
		Base renderer.  Primarily responsible for generating the drawing instructions list.
		API is just init and then render()
		API for renderer is just get_drawing_instructions()
	"""
	def __init__(self, journal):
		"""
			Set a few elements of state.
		"""
		self.context = DrawingContext()
		self.journal = journal

	def journal1_cover(self):
		"""
			The cover for a particular journal template (1, 2).
		"""
		t = self.journal.get_title()
		d = self.journal.subtitle if self.journal.subtitle else ''

		titlepart = t.replace('<br/>', ' ')
		titlepart = titlepart.replace('JotJournal', '<font color="#93d86d"><b>JotJournal</b></font>')
		return {
			'page_number': 0,
			'page_width_inches': Decimal("8.5"),
			'page_height_inches': Decimal("8.5"),
			'background_color': '#ffffff',
			'text_box_margin': Decimal("0.0156250"),
			'layer0': [
				["drawRect", "cover_image", Decimal("1.0"), Decimal("1.0"), Decimal("0.0"), Decimal("0.0"), "center", "center", ""],
				["drawRect", "cover_center_text", Decimal("0.75"), Decimal("0.25"), Decimal("0.125"), Decimal("0.4"), "center", "center", ""],
				["drawRect", "cover_subtitle", Decimal("0.5"), Decimal("0.15"), Decimal("0.25"), Decimal("0.65"), "center", "center", ""]
			],
			'layer1': [
				["drawImageFloatingInRect", "cover_image", "cover_image_image", 1275, 1275, "https://myjotjournal.com/static/images/journal_images/new_front_cover.png"]
			],
			'layer2': [
				["drawText", "cover_center_text", "cover_title_centered_text", "#ffffff", "Helvetica", 42, titlepart, 'title'],
				["drawText", "cover_subtitle", "cover_subtitle_text", "#ffffff", "Helvetica", 20, d, 'title']
			]
		}

	def journal1_rear_cover(self):
		"""
			The rear cover for a particular journal template (1, 2)
		"""
		return {
			'page_number': -1,
			'page_width_inches': Decimal("8.5"),
			'page_height_inches': Decimal("8.5"),
			'background_color': '#ffffff',
			'text_box_margin': Decimal("0.0156250"),
			'layer0': [
				["drawRect", "cover_image", Decimal("1.0"), Decimal("1.0"), Decimal("0.0"), Decimal("0.0"), "center", "center", ""],
			],
			'layer1': [
				["drawImageFloatingInRect", "cover_image", "cover_image_image", 1275, 1275, "https://myjotjournal.com/static/images/journal_images/new_rear_cover.png"]
			],
			'layer2': [
			]
		}

	def journal_shipping_page(self):
		"""
			The order + shipping page for a journal (template neutral).
		"""
		try:
			shipping = self.journal.get_shipping()
			name = "%s %s %s" % (shipping.firstname, shipping.middlename, shipping.lastname)
			street = "%s" % shipping.addr1
			if shipping.addr2:
				street = "%s<br/>%s" % (street, shipping.addr2)
			city = shipping.city
			state = shipping.state
			zip = shipping.zip
			country = shipping.country
			telephone = shipping.telephone
		except IndexError:
			name = "Test"
			street = "Test"
			city = "Test"
			state = "Test"
			zip = "Testt"
			country = "Test"
			telephone = "Test"
		return {
			'page_number': -2,
			'page_width_inches': Decimal(8),
			'page_height_inches': Decimal(8),
			'background_color': '#ffffff',
			'text_box_margin': Decimal("0.0156250"),
			'layer0': [
				["drawRect", "from_top", Decimal("0.33"), Decimal("0.33"), Decimal("0.10"), Decimal("0.16"), "left", "top", ""],
				["drawRect", "to_top", Decimal("0.33"), Decimal("0.33"), Decimal("0.10"), Decimal("0.55"), "left", "top", ""],
				["drawRect", "from_bottom", Decimal("0.33"), Decimal("0.33"), Decimal("0.55"), Decimal("0.16"), "left", "top", ""],
				["drawRect", "to_bottom", Decimal("0.33"), Decimal("0.33"), Decimal("0.55"), Decimal("0.55"), "left", "top", ""],
			],
			'layer1': [
			],
			'layer2': [
				["drawText", "from_top", "from_top_text", "#000000", "Helvetica", 18, "FROM:<br/>JotJournal<br/>P.O. Box 224<br/>Scituate, MA 02066<br/><br/>Order #%s" % self.journal.id, 'address'],
				["drawText", "from_bottom", "from_bottom_text", "#000000", "Helvetica", 18, "FROM:<br/>JotJournal<br/>P.O. Box 224<br/>Scituate, MA 02066<br/><br/>Order #%s" % self.journal.id, 'address'],
				["drawText", "to_top", "to_top_text", "#000000", "Helvetica", 18, "TO:<br/>%s<br/>%s<br/>%s, %s %s<br/>%s" % (name, street, city, state, zip, country), 'address'],
				["drawText", "to_bottom", "to_bottom_text", "#000000", "Helvetica", 18, "TO:<br/>%s<br/>%s<br/>%s, %s %s<br/>%s" % (name, street, city, state, zip, country), 'address']
			]
		}

	def journal_final_page(self):
		"""
			The last journal page with copyright and order number.
		"""
		order_number = self.journal.id
		return {
			'page_number': 34,
			'page_width_inches': Decimal(8),
			'page_height_inches': Decimal(8),
			'background_color': '#ffffff',
			'text_box_margin': Decimal("0.0156250"),
			'layer0': [
				["drawRect", "final_page_text", Decimal("0.9"), Decimal("0.075"), Decimal("0.05"), Decimal("0.9"), "center", "center", ""]
			],
			'layer1': [
			],
			'layer2': [
				["drawText", "final_page_text", "final_page_text_text", "#000000", "Helvetica", 18, "Copyright &copy; 2010, 2011 myjotjournal.com. All rights reserved.  Order #%s." % order_number, 'order']
			]
		}

	def get_drawing_instructions(self, for_shipping=False):
		"""
			The API function called by subclasses.
			Outputs in layers.
			Typically, layer 0: quadrants, layer 1: images, layer 2: text

			Drawing instructions: (XXX FIXME TODO for now assuming quadrants)
				* drawRect: rectId, width, height, offsetx, offsety, gravityx, gravityy, boxcolor -- draws a rectangle of a given color ('' for transparent)
				  at the given offsets (in percent of page dimension, as with margins) with the given dimensions (again in  %)
				  rectId is assigned here and is the positionalthing id
				* drawText: rectId, myId, textcolor, fontfamily, fontsize, content, content_type --
				  rectId is a link to the rect that gives the offset and size of the text block area
				  gravity of the linked rectId here interpreted as a text alignment property -- whether to center the text, and vertically align it
				  in its quadrant
				* drawImageFloatingInRect: rectId, myId, imagewidth, imageheight, imageurl -- image width and height are in pixels, and are used to 
				  calculate an aspect ratio.  The image is then scaled down to float without clipping in the linked rect and gravities are used
				  as with text to determine how the image floats.
		"""
		i = self.context.instructions
		j = self.journal

		for page in j.get_pages():
			pdict = {
				'page_number': page.page_number,
				'page_width_inches': page.page_template.aspect_base_x,
				'page_height_inches': page.page_template.aspect_base_y,
				'background_color': page.page_style.background_color,
				'text_box_margin': page.page_style.text_box_margin,
				'layer0': [],
				'layer1': [],
				'layer2': []
			}

			pagestyle = page.page_style
			color_cache = {}

			dimx, dimy = page.get_grid_dimensions()
			# In _percent of page size_: the safe-printing page margin, 0.0-1.0
			outer_margin_top = page.page_template.outer_margin_top
			outer_margin_right = page.page_template.outer_margin_right
			outer_margin_bottom = page.page_template.outer_margin_bottom
			outer_margin_left = page.page_template.outer_margin_left
			# "streets"
			inner_margin_width = page.page_template.inner_margin_width
			inner_margin_height = page.page_template.inner_margin_height

			# now we can calculate the unit percentage of each kind of thing
			percent_width_after_outer_margins = Decimal(1) - (outer_margin_right + outer_margin_left)
			percent_height_after_outer_margins = Decimal(1) - (outer_margin_top + outer_margin_bottom)
			streets_take_up_width = Decimal(dimx - 1) * inner_margin_width
			streets_take_up_height = Decimal(dimy - 1) * inner_margin_height
			all_units_width = percent_width_after_outer_margins - streets_take_up_width
			all_units_height = percent_height_after_outer_margins - streets_take_up_height
			unit_width = all_units_width / Decimal(dimx)
			unit_height = all_units_height / Decimal(dimy)

			layer0 = pdict['layer0']
			layer1 = pdict['layer1']
			layer2 = pdict['layer2']

			# XXX FIXME TODO only quadrant style implemented:
			content_types = {}
			quads = page.get_quadrants()
			for quad in quads:
				coordx =  quad.coordinate_x
				coordy = quad.coordinate_y
				unitx = quad.units_x
				unity = quad.units_y
				gravityx = quad.grid_gravity_x
				gravityy = quad.grid_gravity_y

				width = (unitx * unit_width) + (Decimal(unitx - 1) * inner_margin_width)
				height = (unity * unit_height) + (Decimal(unity - 1) * inner_margin_height)
				offsetx = outer_margin_left + (coordx * (unit_width + inner_margin_width))
				offsety = outer_margin_top + (coordy * (unit_height + inner_margin_height))
				ggravityx = gravityx.orientation
				ggravityy = gravityy.orientation
				boxcolor = quad.background_color or pagestyle.box_color
				color_cache[quad.positionalthing_ptr_id] = quad.text_color or None
				content_types[quad.positionalthing_ptr_id] = quad.content_type

				draw = ["drawRect", quad.positionalthing_ptr_id, width, height, offsetx, offsety, ggravityx, ggravityy, boxcolor]
				layer0.append(draw)

			items = page.get_journalitems()
			for item in items:
				if item.is_photo():
					imagewidth = item.journalphoto.dimension_x
					imageheight = item.journalphoto.dimension_y
					imageurl = item.journalphoto.fb_source

					# XXX FIXME TODO only quadrant style for now
					draw = ["drawImageFloatingInRect", item.positional_thing.id, item.id, imagewidth, imageheight, imageurl]
					layer1.append(draw)
				else:
					textcolor = color_cache[item.positional_thing.id] or page.page_style.text_color
					fontfamily = page.page_style.text_font
					fontsize = page.page_style.text_size
					content = item.journalmessage.message

					draw = ["drawText", item.positional_thing.id, item.id, textcolor, fontfamily, fontsize, content, item.item_type]
					if content_types[item.positional_thing.id] == "popular:message" or item.item_type == 'status':
						x = "%s %d, %s" % (item.item_date.strftime('%B')[0:3], int(item.item_date.strftime('%d')), item.item_date.strftime('%Y'))
						draw_2 = ["drawTextFragment", item.positional_thing.id, "%s_d" % item.id, textcolor, fontfamily, fontsize, x, 'fragment']
						layer2.append(draw_2)
					layer2.append(draw)

			i.append(pdict)

		# insert the cover XXX SPECIFIC TO JOURNAL TYPE 1, HACK HERE
		i.insert(0, self.journal1_cover())
		if for_shipping:
			i.insert(0, self.journal1_rear_cover())
			i.insert(0, self.journal_shipping_page())
			i.append(self.journal_final_page())

		return i


def xspec_to_align(spec):
	if spec == 'lefttop':
		spec = 'left'
	elif spec == 'rightbottom':
		spec = 'right'
	return spec


def yspec_to_align(spec):
	if spec == 'lefttop':
		spec = 'top'
	elif spec == 'rightbottom':
		spec = 'bottom'
	elif spec == 'center':
		spec = 'middle'
	return spec


RESET_CSS = "" # XXX TODO WRITEME
class CSSRenderer(Renderer):
	"""
		The JSONRenderer just outputs commands to make divs -- here is where we say what those boxes all look like.
	"""
	def render(self):
		"""
			The money: a css stylesheet.
		"""
		output = "%s\n" % RESET_CSS
		instrux = self.get_drawing_instructions()

		output += "\n\n.page { overflow:hidden; position:relative; z-index:1; }\n"
		output += ".quadrant { overflow:hidden; position:absolute; z-index:2; }\n"
		output += ".photo { position:relative; z-index:3; }\n"
		output += ".message { overflow:hidden; position:relative; z-index:4; padding:%s%%; }\n" % (instrux[0]['text_box_margin'] * Decimal(100))
		output += ".message_fragment { overflow:hidden; position:absolute; z-index:4; }\n"
		output += ".idiocy { width:100%; height:100%; }\n"
		#output += ".idiocy td { padding:%s%% }\n\n" % (instrux[0]['text_box_margin'] * Decimal(100))

		p_boxcolor = ''
		quad_cache = {}
		for page in instrux:
			page_number = page['page_number']
			layer0 = page['layer0']
			layer1 = page['layer1']
			layer2 = page['layer2']
			for l in layer0:
				command, id, width, height, offsetx, offsety, ggravityx, ggravityy, boxcolor = l
				quad_cache[id] = [ width, height, ggravityx, ggravityy ]

				# quadrants on a page have a default background color
				if not boxcolor:
					boxcolor = p_boxcolor

				# ggravityx of topleft means text-align left, etc -- this takes care of text and image horiz centering
				ggravityx = xspec_to_align(ggravityx)

				output += "#quadrant_%s { width:%s%%; height:%s%%; left:%s%%; top:%s%%; text-align:%s; background-color: %s }\n" % \
					(id, width*Decimal(100), height*Decimal(100), offsetx*Decimal(100), offsety*Decimal(100), ggravityx, boxcolor)

				# ggravityy of topleft means vertical-align top, etc -- this takes care of text vert centering
				ggravityy = yspec_to_align(ggravityy)

				output += "#quadrant_inner_%s { vertical-align:%s; text-align:%s; }" % \
					(id, ggravityy, ggravityx)

			for l in layer1:
				command, rectId, myId, imagewidth, imageheight, imageurl = l
				# XXX EXPERIMENTAL
				qw, qh, _, _ = quad_cache[rectId]
				if qw/qh <= Decimal(imagewidth)/Decimal(imageheight):
					# have to get fancy with the top property:
					# XXX FIXME TODO: not all gravities mapped (topleft, etc) THIS ASSUMES VERTICAL CENTERING OF IMAGE
					top = (qh/qw - Decimal(imageheight)/Decimal(imagewidth)) * Decimal(100) / (Decimal(2) * (qh/qw))
					frag = "position:relative;top:%s%%;width:100%%" % top
				else:
					frag = "height:100%"
				output += "#photo_%s { %s; }\n" % (myId, frag)

			for l in layer2:
				command, rectId, myId, textcolor, fontfamily, fontsize, content, content_type = l
				# this is a size neutral css, so have to ignore font-size:
				_, _, xspec, yspec = quad_cache[rectId]
				## hack for statuses: left aligned XXX FIXME TODO
				hack_frag = ''
				if content_type == 'status':
					hack_frag = ' text-align: left;'
				output += "#message_%s { color:%s; font-family:%s;%s }\n" % \
					(myId, textcolor, fontfamily, hack_frag)
				if command == 'drawTextFragment':
					xspec = xspec_to_align(xspec)
					yspec = yspec_to_align(yspec)
					# this output is a little hack XXX FIXME TODO make it have its own gravity
					output += "#message_%s { right:2px; bottom:2px; }\n" % (myId)

		return output


class JSONRenderer(Renderer):
	"""
		The interesting thing about this renderer is that the actual drawing commands are implemented on the client side.  So the
		renderer outputs code-like fragments instead of calling local functions to convert to HTML.

		Outputs structure like this:
		output = json({
			pages:
			[
				{
					page_number: 1,
					layer0:
					[
						[drawRect, rectId],
						[drawImageFloatingInRect, rectId, myId, url],
						[drawText, rectId, myId, content, contentType],
						[drawTextFragment, rectId, myId, content, contentType],
						...
					],
					layer1:
					[
						...
					]
					...
				},
				...
			]
		})

		Typically, layer 0: quadrants, layer 1: images, layer 2: text
	"""
	def render(self):
		"""
			The API function.
		"""
		output = { 'pages': [] }
		instrux = self.get_drawing_instructions()
		for page in instrux:
			page_number = page['page_number']
			pdict = {
				'page_number': page_number,
				'layer0': [],
				'layer1': [],
				'layer2': []
			}
			layer0 = page['layer0']
			layer1 = page['layer1']
			layer2 = page['layer2']
			for l in layer0:
				command, id, width, height, offsetx, offsety, ggravityx, ggravityy, boxcolor = l
				pdict['layer0'].append([ 'drawRect', id ])

			for l in layer1:
				command, rectId, myId, imagewidth, imageheight, imageurl = l
				pdict['layer1'].append([ 'drawImageFloatingInRect', rectId, myId, imageurl ])

			for l in layer2:
				command, rectId, myId, textcolor, fontfamily, fontsize, content, content_type = l
				pdict['layer2'].append([ command, rectId, myId, content ])

			output['pages'].append(pdict)

		#pprint.PrettyPrinter().pprint(output)
		return simplejson.dumps(output)


class PDFRenderer(Renderer):
	"""
		Outputs a PDF object of the rendered journal.
	"""
	def render(self, io_object, for_shipping=False):
		"""
			The API function.
		"""
		instrux = self.get_drawing_instructions(for_shipping=for_shipping)
		ppi = 72.0

		mold_geometry = {}
		mold_gravity = {}

		points_w = ppi * float(instrux[0]['page_width_inches'])
		points_h = ppi * float(instrux[0]['page_height_inches'])
		c = canvas.Canvas(io_object, pagesize=(points_w, points_h))
		# this is a little hacky, since we're operating the margin for both h and w on points_w
		text_box_margin_pt = points_w * float(instrux[0]['text_box_margin'])

		for page in instrux:
			# set the page size manually
			points_w = ppi * float(page['page_width_inches'])
			points_h = ppi * float(page['page_height_inches'])
			c.setPageSize([points_w, points_h])

			page_number = page['page_number']
			layer0 = page['layer0']
			layer1 = page['layer1']
			layer2 = page['layer2']
			for l in layer0:
				command, id, width, height, offsetx, offsety, ggravityx, ggravityy, boxcolor = l
				mold_geometry[id] = [offsetx, offsety, width, height]
				mold_gravity[id] = [ggravityx, ggravityy]

				if boxcolor:
					red, green, blue = rgb_from_hex(boxcolor)

					x = float(offsetx) * points_w
					y = (1.0 - (float(offsety) + float(height))) * points_h
					width = float(width) * points_w
					height = float(height) * points_h

					c.setStrokeColorRGB(red, green, blue)
					c.setFillColorRGB(red, green, blue)
					c.rect(x, y, width, height, stroke=1, fill=1)

			for l in layer1:
				command, rectId, myId, imagewidth, imageheight, imageurl = l
				# grab the image (sync is fine for the moment...)
				try:
					f = cStringIO.StringIO(urllib2.urlopen(imageurl).read())
				except urllib2.HTTPError:
					# 404, skip this image
					continue

				# to PIL:
				i = Image.open(f)

				# draw:
				# XXX note: dpi appears to be normalized by the pdf renderer to 1 point = 1 pixel (72 dpi) so 
				# this is informational only (rather than having to normalize width and height of drawing)
				try:
					dpi = i.info["dpi"] or 72
				except KeyError:
					dpi = 72
				mold_offsetx, mold_offsety, mold_width, mold_height = mold_geometry[rectId]
				x = float(mold_offsetx) * points_w
				y = (1.0 - (float(mold_offsety) + float(mold_height))) * points_h

				# math
				image_aspect_ratio = float(imagewidth) / float(imageheight)
				mold_aspect_ratio = float(mold_width) / float(mold_height)
				centering_offset_x = 0.0
				centering_offset_y = 0.0

				mw = points_w * float(mold_width)
				mh = points_h * float(mold_height)

				if image_aspect_ratio > mold_aspect_ratio:
					image_points_x = mw
					image_points_y = image_points_x / image_aspect_ratio
					# XXX FIXME TODO: not all gravities mapped (topleft, etc) THIS ASSUMES VERTICAL CENTERING OF IMAGE
					centering_offset_y = (mh - image_points_y)/2.0
				elif mold_aspect_ratio > image_aspect_ratio:
					image_points_y = mh
					image_points_x = image_points_y * image_aspect_ratio
					# XXX FIXME TODO: not all gravities mapped (topleft, etc) THIS ASSUMES VERTICAL CENTERING OF IMAGE
					centering_offset_x = (mw - image_points_x)/2.0
				else: # ==
					image_points_x = mw
					image_points_y = mh

				#print "image %s: dpi: %s, width: %s, height: %s, centering_offset_x: %s, centering_offset_y: %s, image_points_x: %s, image_points_y: %s" % \
				#	(imageurl, dpi, imagewidth, imageheight, centering_offset_x, centering_offset_y, image_points_x, image_points_y)
				c.drawInlineImage(i, x + centering_offset_x, y + centering_offset_y, width=image_points_x, height=image_points_y)

			stylesheet = getSampleStyleSheet()
			normal_style = stylesheet['BodyText']

			def get_text(_content, _alignment, _fontfamily, _fontsize, _textcolor, _normal_style):
				para = "<para alignment='%s' fontName='%s' fontSize='%s' textColor='%s' leading='%s'>" % (_alignment, _fontfamily, _fontsize, _textcolor, int(float(_fontsize) * 1.20))
				endpara = '</para>'
				_content = para + _content + endpara
				p = Paragraph(_content, _normal_style)
				return p

			for l in layer2:
				command, rectId, myId, textcolor, fontfamily, fontsize, content, contentType = l

				alignment = mold_gravity[rectId][0]
				## hack: statuses are left aligned XXX FIXME TODO
				if contentType == 'status':
					alignment = 'left'
				else:
					alignment = xspec_to_align(alignment)
				if command == 'drawTextFragment':
					## XXX FIXME TODO this is a hack that treats all text fragments as bottom right dates
					alignment = 'right'
				# horiz alignment here ***************************************************************************************
				p = get_text(content, alignment, fontfamily, fontsize, textcolor, normal_style)

				mold_offsetx, mold_offsety, mold_width, mold_height = mold_geometry[rectId]
				# translate all to points now:
				mold_offsetx = float(mold_offsetx) * points_w + text_box_margin_pt
				mold_offsety = float(mold_offsety) * points_h + text_box_margin_pt
				mold_width = float(mold_width) * points_w - 2*text_box_margin_pt
				mold_height = float(mold_height) * points_h - 2*text_box_margin_pt

				actual_width, actual_height = p.wrap(mold_width, mold_height)
				#print "ACTUAL WIDTH/HEIGHT, DESIRED WIDTH/HEIGHT: %s/%s, %s/%s" % (actual_width, actual_height, mold_width, mold_height)
				if actual_width > mold_width or actual_height > mold_height:
					print "Warning!  Text %s took up too much space for mold %s on page %s (%s, %s vs %s, %s)" % (myId, rectId, page, actual_width, actual_height, mold_width, mold_height)
					p = get_text(content, alignment, fontfamily, int((float(fontsize)*2.0)/3.0), textcolor, normal_style)
					actual_width, actual_height = p.wrap(mold_width, mold_height)
					print "ADJUSTED!  Text %s took up space for mold %s on page %s (%s, %s vs %s, %s)" % (myId, rectId, page, actual_width, actual_height, mold_width, mold_height)

				# vert alignment here ***************************************************************************************
				# XXX FIXME TODO: not all gravities mapped (topleft, etc) -- THIS ASSUMES VERTICAL CENTERING OF TEXT
				if command == 'drawText':
					if mold_gravity[rectId][1] == 'center':
						if actual_height < mold_height:
							top_offset = (mold_height - actual_height) / 2.0
						else:
							top_offset = 0
						calc_offset_top = points_h - (mold_offsety + top_offset + actual_height) # vertical centering
					elif mold_gravity[rectId][1] == 'top':
						calc_offset_top = points_h - (mold_offsety + actual_height)
				elif command == 'drawTextFragment':
					## XXX FIXME TODO this is a hack that treats all text fragments as bottom right dates
					calc_offset_top = points_h - (mold_offsety + mold_height) - (actual_height - 17.0)

				p.drawOn(c, mold_offsetx, calc_offset_top)

			c.showPage()

		c.save()
