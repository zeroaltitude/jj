jotjournal.events = (function()
{
	/* 
		Temporal event clustering

		These calculations are based on this whitepaper: http://portal.acm.org/citation.cfm?id=957093 
		(also http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.89.5304&rep=rep1&type=pdf)
		I deviate from the final step by simply merging all found boundary lists and "over segmenting" 
		the image collection, which suits my purposes just fine (i.e. I don't perform the
		confidence score calculation).
	*/

	/* ************************************************************************** SETUP */
	var _events_cache = [];
	var testEvents = [];
	var numPhotos = 15; // per event
	var timeBase = new Date().getTime(); // now in epoch seconds
	var eventsBase = 1000000 * 1000; // 12 days or so, milliseconds
	/* 
		Group the events so that we get some natural boundaries between clusters
	*/
	var events = [Math.floor(eventsBase/16),Math.floor(eventsBase/8),
				  Math.floor(eventsBase/4), Math.floor(eventsBase/2),
				  (eventsBase), 			(2 * eventsBase),
				  (4 * eventsBase), 		(8 * eventsBase)];
	/*
		Create a bunch of randomized test events across those clusters
	*/
	for (var z = 0, y = events.length; z < y; z++)
	{
		var T = events[z];
		for (var i = 0; i < numPhotos; i++)
		{
			var t = Math.floor(T * Math.random());
			// timebase is in seconds:
			testEvents.push(timeBase - T + t);
		}
	}
	/*
		In temporal order, ascending
	*/
	testEvents.sort();

	function facebookDateToJsDate(fbdate)
	{
		// 2007-11-28T23:24:44+0000
		var datetime = fbdate.split('T');
		var ymd = datetime[0].split('-');
		var timestring = datetime[1].split('+')[0];
		return new Date(ymd[1] + '/' + ymd[2] + '/' + ymd[0] + ' ' + timestring);
	}

	/* ************************************************************************** RUN THIS FUNCTION TO MAKE THINGS HAPPEN */
	function calculate(events)
	{
		/* takes a list of events and returns the boundaries in time -- partitions the events into clusters */
		if (events) { events.sort(); }
		_events_cache.push(events = (events || testEvents));
		temporalSimilarity(events);
		similarityNovelty(events);
		boundaries(novelties, events);
		_flattened_boundaries.sort(sorter);
		return _flattened_boundaries;
	}

	/* ************************************************************************** EQUATIONS */
	var temporalSimilarityArray = [];
	var K = [10000, 1000, 100]; // minutes
	function temporalSimilarity(events)
	{
		var len = events.length;
		for (var h = 0, g = K.length; h < g; h++)
		{
			var k = K[h];
			temporalSimilarityArray.push([]);
			var workingWith = temporalSimilarityArray[h];
			for (var i = 0; i < len; i++)
			{
				workingWith.push([]);
				var workingWithInner = workingWith[i];
				for (var j = 0; j < len; j++)
				{
					var foo = Math.exp(0 - (Math.abs(events[i] - events[j])/(k * 60 * 1000)));
					workingWithInner.push(foo);
				}
			}
		}
	}

	function checkerboard(val, x, y)
	{
		if ((x > 0) && (y <= 0))
		{
			// 5, -5
			return 0 - val;
		}
		else if ((x >= 0) && (y > 0))
		{
			// 5, 5
			return val;
		}
		else if ((x < 0) && (y >= 0))
		{
			// -5, 5
			return 0 - val;
		}
		else if ((x <= 0) && (y < 0))
		{
			// -5, -5
			return val;
		}
		else
		{
			// 0, 0
			return 0;
		}
	}

	// http://en.wikipedia.org/wiki/Gaussian_function
	function gaus(x, y)
	{
		var A = 1; // magnitude
		var x0 = 0; // xcoord of the gaussian's center
		var y0 = 0; // ycoord
		var a = .5; // relatum for rotating the gaussian (and giving it an elliptical shape)
		var b = 0; // as a
		var c = .5; // as a
		var expo = (a * Math.pow((x - x0), 2)) + (2 * b * ((x - x0) * (y - y0))) + (c * Math.pow((y - y0), 2));
		return A * Math.exp(0 - expo);
	}

	function sum(list)
	{
		var sum = 0;
		for (var i = 0, j = list.length; i < j; i++)
		{
			sum += list[i];
		}
		return sum;
	}

	function mean(list)
	{
		return sum(list)/list.length;
	}

	function deviations(list)
	{
		var _mean = mean(list);
		var devs = [];
		for (var i = 0, j = list.length; i < j; i++)
		{
			devs.push(list[i] - _mean);
		}
		return devs;
	}

	function stddev(list)
	{
		var devs = deviations(list);
		var sumsq = 0;
		for (var i = 0, j = devs.length; i < j; i++)
		{
			sumsq += (devs[i] * devs[i]);
		}
		return Math.sqrt(sumsq/(j - 1));
	}

	var novelties = [];
	function similarityNovelty(events)
	{
		var z = 11;
		for (var h = 0, g = K.length; h < g; h++)
		{
			var sim = temporalSimilarityArray[h];
			novelties.push([]);
			var workingWith = novelties[h];
			var sum = 0;
			for (var i = 0, j = events.length; i < j; i++)
			{
				sum = 0;
				for (var l = -5; (l + 5) < z; l++)
				{
					for (var m = -5; (m + 5) < z; m++)
					{
						if (((i + l) >= 0) && ((i + m) >= 0))
						{
							var xsim = sim[i + l];
							var val = (xsim !== undefined) ? ((xsim[i + m] !== undefined) ? xsim[i + m] : 0) : 0;
							var cb = checkerboard(gaus(l, m), l, m);
							sum += (val * cb);
						}
					}
				}
				workingWith.push(sum);
			}
		}
	}

	/* the boundaries represent LEADING boundaries; i.e. a date boundary entered here is the first event in a new series of grouped events */
	var _boundaries = [];
	var _flattened_boundaries = [];
	/*
		Using first order differences in the series of novelties:
			* define: A peak is a local maximum that is greater than 1 stddev bigger than a subsequent decline/steady-er
					if the first order difference is negative, and a local maximum wasn't already set, set the local maximum to
					this one
			* accept only boundaries that themselves show the >1stddev dropoff (no steady declines, and local peaks less relevant)
			* When there is an increaser, reset local_maximum to 0
			* Each local maximum gets a 1 in boundaries -- everything else gets a 0

		FORCE FEED HEURISTIC OVERRIDE: (this is crude but seems to work better for facebook-y photos -- we could remove the 2 day clamp to experiment 
										with finding smaller events, but the big clamp helps a lot with strings of very far-apart things that get progressively
										higher/same novelty scores and act as peak-plateaus that don't get individual boundaries in this algo)
			* if two dates are on the same 2 day period, they're not a boundary
			* if two dates are more than 10 days apart, they're a boundary
	*/
	var clamp = 60 * 60 * 24 * 2 * 1000;
	var split = 60 * 60 * 24 * 10 * 1000;
	function dateNotInArray(arr, el)
	{
		for (var i = 0, j = arr.length; i < j; i++)
		{
			if (arr[i].getTime() == el.getTime())
			{
				return false;
			}
		}
		// LOG(0, "is not in array", el);
		return true;
	}

	function boundaries(nov, events)
	{
		for (var i = 0, j = K.length; i < j; i++)
		{
			_boundaries.push([]);
			var workingWith = _boundaries[i];
			var workingWithN = nov[i];
			var std_dev = stddev(workingWithN);

			var local_maximum_value = -1;
			var local_maximum_index = -1;

			for (var k = 0, l = workingWithN.length; k < (l - 1); k++)
			{
				var is_boundary = 0;
				var fodiff = workingWithN[k + 1] - workingWithN[k];
				if (fodiff > 0)
				{
					local_maximum_value = -1;
					local_maximum_index = -1;
				}
				else
				{
					if ((local_maximum_index == -1) && (fodiff < 0))
					{
						local_maximum_value = workingWithN[k];
						local_maximum_index = k;
					}

					var ts1 = events[k];
					var ts0 = events[k - 1];
					var override_together = false;
					var override_apart = false;
					if ((ts1 - ts0) < clamp)
					{
						override_together = true;
					}
					else if ((ts1 - ts0) > split)
					{
						override_apart = true;
					}

					if (!override_together && (((0 - fodiff) > std_dev) || override_apart))
					{
						is_boundary = 1;
						var de = new Date(events[k]);
						workingWith.push({ 'index': k, 'date': de});
						if (dateNotInArray(_flattened_boundaries, de))
						{
							_flattened_boundaries.push(de);
						}
					}
				}
			}
		}
	}

	function sorter(a, b)
	{
		if (a > b) { return 1; }
		else if (a < b) { return -1; }
		else { return 0; }
	}

	/* ************************************************************************** LOGGING */
	function reportNovelties(index)
	{
		var d = new Date(_events_cache[0][index]);
		var simstring = ' (';
		for (var i = 0; i < 3; i++)
		{
			for (var j = -5; j < 6; j++)
			{
				simstring += temporalSimilarityArray[i][index][index + j] + ':';
			}
			simstring += '//';
		}
		console.log(d + ':' + novelties[0][index] + '/' + novelties[1][index] + '/' + novelties[2][index] + simstring);
	}

	/* ************************************************************************** PUBLIC INTERFACE TO OUR OBJECT */
	return { temporalSimilarityArray: temporalSimilarityArray, novelties: novelties, 
			 testEvents: testEvents, calculate: calculate, events: events,
			 novelties: novelties, _boundaries: _boundaries, _flattened_boundaries: _flattened_boundaries, 
			 _events_cache: _events_cache, facebookDateToJsDate: facebookDateToJsDate, reportNovelties: reportNovelties,
			 gaus: gaus };
})();

