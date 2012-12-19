$.extend(jotjournal.facebook, (function()
{
	var FbObj = (function()
	{
		function render(moreArgs)
		{
			var template = 'template';
			if (moreArgs && moreArgs['template'])
			{
				template = moreArgs['template'];
			}
			return this[template].parse_vars($.extend(moreArgs || {}, this));
		}

		function scoreUpdated()
		{
			var $s = $("#score_" + this.id);
			if ($s)
			{
				$s.html(this.score);
			}
		}

		// methods that don't conflict with child interface (don't override create)
		var __EXTENDS_INTERFACE__ = { render: render, scoreUpdated: scoreUpdated };
		function create(base, dataElement, setupFn)
		{
			var obj = $.extend(Object.create(base), __EXTENDS_INTERFACE__, dataElement);
			if (setupFn) { setupFn(obj); }
			return obj;
		}
		// methods for export (in particular, including create)
		var __FULL_INTERFACE__ = $.extend(__EXTENDS_INTERFACE__, { create: create });
		return __FULL_INTERFACE__;
	})();
	// useful alias:
	var _ = FbObj.create;

	var Album = {
		create: function(dataElement) { return _(Album, dataElement, function(album)
		{
			if (album.from)
			{
				album.from = Agent.create(album.from);
			}
		}) },
		getPhotos: function(callback)
		{
			var owner = this.from.id;
			//LOG(0, "Scanning " + owner + "'s photos from album " + this.id);
			jotjournal.facebook.getGraph(this.id, "photos", function(inid, response)
			{
				//LOG(0, "**Success! Album " + inid + " had " + response.data.length + " photos");
				response = jotjournal.facebook.makePhotosFromPhotosList(response.data);
				if (callback)
				{
					callback(response);
				}
			}.bind(this, this.id), function(response)
			{
				alert('failed: ' + response);
			});
		},
		template: '<a href="javascript:getAlbum(${id});">${name}</a> | '
	};

	var Photo = {
		create: function(dataElement)
		{
			return _(Photo, dataElement,
				function(photo)
				{
					if (photo.from)
					{
						photo.from = Agent.create(photo.from);
					}
					if (photo.tags)
					{
						var tags_data = photo.tags.data;
						var tags = [];
						for (var k = 0, l = tags_data.length; k < l; k++)
						{
							tags.push(Tag.create(tags_data[k]));
						}
						photo.tags = tags;
					}
				}
			);
		},
		getCaption: function()
		{
			return this.name;
		},
		template: '<img border="0" src="${picture}" />',
		small_grid_template:'<div class="small_grid_outer" title="${created_time} (${updated_time})"><div class="event_n_score">${event} / <span id="score_${id}">${score}</span></div><div class="small_grid"><img border="0" src="${picture}" /></div></div>'
	};

	var Friend = {
		create: function(dataElement) { return _(Friend, dataElement, function(friend)
		{
			if (friend.from)
			{
				friend.from = Agent.create(friend.from);
			}
		}) },
		template: '<a href="javascript:getFriendPhoto(${id});">${name}</a> | ' 
	};

	var Agent = {
		create: function(dataElement){ return _(Agent, dataElement, $.noop) }, template: ''
	};

	var News = {
		create: function(dataElement) { return _(News, dataElement, function(news)
		{
			if (news.from)
			{
				news.from = Agent.create(news.from);
			}
		}) },
		template: '<a href="javascript:getNews(${id});">${message}</a> | ',
		small_grid_template:'<div class="small_grid_outer" title="${id}"><div class="event_n_score">${event} / <span id="score_${id}">${score}</span></div><div class="small_grid">${message}</div></div>'
	};

	// synthetic object (not in facebook object hierarchy)
	var Caption = {
		create: function(dataElement){ return _(Caption, dataElement, $.noop) },
		template: '',
		small_grid_template:'<div class="small_grid_outer" title="${id}"><div class="event_n_score">${event} / <span id="score_${id}">${score}</span></div><div class="small_grid">${text}</div></div>'
	};

	// non-id-based
	var Action = {
		create: function(dataElement){ return _(Action, dataElement, $.noop) }, template: ''
	};

	var Comment = {
		create: function(dataElement) { return _(News, dataElement, function(comment)
		{
			if (comment.from)
			{
				comment.from = Agent.create(comment.from);
			}
		}) },
		template: ''
	};

	var Wall = {
		create: function(dataElement) { return _(Wall, dataElement, function(wall)
		{
			if (wall.actions)
			{
				var actions = [];
				for (var k = 0, l = wall.actions.length; k < l; k++)
				{
					actions.push(Action.create(wall.actions[k]));
				}
				wall.actions = actions;
			}
			if (wall.comments)
			{
				var comments_data = wall.comments.data;
				var comments = [];
				for (var k = 0, l = comments_data.length; k < l; k++)
				{
					comments.push(Comment.create(comments_data[k]));
				}
				wall.comments = comments;
			}
			if (wall.from)
			{
				wall.from = Agent.create(wall.from);
			}
		}) },
		template: '<a href="javascript:getWall(\'${id}\');"><img border="0" src="${picture}"/>${caption} / ${link} / ${name}</a> | ',
		small_grid_template:'<div class="small_grid_outer" title="${id}"><div class="event_n_score">${event} / <span id="score_${id}">${score}</span></div><div class="small_grid">${caption} / ${link} / ${name}</div></div>'
	};

	var Tag = {
		create: function(dataElement){ return _(Tag, dataElement, $.noop) }, template: ''
	};

	var Like = {
		create: function(dataElement){ return _(Like, dataElement, $.noop) }, template: '<a href="javascript:getLike(${id});">${name} [${category}]</a> | '
	};

	return { Photo: Photo, Tag: Tag, Wall: Wall, News: News, Friend: Friend, Comment: Comment, Action: Action, Agent: Agent, Like: Like, Album: Album, Caption: Caption };
})());


