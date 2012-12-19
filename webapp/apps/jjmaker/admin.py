from django.contrib import admin
from jjmaker.models import Order, UserProfile, Coupon, Shipping, Unsubscriber

class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('id', 'fb_fname', 'fb_lname', 'fb_name', 'fb_id', 'email')

admin.site.register(UserProfile, UserProfileAdmin)


class OrderAdmin(admin.ModelAdmin):
	date_hierarchy = 'created'
	list_display = ('id', 'user_id', 'product_id', 'shipping_id', 'journal_id', 'quantity', 'status', 'coupon_id')

	def user_id(self, obj):
		try:
			return '%s (%s)' % (obj.user.id, obj.user.fb_name)
		except:
			return ''
	def product_id(self, obj):
		try:
			return obj.product.id
		except:
			return ''
	def shipping_id(self, obj):
		try:
			return obj.shipping.id
		except:
			return ''


admin.site.register(Order, OrderAdmin)


class ShippingAdmin(admin.ModelAdmin):
	list_display = ('firstname', 'lastname', 'addr1', 'city', 'state', 'zip', 'telephone')

admin.site.register(Shipping, ShippingAdmin)


class CouponAdmin(admin.ModelAdmin):
	list_display = ('ctype', 'amount', 'code')

admin.site.register(Coupon, CouponAdmin)


