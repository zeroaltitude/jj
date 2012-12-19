jotjournal.commands = (function()
{
	var PAGE_ID = "#page_${page_number}";
	var PAGE_CLASS = ".page_${page_number}";
	var QUADRANT_CLASS = ".quadrant";
	var IMAGE_CLASS = ".photo";
	var QUADRANT_ID = "#quadrant_${rectId}";
	var IMAGE_ID = "#photo_${myId}";
	var TEXT_ID = "#message_${myId}";

	var QUAD_TEMPL = "<div id='quadrant_${rectId}' class='quadrant'></div>";
	var PHOTO_TEMPL = "<img border='0' id='photo_${myId}' src='${url}' class='photo' />"
	var TEXT_TEMPL = "<table class='idiocy'><tr><td id='quadrant_inner_${rectId}'><div id='message_${myId}' class='message'>${content}</div></td></tr></table>";
	var TEXT_FRAG_TEMPL = "<div id='message_${myId}' class='message_fragment'>${content}</div>";

	function drawRect(page, rectId)
	{
		//LOG(0, 'drawRect', page, rectId);
		$(PAGE_ID.parse_vars({page_number:page})).append(QUAD_TEMPL.parse_vars({rectId:rectId}));
	}

	function drawText(rectId, myId, content, contentType)
	{
		//LOG(0, 'drawText', rectId, myId, content);
		$(QUADRANT_ID.parse_vars({rectId:rectId})).append(TEXT_TEMPL.parse_vars({myId:myId, rectId:rectId, content:content}));
	}

	function drawTextFragment(rectId, myId, content, contentType)
	{
		//LOG(0, 'drawText', rectId, myId, content);
		$(QUADRANT_ID.parse_vars({rectId:rectId})).append(TEXT_FRAG_TEMPL.parse_vars({myId:myId, rectId:rectId, content:content}));
	}

	function drawImageFloatingInRect(rectId, myId, url)
	{
		//LOG(0, 'drawImageFloatingInRect', rectId, myId, url);
		$(QUADRANT_ID.parse_vars({rectId:rectId})).append(PHOTO_TEMPL.parse_vars({myId:myId, url:url}));
	}

	function runCommand(page_number, commandArr)
	{
		var ca = Array.prototype.slice.call(commandArr);
		var command = ca.shift();
		switch(command)
		{
			case 'drawRect':
				ca.unshift(page_number);
				return drawRect.apply(this, ca);
				break;
			case 'drawText':
				return drawText.apply(this, ca);
				break;
			case 'drawTextFragment':
				return drawTextFragment.apply(this, ca);
				break;
			case 'drawImageFloatingInRect':
				return drawImageFloatingInRect.apply(this, ca);
				break;
			default:
				//LOG(0, "runCommand hit default case in error: " + command + '(' + page_number + ')');
				break;
		}
	}

	function scanTextSizes(page1, page2)
	{
		var messages = $("#page_" + page1 + " .message, #page_" + page2 + " .message");
		for (var i = 0, j = messages.length; i < j; i++)
		{
			var m = $(messages[i]);
			var height = m.height();
			var superparent = m.parents(".quadrant");
			var parentheight = superparent.height();
			//LOG(0, m[0].id + "/" + superparent[0].id + "/" + height + "/" + parentheight);
			if (height > parentheight)
			{
				m.css("font-size", "8px");
			}
		}
	}

	function runCommands(commands)
	{
		var pages = commands.pages;
		for (var i = 0, j = pages.length; i < j; i++)
		{
			var that = pages[i];
			var page_number = that.page_number;
			var layers = [that.layer0, that.layer1, that.layer2];
			for (var x = 0, y = layers.length; x < y; x++)
			{
				for (var k = 0, l = layers[x].length; k < l; k++)
				{
					runCommand(page_number, layers[x][k]);
				}
			}
		}
	}

	return {runCommands: runCommands, scanTextSizes: scanTextSizes};
})();