/*

TODO: 'paging' api common to all graph data

*/

/* ALBUM Data element:
	count
	created_time
	description
	from = AGENT
	id
	link
	location
	name
	privacy
	updated_time
*/

/* PHOTO Data element:
	var created_time = o.created_time;
	var from = AGENT
	var from_id = from.id;
	var from_name = from.name;
	var height = o.height;
	var icon = o.icon;
	var id = o.id;
	var link = o.link;
	var name = o.name <--!! the photo's caption
	var picture = o.picture;
	var source = o.source;
	var tags = o.tags;
	tags = TAGS
	var updated_time = o.updated_time;
	var width = o.width;
*/

/* FRIEND Data element:
	var created_time = o.created_time;
	var from = AGENT
	var height = o.height;
	var icon = o.icon;
	var id = o.id;
*/

/* NEWS Data element:
	var created_time = o.created_time;
	var id = o.id;
	var from = AGENT
	var message = o.message;
	var updated_time = o.updated_time;
*/

/* ACTION
	link: o.actions[n].link
	name: o.actions[n].name
*/

/* COMMENT
	created_time: o.comments.data[n].created_time,
	from: AGENT
	id: o.comments.data[n].id,
	message: o.comments.data[n].message
*/

/* WALL Data element:
	var actions = ACTIONS
	var attribution = o.attribution;
	var caption = o.caption;
	var comments = COMMENTS
	var created_time = o.created_time;
	from = AGENT
	var icon = o.icon;
	var id = o.id;
	var link = o.link;
	var name = o.name;
	var picture = o.picture;
	var updated_time = o.updated_time;
*/

/* TAG Data element:
	created_time: _o.created_time,
	id: _o.id,
	name: _o.name,
	x: _o.x,
	y: _o.y
*/

// AGENT: id, name

/* LIKES: id, name, category */
