

ITEM_VISIBILITY_STATES = (
	('shown', 'shown'),
	('removed', 'removed'),
	('hidden', 'hidden'),
	('rejected', 'rejected'),
)


ACTIVITY_TYPES = (
	('logged_in', 'logged_in'),
	('logged_out', 'logged_out'),
	('viewed_journal', 'viewed_journal'),
	('bought_journal', 'bought_journal'),
	('removed_item', 'removed_item'),
	('liked_item', 'liked_item'),
	('commented_item', 'commented_item'),
	('shared_item', 'shared_item'),
	('failed_to_make_journal_from_scarce_items', 'failed_to_make_journal_from_scarce_items'),
)


JOURNAL_STATUSES = (
	('active', 'active'),
	('deleted', 'deleted'),
	('printed', 'printed'),
)


ORDER_STATUSES = (
	('active', 'active'),
	('failed', 'failed'),
	('authorized', 'authorized'),
	('sold', 'sold'),
	('shipped', 'shipped'),
	('returned', 'returned'),
	('promotion', 'promotion'),
)


GRAVITIES = (
	('center', 'center'),
	('lefttop', 'lefttop'), # can be for horiz OR vert, so name it funny
	('rightbottom', 'rightbottom'), # can be for horiz OR vert, so name it funny
)


MOLD_TYPES = (
	('photo', 'photo'),
	('message', 'message'),
)


MODEL_TYPES = (
	('Journal', 'Journal'),
	('UserProfile', 'UserProfile'),
	('JournalItem', 'JournalItem'),
	('JournalPage', 'JournalPage'),
	('Facebook', 'Facebook'),
)


FB_ITEM_TYPES = (
	('photo', 'photo'),
	('caption', 'caption'),
	('wall', 'wall'),
	('status', 'status'),
)


DEFAULT_PAGE_COUNT = 33

