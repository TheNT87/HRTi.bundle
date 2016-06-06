#Copyright NT
import inspect

TITLE = 'HRTi Plex'
ICON = 'icon-default.png'
URL = 'https://hrti.hrt.hr/'
CLIENT_HOST = 'clientapi.hrt.hr'
LOGIN_DATA_KEY = 'login'

DEBUG_RANDOM = Util.RandomInt( 0,67 )

def Start():
	Log( "starting plug-in" )
	ObjectContainer.title1 = TITLE
	DirectoryObject.thumb = R(ICON)
	if( Prefs['username'] == None or Prefs['password'] == None):
		raise ValueError('username and password required')
	#~ if(not Data.Exists( LOGIN_DATA_KEY ) ):
		#~ request = {"application_publication_id": "all_in_one"}
		#~ request['uuid'] = identify( request )
		#~ request.update({ "application_version":"1.1",
			#~ "device_model_string_id":Platform.MachineIdentifier,
			#~ "os":Platform.OS, "os_version":Platform.OSVersion, # evtl. Platform.CPU
			#~ "screen_height":"1080", "screen_width":"1920"
		#~ })
		#~ login_request = HTTP.Request( LOGIN_URL % parse_session( request ),
			#~ headers = REQUEST_HEADERS, data = '{"username":"%(username)s","password":"%(password)s"}' % Prefs
		#~ )
		#~ login_request.load()
		#~ Data.SaveObject(LOGIN_DATA_KEY,JSON.ObjectFromString(login_request.content))
	Log("%s",login())
	login_data = Data.LoadObject( LOGIN_DATA_KEY )
	access_token = login_data[ SECURE_STREAMING_TOKEN_KEY ]
	expires = Datetime.FromTimestamp( float(access_token.split('/')[2]))
	Log.Info(access_token)
	if( expires < Datetime.Now() ):
		Log.Info('login has expired')
		session_data = Data.LoadObject( SESSION_DATA_KEY )
		Log.Debug("modules: %s", session_data["modules"].items() )
		Log.Debug("session data: %s", session_data.items() )
		Log.Debug("login data: %s", login_data.items() )
		for k,v in login_data['services'].items():
			if bool(v) :
				modules = session_data['modules']
				if k in modules:
					Log.Debug("module {0}: %s",k,modules[k].items())
		#debug(modules)
	
		
	Plugin.AddViewGroup("vod", viewMode='List', mediaType='items')
	Log.Debug( "parsed start" )
	
@handler('/video/hrti', TITLE, thumb = ICON)
def MainMenu():
	oc = ObjectContainer( header = 'loading', message='please wait ..',
		objects = [
			DirectoryObject(key = Callback(VideoOnDemand), title = L('vod') ),
			DirectoryObject(key = Callback(EPG), title = 'epg')
		], no_cache = True
	)
	return oc
	
@route("video/hrti/vod")
def VideoOnDemand():
	oc = ObjectContainer( no_cache = True, title2=L('vod'))
	session = Data.LoadObject( SESSION_DATA_KEY )
	uri = session['modules']['channel']['resources']['all']['uri'].format(application_id="all_in_one",language="hr" )
	channel_list = XML.ElementFromURL( uri )
	for channel in channel_list.xpath("//channel"):
		oc.add( DirectoryObject(
			title = channel.xpath("./name/text()")[0],
			thumb = Resource.ContentsOfURLWithFallback(channel.xpath("./img/text()")[0])
			#~ url = channel.xpath("./live_img/text()")[0],
			#~ summary = 'summary'
			
		))
	return oc

@route("video/hrti/epg")
def EPG():
	oc = ObjectContainer( no_cache = True)
	try:
		uri = Data.LoadObject( SESSION_DATA_KEY )['modules']['epg']['resources']['program_category']['uri']
		programm_list = XML.ElementFromURL( uri)
		for programm_category in programm_list.xpath( '//epg_program_category' ):
			oc.add( DirectoryObject(
				key = Callback(EPGCategory,id = programm_category.xpath('./id/text()')[0]),
				title = programm_category.xpath('./name/text()')[0] )
			)
	except Exception as e:
		Log.Error('chaugth e')
	return oc

@route("video/hrti/epg/{id}")
def EPGCategory(id):
	return ObjectContainer( no_cache = True)


def login():
	KEY = 'login'
	if( Data.Exists( KEY ) ):
		data = Data.LoadObject( KEY )
		access_token = data[ 'secure_streaming_token' ]
		expires = Datetime.FromTimestamp( float(access_token.split('/')[2]) )
		if( expires > Datetime.Now() ):
			return data
		URL = 'https://clientapi.hrt.hr/user/login/session_id/%(session_id)s/format/json'
		login_request = HTTP.Request( URL % parse_session( identify() ),
			headers = REQUEST_HEADERS, data = '{"username":"%(username)s","password":"%(password)s"}' % Prefs
		)
		login_request.load()
		Data.SaveObject(LOGIN_DATA_KEY,JSON.ObjectFromString(login_request.content))
	return Data.LoadObject( KEY )
	

	
MODULES_KEY = 'modules'
APPLICATION_ID_KEY = 'application_id'
LANGUAGE_SOURCE_KEY = 'language_source'

def session(request):
	KEY = 'session'
	request.update({ "application_version":"1.1",
		"device_model_string_id":Platform.MachineIdentifier,
		"os":Platform.OS, "os_version":Platform.OSVersion, # evtl. Platform.CPU
		"screen_height":"1080", "screen_width":"1920"
	})
	request = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, method='PUT',
		data = JSON.StringFromObject( request )
	)
	request.load()
	Data.SaveObject(KEY, JSON.ObjectFromString( request.content ) )
	#~ try:
		#~ Data.SaveObject(LANGUAGE_SOURCE_KEY, XML.ElementFromURL( response[LANGUAGE_SOURCE_KEY] ) )
	#~ except Exception as e:
		#~ Log.Exception('chaugth %s on saving language_source',e)
	#~ Dict[ MODULES_KEY ] = response[ MODULES_KEY ]
	#~ Dict[ APPLICATION_ID_KEY ] = response[ APPLICATION_ID_KEY ]
	return Data.LoadObject( KEY )

IDENTIFY_URL = 'https://clientapi.hrt.hr/client_api.php/config/identify/format/json'
REQUEST_HEADERS = {'Content-Type': 'application/json'}

def identify():
	request = {"application_publication_id": "all_in_one"}
	HTTP.Request( IDENTIFY_URL, method='OPTIONS' ).load()
	identity = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, data=JSON.StringFromObject(request) )
	identity.load()
	request['uuid'] = JSON.ObjectFromString( identity.content )['uuid']
	return request

def debug(d):
	try:
		for k,v in d.items():
			if k == 'modules':
				for km,vm in v.items():
					Log.Info("%s: %s",km,vm)
			else:
				Log.Info("%s: %s",k,v)
	except Exception:
		Log.Info("%s", inspect.getmembers( d ) )
	
