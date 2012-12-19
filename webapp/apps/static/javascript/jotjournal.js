/**
 * The "bind()" function extension from Prototype.js, extracted for general use
 *
 * @author Richard Harrison, http://www.pluggable.co.uk
 * @author Sam Stephenson (Modified from Prototype Javascript framework)
 * @license MIT-style license @see http://www.prototypejs.org/
 */

Function.prototype.bind = function()
{
    var _$A = function(a)
    {
        return Array.prototype.slice.call(a);
    };
    if ((arguments.length < 2) && (typeof arguments[0] == "undefined"))
    {
        return this;
    }
    var __method = this, args = _$A(arguments), object = args.shift();
    return function()
    {
        return __method.apply(object, args.concat(_$A(arguments)));
    };
};

var BLOCK_PARSE_REGEX = /\$\{(\w+)\}/igm;
String.prototype.parse_vars = function(dataDict)
{
        return this.replace(BLOCK_PARSE_REGEX, function(match, param, offset, orig)
        {
                if (!dataDict) { return ""; }
                return (dataDict[param] || (dataDict[param] == 0)) ? (dataDict[param]) : ("");
        });
};

// console output
if (!window.console)
{
	window.console =
	{
		log: function(message)
		{
			// alert(message);
		}
	};
}
var LOGLEVEL = 0; // everything
function LOG()
{
	var level = arguments[0];
	if (level >= LOGLEVEL)
	{
		for (var i = 1, j = arguments.length; i < j; i++)
		{
			window.console.log(arguments[i]);
		}
	}
}

// detect whether __proto__ is supported in this browser
var __proto_supported__ = false;
try
{
	__proto_supported__ = ({}).__proto__;
} catch (e) { /* failed, so stays false */ }

if (typeof Object.create !== 'function')
{
	Object.create = function(o)
	{
		// this could be further modified to support ECMAScript 5 strict mode:
		function F() { if (!__proto_supported__) { this.__proto__ = arguments.callee.prototype; } }
		F.prototype = o;
		return new F();
	};
}

if (typeof Object.prototype.hasancestor !== 'function')
{
	Object.prototype.hasancestor = function(o)
	{
		if (this === o) { return true; }
		else if (!this.__proto__ || !o) { return false; }
		return this.__proto__.hasancestor(o);
	};
 	// jQuery hypersafety (this is why we can't have nice things: jquery uses the "wisdom" of not checking hasOwnProperty, even in its trivial form):
	Object.prototype.hasancestor.exec = function()
	{
		return null;
	};
	Object.prototype.hasancestor.replace = function()
	{
		return null;
	};
	Object.prototype.hasancestor.test = function()
	{
		return null;
	};
}

var jotjournal = (function()
{
	function DEVELOPMENT()
	{
		if ((document.location.href.indexOf('staging') != -1) || (document.location.href.indexOf('.me') != -1))
		{
			return true;
		}
		return false;
	}

	function ajax(url, data, callback)
	{
		return $.ajax({
			type: "POST",
			url: url,
			data: data, // obj key: value, key: value...
			complete: callback
		});
	}

	/* cookie functions: http://techpatterns.com/downloads/javascript_cookies.php */
	function setCookie(name, value, expires, path, domain, secure)
	{
		// set time, it's in milliseconds
		var today = new Date();
		today.setTime(today.getTime());

		// EdA: override this to default to base path instead of "" (easier for simplistic auth systems)
		path = path || "/";

		/*
		    {expires} days
		*/
		if (expires)
		{
			expires = expires * 1000 * 60 * 60 * 24;
		}
		var expires_date = new Date(today.getTime() + (expires));
		document.cookie = name + "=" + escape(value) +
			((expires) ? ";expires=" + expires_date.toGMTString() : "") +
			((path) ? ";path=" + path : "") +
			((domain) ? ";domain=" + domain : "") +
			((secure) ? ";secure" : "" );
	}

	function getCookie(name, startsWith, getName)
	{
		// first we'll split this cookie up into name/value pairs
		// note: document.cookie only returns name=value, not the other components
		var a_all_cookies = document.cookie.split(';');
		var a_temp_cookie = '';
		var cookie_name = '';
		var cookie_value = '';
		var b_cookie_found = false; // set boolean t/f default f

		for (var i = 0; i < a_all_cookies.length; i++)
		{
			// now we'll split apart each name=value pair
			a_temp_cookie = a_all_cookies[i].split('=');

			// and trim left/right whitespace while we're at it
			cookie_name = a_temp_cookie[0].replace(/^\s+|\s+$/g, '');

			// if the extracted name matches passed name
			if ((cookie_name == name) || (startsWith && (cookie_name.indexOf(name) == 0)))
			{
				b_cookie_found = true;
				// we need to handle case where cookie has no value but exists (no = sign, that is):
				if (a_temp_cookie.length > 1)
				{
					cookie_value = unescape(a_temp_cookie[1].replace(/^\s+|\s+$/g, ''));
				}
				// note that in cases where cookie is initialized but no value, null is returned
				if (getName)
				{
					return [cookie_name, cookie_value];
				}
				return cookie_value;
			}
		}
		if (!b_cookie_found)
		{
			return null;
		}
	}

	function deleteCookie(name, path, domain)
	{
		if (this.getCookie(name))
		{
			// EdA: override this to default to base path instead of "" (easier for simplistic auth systems)
			path = path || "/";
			document.cookie = name + "=" +
				((path) ? ";path=" + path : "") +
				((domain) ? ";domain=" + domain : "" ) +
				";expires=Thu, 01-Jan-1970 00:00:01 GMT";
		}
	}

	function getQueryParam(paramname, def, url)
	{
		var ret = def || null;
		url = url || document.location.href;
		if (url)
		{
			if (url.indexOf('?') > -1)
			{
				var qp = url.substring(url.indexOf('?') + 1);
				var qpvs = qp.split(/&/);
				for (var i = 0, j = qpvs.length; i < j; i++)
				{
					if (qpvs[i] && (qpvs[i].indexOf('=') > -1))
					{
						var kv = qpvs[i].split(/=/);
						if (kv[0] && (kv[0] == paramname))
						{
							ret = kv[1];
							break;
						}
					}
				}
			}
		}
		return ret;
	}

	function init()
	{

	}

	function unload()
	{

	}
	return { init: init, unload: unload, ajax: ajax, getQueryParam: getQueryParam, getCookie: getCookie, setCookie: setCookie, deleteCookie: deleteCookie, DEVELOPMENT: DEVELOPMENT };
})();

$(document).ready(jotjournal.init);
$(window).unload(jotjournal.unload);


// quick test
var test_ancestors = function()
{
	var x = {'a':'b'};
	var y = Object.create(x);
	if (!y.hasancestor(x)) { alert('failed'); }
	if (!y.hasancestor(y)) { alert('failed'); }
	if (y.hasancestor(new Object())) { alert('failed'); }
	var a = Object.create(y);
	if (!a.hasancestor(y)) { alert('failed'); }
	if (!a.hasancestor(x)) { alert('failed'); }
	var z = {'a':'b'};
	if (y.hasancestor(z)) { alert('failed'); }
	if (z.hasancestor(y)) { alert('failed'); }
};

