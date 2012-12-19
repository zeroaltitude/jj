jotjournal.facebook = (function()
{
	var COMMENTS_WEIGHT = 3;
	var LIKES_WEIGHT = 2;
	var _TEXTS = []; // { id: id, text:text, type:{caption|wall|news}, date:date, event:event, score:score, linked_to:{photo_id|''} }
	var _PHOTOS = [];
	var status_messages = "";
	var AGGRESSIVE_TEXTS = true;
	var CLIENT_CULLING = false;
	var _TEMPLATE = 2;
	var DEBUG_ALL = 0;
	var photos_max = 76; // rough
	var text_max = 76; // every photo has a text for some modes
	var inclusion_target = photos_max + text_max; // rough
	var photos_min = 45;
	var text_min = 45;

	/*
		this option, as per Liesel, causes the algorithm in the photo adder to not just pick captions, but also tags and
		dates as possible texts
	*/
	function toggleAggressiveTexts()
	{
		AGGRESSIVE_TEXTS = !AGGRESSIVE_TEXTS;
	}

	function toggleClientCulling()
	{
		CLIENT_CULLING = !CLIENT_CULLING;
	}

	function setTemplate(val)
	{
		_TEMPLATE = val;
	}

	function notCut(obj)
	{
		var c = jotjournal.getCookie("cuts");
		if (c)
		{
			if (c.indexOf("," + obj.id) != -1)
			{
				//LOG(0, "Cut " + obj.id + "!");
				return false;
			}
		}
		return true;
	}

	function notAlreadyPresentInTexts(obj)
	{
		/*
			If obj is a caption and what's in texts already is a status, then clobber status and return false (we'll add by clobbering)
			Otherwise, on match, return false
			Else, return true
		*/
		var m = obj.message;
		for (var i = 0, j = _TEXTS.length; i < j; i++)
		{
			if (_TEXTS[i].message == m)
			{
				if ((obj.type == "caption") && (_TEXTS[i].type == "status"))
				{
					//LOG(0, "obj type clobbered texts type", obj.type, _TEXTS[i].type, obj);
					_TEXTS[i] = obj;
				}
				return false;
			}
		}
		return true;
	}

	// conforming object: obj.created_time
	function pushText(conformingObject, objtype)
	{
		var c = jotjournal.events.facebookDateToJsDate(conformingObject.created_time);
		conformingObject.date = c;
		var _mysqldate = conformingObject.created_time.split('T');
		var _mysqltime = _mysqldate[1].split('+')[0];
		conformingObject.mysql_date = _mysqldate[0] + " " + _mysqltime;
		conformingObject.event = 0;
		conformingObject.score = 0;
		conformingObject.type = (objtype == jotjournal.facebook.Wall) ? 'wall' : 'status';
		conformingObject.linked_to = '';
		conformingObject.link = conformingObject.link || '';
		conformingObject.message = conformingObject.message || conformingObject.text;
		if (conformingObject.message && passesTextFilter(conformingObject.message) && notAlreadyPresentInTexts(conformingObject) && notCut(conformingObject))
		{
			_TEXTS.push(conformingObject);
		}
	}

	function epochTimeAsFacebookTime(epochTime)
	{
		// 2007-11-28T23:24:44+0000
		var d = new Date(parseInt(epochTime) * 1000);
		var lt = d.toLocaleTimeString();
		// on safari (chrome?), locale time string includes am/pm and timezone (and we're going to ignore the 12 hour problem that you get knocking off the ampm)
		if (lt.indexOf(' ') > -1)
		{
			lt = lt.split(' ')[0];
		}
		return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate() + 'T' + lt + '+0000';
	}

	function getStatusUpdates(user, callback)
	{
		LOG(0, "getStatusUpdates: start");
		// the stream is far too busy to use paging to get these, so we query for just *our* status updates
		if (status_messages)
		{
			status_messages.append("Getting status updates (fetching)...<br/>");
		}
		//getFQL("SELECT message, created_time, updated_time, post_id, actor_id, likes, comments, attachment FROM stream WHERE source_id = " + user + " AND actor_id = " + user + " AND message != ''", function(response)
		//"https://graph.facebook.com/me/feed?access_token=2227470867|2.AQA_BvBqG07ijYUY.3600.1308193200.0-572816695|xE4fJbKhXw1kcgvCu7htd7BGBA0&limit=1000";
		FB.api('/me/feed', { limit: 250 }, function(response)
		{
			LOG(0, "getFQL stream anon response: start", response);
			if (status_messages)
			{
				status_messages.append("Getting status updates (adding to queue)...<br/>");
			}
			if (response && response.data)
			{
    			for (var i = 0, j = response.data.length; i < j; i++)
    			{
    				var d = response.data[i];
    				// Omit status updates with link attachments or not posted by me:
    				if (!d ||
    					(d.type !== "status") ||
    					((d.attachment) && (d.attachment.href)) || 
    					(d.message === '') ||
    					(d.from && (d.from.id != FB.getAuthResponse().userID))
    				)
    				{
    					continue;
    				}
    				d.id = 'news_' + d.id;
    				var n = jotjournal.facebook.News.create(d);
    				//LOG(0, 'stream item', n);
    				pushText(n, jotjournal.facebook.News);
    				var lc = d.likes ? d.likes.count : 0;
    				var cc = d.comments ? d.comments.count : 0;
    				n.score = parseInt(lc || 0) * LIKES_WEIGHT + parseInt(cc || 0) * COMMENTS_WEIGHT;
    			}
			}
			else
			{
			    LOG(0, "getStatusUpdates response no data", response, FB);
			}
			if (callback)
			{
				callback();
			}
			LOG(0, "getFQL stream anon response: end");
		});
		LOG(0, "getStatusUpdates: end");
	}

	var badExpressions = [
		"Shozu",
		"shozu",
		"ShoZu",
		"Check out this video",
		"http://"
	];
	function passesTextFilter(output)
	{
		for (var i = 0, j = badExpressions.length; i < j; i++)
		{
			if (output.indexOf(badExpressions[i]) > -1)
			{
				return false;
			}
		}
		return true;
	}

	function getItemFromList(list, item_id)
	{
		for (var i = 0, j = list.length; i < j; i++)
		{
			if (item_id == list[i].id)
			{
				return list[i];
			}
		}
	}

	function analyzeInclusion(texts, photos)
	{
		/*
			Inclusion:
			
			1.  Highest scored photos
			2.  Texts linked to included photos
			3.  Rest of the texts up to a maximum.
			4.  Fill out events by inclusion and count of photos in event
			5.  Fill in remainder with photos, last to first
		*/
		/* **************************************************************** Setup **/
		texts.sort(dateSorter);
		photos.sort(dateSorter);

		var selected = [[], []];
		var countincluded = 0;
		var countscored = 0;
		var eventsmap = {}; // eventnum => [array of indices]
		var lastevent = photos[photos.length - 1].event;
		var scoremap = {}; // score => [array of indices]
		var scorearray = []; // so we can sort scores
		var events_mapped = {};
		var events_mapped_array = [];
		for (var i = photos.length - 1; i >= 0; i--)
		{
			var p = photos[i];
			var e = p.event;
			var s = p.score;
			if (s > 0)
			{
				countscored++;
			}
			if (!eventsmap[e])
			{
				eventsmap[e] = [];
			}
			eventsmap[e].push(i);
			if (!scoremap[s])
			{
				scoremap[s] = [];
			}
			scoremap[s].push(i);
			if (scorearray.indexOf(s) == -1)
			{
				scorearray.push(s);
			}
		}
		scorearray.sort();
		/* **************************************************************** Pass 1 */
		for (var i = scorearray.length - 1; i >= 0; i--)
		{
			var thisscore = scorearray[i];
			var scores = scoremap[thisscore];
			var count = scores.length;
			for (var j = 0; j < count; j++)
			{
				selected[0].push(photos[scores[j]]);
				events_mapped[photos[scores[j]].event] = "1";
				countincluded++;
				if (countincluded >= (inclusion_target - text_max)) // save some room for texts
				{
					i = -1; // exit both loops
					break;
				}
			}
		}
		//LOG(0, "analyzeInclusion1", countincluded, countscored, eventsmap, lastevent, scoremap, scorearray);
		/* **************************************************************** Pass 2 */
		for (var i = texts.length - 1; i >= 0; i--)
		{
			var linked_to = texts[i].linked_to;
			if (linked_to)
			{
				// see if the photo referenced is in the inclusion list already, and if not, add it
				var pho = getItemFromList(selected[0], linked_to);
				if (!pho)
				{
					pho = getItemFromList(photos, linked_to);
					events_mapped[pho.event] = "1";
					selected[0].push(pho);
					countincluded++;
				}
				// now add the text
				selected[1].push(texts[i]);
				countincluded++;
			}
			if ((selected[1].length >= text_max) || (countincluded >= inclusion_target))
			{
				break;
			}
		}
		//LOG(0, "analyzeInclusion2", countincluded, countscored, eventsmap, lastevent, scoremap, scorearray);
		/* **************************************************************** Pass 3 */
		if ((selected[1].length < text_max) && (countincluded < inclusion_target))
		{
			for (var i = texts.length - 1; i >= 0; i--)
			{
				var item = getItemFromList(selected[1], texts[i].id);
				if (!item)
				{
					selected[1].push(texts[i]);
					countincluded++;
					if ((selected[1].length >= text_max) || (countincluded >= inclusion_target))
					{
						break;
					}
				}
			}
		}
		//LOG(0, "analyzeInclusion3", countincluded, countscored, eventsmap, lastevent, scoremap, scorearray);
		/* **************************************************************** Pass 4 */
		if (countincluded < inclusion_target)
		{
			for (var i in events_mapped)
			{
				if (events_mapped.hasOwnProperty(i))
				{
					events_mapped_array.push(i);
				}
			}
			events_mapped_array.sort();
			for (var i = events_mapped_array.length - 1; i >= 0; i--)
			{
				var thislist = eventsmap[events_mapped_array[i]];
				for (var j = 0, k = thislist.length; j < k; j++)
				{
					var pho = photos[thislist[j]];
					var item = getItemFromList(selected[0], pho.id);
					if (!item)
					{
						selected[0].push(pho);
						countincluded++;
					}
					if (countincluded >= inclusion_target)
					{
						i = -1; // exit both loops
						break;
					}
				}
			}
			//LOG(0, "analyzeInclusion4", countincluded, countscored, eventsmap, lastevent, scoremap, scorearray);
		}
		/* **************************************************************** Pass 5 */
		if (countincluded < inclusion_target)
		{
			for (var i = photos.length - 1; i >= 0; i--)
			{
				var pho = photos[i];
				var item = getItemFromList(selected[0], pho.id);
				if (!item)
				{
					selected[0].push(pho);
					countincluded++;
				}
				if (countincluded >= inclusion_target)
				{
					break;
				}
			}
			//LOG(0, "analyzeInclusion5", countincluded, countscored, eventsmap, lastevent, scoremap, scorearray);
		}

		selected[0].sort(dateSorter);
		selected[1].sort(dateSorter);
		//LOG(0, "analyzeInclusion-end", selected);
		return selected;
	}

	function tellServerTooLittleContent(photoCount, textCount)
	{
		jotjournal.ajax(
			"/jjmaker/too_little_content",
			{ photoCount: photoCount, textCount: textCount },
			function(XMLHttpRequest, textStatus)
			{
				var responseObj = JSON.parse(XMLHttpRequest.responseText);
			}
		);
	}

	function sendJournal(texts, photos, template, callback, failure_callback)
	{
		var selected;
		if (CLIENT_CULLING)
		{
			LOG(0, "Running pre-analysis");
			/* preanalysis */
			if (status_messages)
			{
				status_messages.append("Running pre-send analysis on photos and messages for inclusion in online journal...<br/>");
			}
			selected = analyzeInclusion(texts, photos);
		}
		else
		{
			if (status_messages)
			{
				status_messages.append("*NOT* running pre-send analysis on photos and messages for inclusion in online journal, just taking first " + inclusion_target + "...<br/>");
			}
			texts.sort(dateSorter);
			photos.sort(dateSorter);
			var metadata = "photos_length:" + photos.length + ";texts_length:" + texts.length + ";first_photo:" + (photos[0] ? photos[0].id : "") + ";first_text:" + (texts[0] ? texts[0].id : "") + ";last_photo:" + (photos[0] ? photos[photos.length-1].id : "") + ";last_text:" + (texts[0] ? texts[texts.length-1].id : "");
			if (texts.length > text_max)
			{
				texts.splice(0, texts.length - text_max);
			}
			if (photos.length > photos_max)
			{
				photos.splice(0, photos.length - photos_max);
			}
			selected = [photos, texts];
		}

		/* Possible early exit: did we not get enough stuff to make a book out of? */
		if ((selected[0].length + selected[1].length) < (photos_min + text_min))
		{
			// tell the server about this in the meanwhile
			tellServerTooLittleContent(selected[0].length, selected[1].length);
			if (status_messages)
			{
				status_messages.append("Abort: not enough content to make a book (" + selected[0].length + ' + ' + selected[1].length + ")");
			}
			if (failure_callback)
			{
				failure_callback();
			}
			return;
		}
		LOG(0, "Got OK content amount: " + selected[0].length + " + " + selected[1].length);
		/* *********************************************************************** */

		if (status_messages)
		{
			status_messages.append("Sending chosen photos and messages to server for creation of new journal...<br/>");
		}
		jotjournal.ajax(
			"/jjmaker/journal",
			{ texts: JSON.stringify(selected[1]), photos: JSON.stringify(selected[0]), template: template, metadata: metadata },
			function(XMLHttpRequest, textStatus)
			{
				var responseObj = JSON.parse(XMLHttpRequest.responseText);
				var sufficient = responseObj.sufficient;
				var id = responseObj.id;
				if (status_messages)
				{
					if (sufficient)
					{
						status_messages.append("Your journal was created, and the id was " + id + "<br/>");
						status_messages.append("You can see the HTML version of your journal <a target='_new' href='/jjmaker/journal_1_view/" + id + "/'>here</a>.<br/>");
						status_messages.append("You can see the PDF version of your journal <a target='_new' href='/jjmaker/journal_1_pdf/" + id + "/'>here</a>.<br/>");
						status_messages.append("You can see the Popular Image version of your journal <a target='_new' href='/jjmaker/journal_1_popimg/" + id + "/'>here</a>.<br/>");
						if (callback)
						{
							callback(id);
						}
					}
					else
					{
						if (failure_callback)
						{
							failure_callback(responseObj);
						}
						else
						{
							if (responseObj.exc)
							{
								alert('Problem: encountered unexpected error; email jotjournal@myjotjournal.com with journal ID ' + id + ' and detail message: ' + responseObj.exc);
								status_messages.append("Hmm, something seems to have gone wrong, is this false?: " + sufficient + "<br/>");
							}
							else
							{
								alert('Problem: insufficient Facebook content to create journal -- send this message and your Facebook user id to eddie@myjotjournal.com');
								status_messages.append("Hmm, something seems to have gone wrong, is this false?: " + sufficient + "<br/>");
							}
						}
					}
				}
			}
		);
	}

	function gatherJournalAssets(e, stage1_callback, stage2_callback, stage3_callback, stage4_callback, journal_made_callback, no_journal_made_callback)
	{
		LOG(0, "gatherJournalAssets: start");
		// status updates are news feed items (/home) that are FROM me
		// reset _PHOTOS and _TEXTS:
		if (status_messages)
		{
			status_messages.append("Gathering photos and messages from your Facebook account...<br/>");
		}
		_PHOTOS.length = 0;
		_TEXTS.length = 0;
		getUserAlbumPhotos('me',
			scoreObj,
			function(photos, photos_dates)
			{
				LOG(0, "getUserAlbumPhotos anon response: start");
				if (status_messages)
				{
					status_messages.append("Event segmenting photos and messages...<br/>");
				}
				if (CLIENT_CULLING)
				{
					LOG(0, "Grouping events");
					groupEvents(photos, photos_dates);
				}
				var html = '';
				for (var i = 0, j = photos.length; i < j; i++)
				{
					html += photos[i].render({ template: 'small_grid_template' });
				}
				if (DEBUG_ALL)
				{
					if (status_messages)
					{
						status_messages.append("Rendering photos and messages to page for review...<br/>");
					}
					if ($("#results_photos"))
					{
						$("#results_photos").append(html);
					}
				}
				html = '';
				for (var i = 0, j = _TEXTS.length; i < j; i++)
				{
					var output = _TEXTS[i].render({ template: 'small_grid_template' });
					// Filter out unuseful texts:
					if (passesTextFilter(output))
					{
						html += output;
					}
				}
				if (DEBUG_ALL)
				{
					if ($("#results_texts"))
					{
						$("#results_texts").append(html);
					}
				}
				// to the server we go:
				_PHOTOS.push.apply(_PHOTOS, photos);
				if (status_messages)
				{
					status_messages.append("!!Now waiting 30 seconds for any stragglers to come in!!...template is.... " + _TEMPLATE + "<br/>");
				}
				if (stage3_callback)
				{
					setTimeout(stage3_callback, 5000);
				}
				setTimeout(journal_made_callback.bind(this, _TEXTS, _PHOTOS, _TEMPLATE, stage4_callback, no_journal_made_callback), 10000);
				LOG(0, "getUserAlbumPhotos anon response: end");
			}
		);
		if (stage1_callback)
		{
			stage1_callback();
		}
		getStatusUpdates('me', stage2_callback);
		LOG(0, "gatherJournalAssets: end");
	}

	function dateSorter(a, b)
	{ 
		if (a.date > b.date) { return 1; }
		else if (a.date < b.date) { return -1; }
		else { return 0; }
	}

	function scoreObj(obj)
	{
		getGraph(obj.id, "comments", function(obj, response)
		{
			if (response.data.length > 0)
			{
				obj.score += response.data.length * COMMENTS_WEIGHT;
				obj.scoreUpdated();
				//LOG(0, "**COMMENTS: Success! " + obj.id + " had " + response.data.length + " connections (score:" + obj.score + '/' + obj.event + ")");
			}
		}.bind(this, obj));

		getGraph(obj.id, "likes", function(obj, response)
		{
			if (response.data.length > 0)
			{
				obj.score += response.data.length * LIKES_WEIGHT;
				//LOG(0, "**LIKES: Success! " + obj.id + " had " + response.data.length + " connections (score:" + obj.score + '/' + obj.event + ")");
			}
		}.bind(this, obj));
	}

	function groupEvents(photos, photos_dates)
	{
		LOG(0, "groupEvents: start");
		var b = jotjournal.events.calculate(photos_dates);
		var eventIndex = 0;
		// sort photos chrono:
		photos.sort(dateSorter);
		for (var i = 0, j = photos.length; i < j; i++)
		{
			var e = photos[i];
			var boundary = b[eventIndex];
			var edate = e.date;
			if (edate >= boundary)
			{
				++eventIndex;
			}
			// LOG(0, "compare photo " + i + " and event index " + eventIndex + " eventdate:" + edate + " boundary:" + boundary);
			e.event = eventIndex;
		}
		// LOG(0, "bounded events:", photos);
		LOG(0, "groupEvents: end");
		return photos;
	}

	var _mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	function asPrettyDate(c)
	{
		return _mon[c.getMonth()] + " " + c.getDate() + ", " + c.getFullYear();
	}

	function pushPhoto(photos, photos_dates, photo)
	{
		// if this photo doesn't have a source, we can't use it
		if (!photo || !photo.source)
		{
			return;
		}
		if (!notCut(photo))
		{
			return;
		}
		var c = jotjournal.events.facebookDateToJsDate(photo.created_time);
		photo.date = c;
		var _mysqldate = photo.created_time.split('T');
		var _mysqltime = _mysqldate[1].split('+')[0];
		photo.mysql_date = _mysqldate[0] + " " + _mysqltime;
		photo.event = 0;
		photo.score = 0;
		photo.type = 'photo';
		var pushed = false;
		if (photo.name) // comments
		{
			if (passesTextFilter(photo.name))
			{
				var obj = jotjournal.facebook.Caption.create({ id: "caption_" + photo.id, link: photo.link, message: photo.name, text: photo.name, type: 'caption', date: photo.date, mysql_date: photo.mysql_date, event: 0, score: 0, linked_to: photo.id });
				pushed = true;
				if (notAlreadyPresentInTexts(obj) && notCut(obj))
				{
					_TEXTS.push(obj);
					//LOG(0, "Added photo caption from photo.name " + photo.name + " (" + photo.id + ")");
				}
			}
		}

		if (AGGRESSIVE_TEXTS && !pushed)
		{
			if (photo.tags && (photo.tags.length > 0))
			{
				var names = [];
				for (var i = 0, j = photo.tags.length; i < j; i++)
				{
					if (photo.tags[i].name)
					{
						names.push(photo.tags[i].name);
					}
				}
				if (names.length > 0)
				{
					names = names.join(', ');
					var obj = jotjournal.facebook.Caption.create({ id: "caption_" + photo.id, link: photo.link, message: names, text: names, type: 'caption', date: photo.date, mysql_date: photo.mysql_date, event: 0, score: 0, linked_to: photo.id });
					pushed = true;
					if (notAlreadyPresentInTexts(obj) && notCut(obj))
					{
						_TEXTS.push(obj);
					}
				}
			}
			if (!pushed)
			{
				var obj = jotjournal.facebook.Caption.create({ id: "caption_" + photo.id, link: photo.link, message: asPrettyDate(c), text: asPrettyDate(c), type: 'caption', date: photo.date, mysql_date: photo.mysql_date, event: 0, score: 0, linked_to: photo.id });
				if (notAlreadyPresentInTexts(obj) && notCut(obj))
				{
					_TEXTS.push(obj);
					//LOG(0, "Added pretty date photo caption " + asPrettyDate(c) + " (" + photo.id + ")");
				}
			}
		}

		photos.push(photo);
		photos_dates.push(c.getTime());
	}

	var _photoCallsOutstanding = 0;
	function getUserAlbumPhotos(user, perPhotoCallback, finalCallback)
	{
		var photos = []; // photo objs decorated with 'date', 'event' and 'score'
		var photos_dates = [];
		if (status_messages)
		{
			status_messages.append("Getting photo albums (fetching)...<br/>");
		}
		jotjournal.facebook.getGraph(user, 'albums', function(albumsList)
		{
		    if (albumsList && albumsList.data)
		    {
    			for (var i = 0, j = albumsList.data.length; i < j; i++)
    			{
    				var isLast = (i == (albumsList.data.length - 1));
    				var album = jotjournal.facebook.Album.create(albumsList.data[i]);

    				if (album.name.indexOf('JotJournal') != -1)
    				{
    					// fix #52: no JJ albums in stream
    					continue;
    				}

    				if (status_messages)
    				{
    					status_messages.append("Getting photos for album " + album.id + " (fetching)...<br/>");
    				}
    				_photoCallsOutstanding++;
    				album.getPhotos(function(isLast, photosArray)
    				{
    					if (status_messages)
    					{
    						status_messages.append("Getting photos (adding to queue)...<br/>");
    					}
    					for (var k = 0, l = photosArray.length; k < l; k++)
    					{
    						var photo = photosArray[k];
    						pushPhoto(photos, photos_dates, photo);
    						if (perPhotoCallback)
    						{
    							perPhotoCallback(photo);
    						}
    					}
    					_photoCallsOutstanding--;
    					if (_photoCallsOutstanding == 0)
    					{
    						if (finalCallback)
    						{
    							setTimeout(function(){finalCallback(photos, photos_dates);}, 10000); // 10 seconds of wiggle room, possibly needed because the perPhotoCallback could *also* be async! (scoring)
    						}
    					}
    				}.bind(this, isLast));
    			}
			}
			else
			{
			    LOG(0, "getUserAlbumPhotos no albums list", albumsList, FB);
			}
		});
	}

	function makePhotosFromPhotosList(photosList)
	{
		var photos = [];
		for (var i = 0, j = photosList.length; i < j; i++)
		{
			var photo = jotjournal.facebook.Photo.create(photosList[i]);
			photos.push(photo);
		}
		return photos;
	}

	var giirCache = {};
	function getItemsInRange(date1, date2, photos, texts)
	{
		if (giirCache[date1] !== undefined && giirCache[date1][date2] !== undefined)
		{
			return giirCache[date1][date2];
		}
		var count = 0;
		for (var i = 0, j = 2; i < j; i++)
		{
			var items = (i == 0) ? photos : texts;
			for (var k = 0, l = items.length; k < l; k++)
			{
				var x = new Date(items[k].date);
				if ((x >= date1) && (x <= date2))
				{
					count++;
				}
			}
		}
		//LOG(0, "Count is " + count + " for " + date1 + " and " + date2);
		if (!giirCache[date1])
		{
			giirCache[date1] = {};
		}
		giirCache[date1][date2] = count;
		return count;
	}

	function filterItemsByDate(items, date1, date2)
	{
		var newitems = [];
		for (var i = 0, j = items.length; i < j; i++)
		{
			var d = new Date(items[i].date);
			//LOG(0, "Comparing item " + items[i] + " with " + date1 + " and " + date2);
			if (((d >= date1) || (date1 === null)) && ((d <= date2) || (date2 === null)))
			{
				newitems.push(items[i]);
			}
		}
		//LOG(0, "Count is " + newitems.length + " for " + date1 + " and " + date2);
		return newitems;
	}

	var _RANGE_BEGIN = null;
	var _RANGE_BEGIN_UNIT = null;
	var _RANGE_END = null;
	var _RANGE_END_UNIT = null;
	function setDateRangeAndContinue(texts, photos, template, callback, failure_callback)
	{
		//LOG(0, texts, photos, template, callback, failure_callback, _RANGE_BEGIN, _RANGE_END);
		$("#graphblackout").css("display", "none");
		sendJournal(filterItemsByDate(texts, _RANGE_BEGIN, _RANGE_END), filterItemsByDate(photos, _RANGE_BEGIN, _RANGE_END), template, callback, failure_callback);
	}

	function journalToMake(texts, photos, template, callback, failure_callback)
	{
		//////////////////////////////////////////////////////////////////////////// set up
		texts.sort(jotjournal.facebook.dateSorter);
		photos.sort(jotjournal.facebook.dateSorter);
		//////////////////////////////////////////////////////////////////////////// date range
		var tb = new Date(texts[0].date);
		var te = new Date(texts[texts.length - 1].date);
		var pb = new Date(photos[0].date);
		var pe = new Date(photos[texts.length - 1].date);
		var b = (tb >= pb) ? pb : tb;
		var e = (te <= pe) ? pe : te;
		var diff_ms = e - b;
		var days = diff_ms / 1000 / 60 / 60 / 24; // date range in days
		//////////////////////////////////////////////////////////////////////////// canvas spec
		var canvas_width = 700;
		var canvas_height = 100;
		var header_height = 112;
		// divide into 70 units (2 x width 10 x 70 = 1400)
		var BARS_PER_UNIT = 2; // text bar and photo bar
		var BAR_WIDTH = 5;
		var UNITS = canvas_width / (BAR_WIDTH * BARS_PER_UNIT);
		var HEIGHT_UNIT = 4; // how high 1 is in px
		var MAXH = parseInt(canvas_height / HEIGHT_UNIT);
		var span = days / UNITS;
		if (span < 1) { span = 1; }
		// turn the span into a ms interval
		var spanms = span * 24 * 60 * 60 * 1000;
		var pdArray = new Array(UNITS);
		var tdArray = new Array(UNITS);
		//////////////////////////////////////////////////////////////////////////// set up and display the widget
		var w_height = $(window).height();
		var w_width = $(window).width();
		var gt = (parseInt(w_height/2) - parseInt(canvas_height/2));
		var gl = (parseInt(w_width/2) - parseInt(canvas_width/2));
		$("#graphblackout").css("display", "block").css("height", w_height + "px").css("width", w_width + "px");
		$("#graph").css("width", canvas_width + "px").css("height", canvas_height + "px").css("top", gt - header_height + "px").css("left", gl + "px");
		$("#graph_label").css("top", (gt - 24 - header_height) + "px").css("left", gl + "px");
		$("#graph_slider").css("width", (canvas_width + 4) + "px").css("top", (gt + canvas_height + 10 - header_height) + "px").css("left", gl + "px");
		$("#graph_caption").css("top", (gt + canvas_height + 35 - header_height) + "px").css("left", gl + "px");
		$("#graph_continue").css("top", (gt + canvas_height + 42 - header_height + 20) + "px").css("left", (gl + canvas_width - 58) + "px");
		$("#graph_continue").live("click", setDateRangeAndContinue.bind(jotjournal.facebook, texts, photos, template, callback, failure_callback));
		$("#graph_slider").slider({
			range: true,
			min: 0,
			max: UNITS,
			values: [0, UNITS],
			slide: function(event, ui)
			{
				var first_slider = ui.values[0];
				var second_slider = ui.values[1];
				// which one is moving:
				var moving;
				if (_RANGE_BEGIN_UNIT == first_slider)
				{
					// second one is moving
					moving = 2;
				}
				else
				{
					// first one is moving
					moving = 1;
				}
				var d1 = new Date(b.getTime() + spanms * first_slider);
				var d2 = new Date(b.getTime() + spanms * second_slider);
				var items = getItemsInRange(d1, d2, photos, texts);
				//LOG(0, "items: " + items);
				if (items < (photos_min + text_min + 20)) // wiggle room
				{
					if (moving == 1)
					{
						// attempt to bring OUT slider 2
						var bringin = second_slider;
						while (1)
						{
							if (bringin == UNITS)
							{
								return false;
							}
							bringin += 1;
							var bd2 = new Date(b.getTime() + spanms * bringin);
							items = getItemsInRange(d1, bd2, photos, texts);
							if (items >= (photos_min + text_min + 20))
							{
								// move out the slider and reset d2
								d2 = bd2;
								second_slider = bringin;
								$("#graph_slider").slider({values:[first_slider, second_slider]});
								break;
							}
						}
					}
					else
					{
						// attempt to bring OUT slider 1
						var bringin = first_slider;
						while (1)
						{
							if (bringin == 0)
							{
								return false;
							}
							bringin -= 1;
							var bd1 = new Date(b.getTime() + spanms * bringin);
							items = getItemsInRange(bd1, d2, photos, texts);
							if (items >= (photos_min + text_min + 20))
							{
								// move out the slider and reset d1
								d1 = bd1;
								first_slider = bringin;
								$("#graph_slider").slider({values:[first_slider, second_slider]});
								break;
							}
						}
					}
				}
				else
				{
					// tighten up the slider that's not moving
					if (moving == 1)
					{
						// bring in slider 2
						var bringin = second_slider;
						while (1)
						{
							bringin -= 1;
							var bd2 = new Date(b.getTime() + spanms * bringin);
							items = getItemsInRange(d1, bd2, photos, texts);
							if (items >= (photos_min + text_min + 20))
							{
								// move in the slider and reset d2
								d2 = bd2;
								second_slider = bringin;
								$("#graph_slider").slider({values:[first_slider, second_slider]});
							}
							else
							{
								// all done bringing it in; time to break
								break;
							}
						}
					}
					else
					{
						// bring up slider 1
						var bringin = first_slider;
						while (1)
						{
							bringin += 1;
							var bd1 = new Date(b.getTime() + spanms * bringin);
							items = getItemsInRange(bd1, d2, photos, texts);
							if (items >= (photos_min + text_min + 20))
							{
								// move up the slider and reset d2
								d1 = bd1;
								first_slider = bringin;
								$("#graph_slider").slider({values:[first_slider, second_slider]});
							}
							else
							{
								// all done bringing it in; time to break
								break;
							}
						}
					}
				}
				_RANGE_BEGIN = d1;
				_RANGE_BEGIN_UNIT = first_slider;
				_RANGE_END = d2;
				_RANGE_END_UNIT = second_slider;
				$("#date_range_string").html(d1.toLocaleDateString() + " to " + d2.toLocaleDateString());
			}
		});
		//////////////////////////////////////////////////////////////////////////// setup graph object
		var specCtx;
		specCtx = Raphael(document.getElementById("graph"), canvas_width, canvas_height);
		var red = "rgb(53,145,199)";
		var red_svg = "#3581c7";
		var green = "rgb(185,215,76)";
		var green_svg = "#b9d74b";
		//////////////////////////////////////////////////////////////////////////// render the graph
		// photos
		for (var i = 0, j = photos.length; i < j; i++)
		{
			var tmsdiff = new Date(photos[i].date).getTime() - b.getTime();
			if (!pdArray[Math.floor(tmsdiff/spanms)])
			{
				pdArray[Math.floor(tmsdiff/spanms)] = 1;
			}
			else
			{
				pdArray[Math.floor(tmsdiff/spanms)] += 1;
			}
		}
		for (var i = 0, j = pdArray.length; i < j; i++)
		{
			// 4 pixels per unit, so MAXH units (700 px)
			var h = pdArray[i] || 0;
			if (h > MAXH) { h = MAXH; }
			if (h)
			{
				specCtx.rect(i * BAR_WIDTH*2, (canvas_height - h * HEIGHT_UNIT), BAR_WIDTH, h * HEIGHT_UNIT).attr({stroke: red_svg, fill: red_svg, opacity: 0.5, title: h + " photos from " + new Date(b.getTime() + spanms * i).toLocaleDateString() + " to " + new Date(b.getTime() + spanms * (i + 1)).toLocaleDateString()});
			}
		}
		specCtx.fillStyle = green;
		// texts
		for (var i = 0, j = texts.length; i < j; i++)
		{
			var tmsdiff = new Date(texts[i].date).getTime() - b.getTime();
			if (!tdArray[Math.floor(tmsdiff/spanms)])
			{
				tdArray[Math.floor(tmsdiff/spanms)] = 1;
			}
			else
			{
				tdArray[Math.floor(tmsdiff/spanms)] += 1;
			}
		}
		for (var i = 0, j = tdArray.length; i < j; i++)
		{
			// 4 pixels per unit, so MAXH units (700 px)
			var h = tdArray[i] || 0;
			if (h > MAXH) { h = MAXH; }
			if (h)
			{
				specCtx.rect(i * BAR_WIDTH*2 + BAR_WIDTH, (canvas_height - h * HEIGHT_UNIT), BAR_WIDTH, h * HEIGHT_UNIT).attr({stroke: green_svg, fill: green_svg, opacity: 0.5, title: h + " messages from " + new Date(b.getTime() + spanms * i).toLocaleDateString() + " to " + new Date(b.getTime() + spanms * (i + 1)).toLocaleDateString()});
			}
		}
		$("#date_range_string").html(new Date(b.getTime()).toLocaleDateString() + " to " + new Date(b.getTime() + spanms * (UNITS)).toLocaleDateString());
	}

	// generic graph api call; this actually has a little bit of mojo: we'll automatically take requests not supported by the graph api and
	// rewrite them as fql queries
	function getGraph(id, graphtype, successCallback, failureCallback, limit, since, debug)
	{
		if (!id) { id = 'me'; }
		if (!limit) { limit = 1000; }
		if (!since) { since = ''; }
		if (debug)
		{
			//LOG(0, 'getGraph', id, graphtype, successCallback);
		}
		if (graphtype == "comments")
		{
			// LOG(0, 'getGraph shunting comments to fql');
			getFQL("select xid, object_id, post_id, fromid, time, text, id, username, reply_xid from comment where object_id=" + id, function(response)
			{ 
				//LOG(0, "shunted!", response);
				successCallback({ data:response }); 
			});
		}
		else
		{
			FB.api('/' + id + '/' + graphtype, { limit: limit, since: since, metadata: '1' }, function(response)
			{
				if (debug)
				{
					//LOG(0, 'getGraph:responseCallback', response);
				}
				if (response.paging)
				{
					//LOG(0, 'getGraph:responseCallback: PAGING!  Here is the scoop', response.paging);
				}
				successCallback(response);
			});
		}
	}

	function getFQL(query, callback)
	{
		FB.api(
			{
				method: "fql.query",
				query: query
			},
			callback || function(response) { /* LOG(0, "getFQL", response); */ }
		);
	}

	function fbDisconnect(successCallback, failureCallaback)
	{
		FB.api({ method: 'Auth.revokeAuthorization' }, function(response)
		{
			successCallback();
		});
	}

	var opts =
	{
		scope: 'user_photo_video_tags,publish_stream,read_stream,user_photos'
	};
	function fbLogin(successCallback, failureCallback)
	{
		jotjournal.deleteCookie('sessionid');
		var x = jotjournal.getCookie("fbsr_", true, true);
		if (x && x[0])
		{
			jotjournal.deleteCookie([0]);
		}
		FB.login(
			function(response)
			{
				handleSessionResponse(response, successCallback, failureCallback);
			}, 
			opts
		);
	}

	function fbLogout(successCallback, failureCallback)
	{
		jotjournal.deleteCookie('sessionid');
		jotjournal.deleteCookie(jotjournal.getCookie("fbsr_", true, true)[0]);
		FB.logout(function(response)
		{ 
			handleSessionResponse(response, successCallback, failureCallback);
		});
	}

	// handle a session response from any of the auth related calls
	function handleSessionResponse(response, successCallback, logoutOrFailureCallback)
	{
		// if we dont have a session, just hide the user info
		if (!response.authResponse)
		{
			logoutOrFailureCallback();
			return;
		}

		// if we have a session, query for the user's profile picture and name
		getFQL('SELECT name, pic FROM profile WHERE id=' + FB.getAuthResponse().userID, function(response) { successCallback(response); });
	}

	var pageSuccessCallback = function() {};
	var pageFailureCallback = function() {};
	function registerLoginCallbacks(successCallback, failureCallback)
	{
		pageSuccessCallback = successCallback;
		pageFailureCallback = failureCallback;
	}

	function init()
	{
		if (window.FB)
		{
			// initialize the library with the API key
			FB.init({
				apiKey: FACEBOOK_API_KEY,
				appId: FACEBOOK_APP_ID,
				status: true,
				cookie: true,
				xfbml: true,
				oauth: true
			});

			// fetch the status on load
			FB.getLoginStatus(function(response){ handleSessionResponse(response, pageSuccessCallback, pageFailureCallback) });
		}
		status_messages = $("#status_messages");
	};

	function unload()
	{
		
	};

	return {init: init, unload: unload, getGraph: getGraph, handleSessionResponse: handleSessionResponse, getFQL: getFQL,
			fbDisconnect: fbDisconnect, fbLogin: fbLogin, fbLogout: fbLogout, registerLoginCallbacks: registerLoginCallbacks,
			makePhotosFromPhotosList: makePhotosFromPhotosList, getUserAlbumPhotos: getUserAlbumPhotos, groupEvents: groupEvents,
			scoreObj: scoreObj, gatherJournalAssets: gatherJournalAssets, _PHOTOS: _PHOTOS, _TEXTS: _TEXTS, setTemplate: setTemplate, sendJournal: sendJournal,
			getStatusUpdates: getStatusUpdates, toggleAggressiveTexts: toggleAggressiveTexts, dateSorter: dateSorter, journalToMake: journalToMake,
			toggleClientCulling: toggleClientCulling, setDateRangeAndContinue: setDateRangeAndContinue };
})();

$(document).ready(jotjournal.facebook.init);
$(window).unload(jotjournal.facebook.unload);
