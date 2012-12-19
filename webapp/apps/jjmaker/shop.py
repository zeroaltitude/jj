from django.conf import settings
from django.utils import simplejson

from payflowpro.classes import CreditCard, Amount, Address
from payflowpro.client import PayflowProClient

import constants, traceback

from jotjournal_utils import get_ticket
from jjmaker.models import create_shipping, create_order, get_coupon

from decimal import *


def validate_totals(state, shipping, tax, amt, quantity, coupon):
	"""
		Prices are calculated both client-side and server side.  They should match.
	"""
	SHIPPING = Decimal("5")
	INTERNATIONAL_SHIPPING = Decimal("16.35")
	if shipping > SHIPPING: # HACK: idea is even discounted international shipping is more $$ than US, this could go horribly wrong on discounts of > 66%
		SHIPPING = INTERNATIONAL_SHIPPING
	UNIT_PRICE = Decimal("15") # FIXME on product 2 TODO
	quantity = Decimal(quantity)
	subtotal = quantity * UNIT_PRICE
	if state == 'MA':
		tx = Decimal(subtotal * settings.MA_TAX).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
	else:
		tx = Decimal("0")

	if coupon:
		coupon = get_coupon(coupon)
		if coupon:
			# coupon knows how to take $$ off of an order
			(subtotal, SHIPPING, tx) = coupon.calculate(quantity, UNIT_PRICE, SHIPPING, tx)

	if not shipping == SHIPPING:
		settings.SHOP_LOGGER.info("Shipping failed validation in validate_totals (%s vs %s)" % (shipping, SHIPPING))
		return False
	if not subtotal == amt:
		settings.SHOP_LOGGER.info("subtotal failed validation in validate_totals (%s vs %s)" % (subtotal, amt))
		return False
	if state == 'MA':
		if not tx == tax:
			settings.SHOP_LOGGER.info("Tax failed validation in validate_totals (%s vs %s)" % (tx, tax))
			return False
	
	return True


def purchase(userprofile=None, amt=15.00, shippingprice=5.00, tax=0.00, cctype='Visa', ccnum=settings.TEST_VISA_ACCOUNT_NO, expdate=settings.TEST_VISA_EXPIRATION, csc=settings.TEST_CVV2, firstname='John', middlename='',
			lastname='Doe', street='1313 Mockingbird Lane', street2='', city='Beverly Hills', state='CA', zip='90110',
			countrycode='US', currencycode='USD', journal_id=0, email=settings.TEST_EMAIL_PERSONAL, phone='', ipaddress='', quantity=0, coupon=''):
	"""
		Direct purchase through paypal.
	"""

	# make sure all amounts are not more precise than cents
	amt =  Decimal(amt).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
	shippingprice = Decimal(shippingprice).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
	tax =  Decimal(tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
	total_amt = amt + shippingprice + tax

	settings.SHOP_LOGGER.info("Purchase called: amt: %s, shipping: %s, tax: %s, cctype: %s, ccnum: %s, expdate: %s, csc: %s, firstname: %s, middlename: %s, lastname: %s, street: %s, street2: %s, city: %s, state: %s, zip: %s, countrycode: %s, currencycode: %s, journal_id: %s, email: %s, phone: %s, ipaddress: %s, coupon: %s" % 
		(amt, shippingprice, tax, cctype, ccnum, expdate, csc, firstname, middlename, lastname, street, street2, city, state, zip, countrycode, currencycode, journal_id, email, phone, ipaddress, coupon))

	if not validate_totals(state, shippingprice, tax, amt, quantity, coupon):
		return 'FAILURE: price hacked'

	try:

		if total_amt == 0:
			response_message = 'Approved'
			result = '0'
			auth_code = transaction_id = 'zero_value_from_coupon'
			
		else:
			# Setup the client object.
			client = PayflowProClient(partner=settings.PAYPAL_PARTNER_ID, vendor=settings.PAYPAL_VENDOR_ID, username=settings.PAYPAL_USERNAME, password=settings.PAYPAL_PASSWORD, url_base='https://payflowpro.paypal.com')

			# Here's a VISA Credit Card for testing purposes.
			credit_card = CreditCard(acct=ccnum, expdate=expdate, cvv2=csc)

			# Let's do a quick sale, auth only, with manual capture later
			responses, unconsumed_data = client.authorization(credit_card, Amount(amt=total_amt, currency="USD"), 
												extras=[Address(street=street + ',' + street2, city=city, billtocountry=countrycode, state=state, country=countrycode, companyname='', zip=zip)])

			# If the sale worked, we'll have a transaction ID
			transaction_id = responses[0].pnref # little string
			response_message = responses[0].respmsg # 'Approved', 'Invalid account number'
			auth_code = responses[0].authcode # little string, None on failure
			result = responses[0].result # 0, positive numbers are error codes
			auth_errors = responses[0].errors # {}

			if len(responses) > 1:
				# on error responses[1] may not exist
				avsaddr = responses[1].avsaddr # 'Y'
				iavs = responses[1].iavs # ?
				avszip = responses[1].avszip # ?
				addr_errors = responses[1].errors # {}

		if response_message == 'Approved' and result == '0':
			settings.SHOP_LOGGER.info("Purchase called: response from paypal was SUCCESS: success: %s, transactionid: %s, auth_code: %s, response_message: %s" % (result, transaction_id, auth_code, response_message))

			# create order-related db entries
			# XXX unitprice: replace with product's unit price HACK TODO FIXME
			shipping = create_shipping(firstname=firstname, middlename=middlename, lastname=lastname, addr1=street, addr2=street2, city=city, state=state, zip=zip, country=countrycode, telephone=phone)
			order = create_order(userprofile=userprofile, shipping=shipping, journal_id=journal_id, quantity=quantity, status='sold', ccauth=auth_code, notes='transaction_id: %s' % transaction_id,
								 unitprice=Decimal("15.00"), shippingprice=shippingprice, tax=tax, coupon_id=coupon)

			# create validation ticket
			return get_ticket(journal_id)

		settings.SHOP_LOGGER.info("Purchase called: response from paypal was FAILURE: success: %s, transactionid: %s, auth_errors: %s, response_message: %s" % (result, transaction_id, auth_errors, response_message))
		return 'FAILURE: %s' % (result)

	except Exception, err:
		traceback.print_exc()
		settings.SHOP_LOGGER.info("Purchase called: FAILURE, see exception log")
		settings.SHOP_LOGGER.exception("Exception:")
		return 'FAILURE: exception'

