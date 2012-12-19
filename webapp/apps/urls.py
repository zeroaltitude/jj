from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^jjmaker/journal/?$', 'jjmaker.views.journal'),
	#(r'^jjmaker/jstest/?$', 'jjmaker.views.jstest'),
	(r'^jjmaker/create_debug/?$', 'jjmaker.views.create_debug'),

	(r'^jjmaker/?$', 'jjmaker.views.landing'),
	(r'^jjmaker/create/?$', 'jjmaker.views.create'),
	(r'^jjmaker/review/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.review'),
	(r'^jjmaker/shop/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.shop'),
	(r'^jjmaker/thanks/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.thanks'),
	(r'^jjmaker/checkout/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.checkout'),
	(r'^jjmaker/get_fid/(?P<journal_id>[^/]+)/(?P<quadrant_id>[^/]+)/?$', 'jjmaker.views.get_fid'),
	(r'^jjmaker/apply_coupon/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.apply_coupon'),
	(r'^jjmaker/set_title/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.set_title'),
	(r'^jjmaker/too_little_content/?$', 'jjmaker.views.too_little_content'),

	(r'^jjmaker/share/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.share'),
	(r'^jjmaker/disconnect/?$', 'jjmaker.views.disconnect'),

	(r'^jjmaker/tos/?$', 'jjmaker.views.tos'),
	(r'^jjmaker/unsubscribe/?$', 'jjmaker.views.unsubscribe_view'),

	(r'^jjmaker/popunder/?$', 'jjmaker.views.popunder'),

    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

	(r'^jjmaker/journal_1_view/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.journal_1_view'),
	(r'^jjmaker/journal_1_pdf/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.journal_1_pdf'),
	(r'^jjmaker/journal_1_popimg/(?P<journal_id>[^/]+)/.*$', 'jjmaker.views.journal_1_popimg'),
	(r'^jjmaker/journalstyle/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.journal_stylesheet'),

	(r'^jjmaker/promotion/?$', 'jjmaker.views.promotion'),
	(r'^jjmaker/promotion_checkout/(?P<journal_id>[^/]+)/?$', 'jjmaker.views.promotion_checkout'),
)
