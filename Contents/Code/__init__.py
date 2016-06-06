#Copyright NT
import inspect

TITLE = 'HRTi Plex'
ICON = 'icon-default.png'
URL = 'https://hrti.hrt.hr/'
LOGIN_URL = 'https://clientapi.hrt.hr/user/login/session_id/%s/format/json'
CLIENT_HOST = 'clientapi.hrt.hr'
SESSION_DATA_KEY = 'session_response'
LOGIN_DATA_KEY = 'login'
SECURE_STREAMING_TOKEN_KEY = 'secure_streaming_token'

DEBUG_RANDOM = Util.RandomInt( 0,67 )

def Start():
	Log.Info( "starting plug-in" )
	ObjectContainer.title1 = TITLE
	DirectoryObject.thumb = R(ICON)
	if( Prefs['username'] == None or Prefs['password'] == None):
		raise ValueError('username and password required')
	if(not Data.Exists( LOGIN_DATA_KEY ) ):
		request = {"application_publication_id": "all_in_one"}
		request['uuid'] = identify( request )
		request.update({ "application_version":"1.1",
			"device_model_string_id":Platform.MachineIdentifier,
			"os":Platform.OS, "os_version":Platform.OSVersion, # evtl. Platform.CPU
			"screen_height":"1080", "screen_width":"1920"
		})
		login_request = HTTP.Request( LOGIN_URL % parse_session( request ),
			headers = REQUEST_HEADERS, data = '{"username":"%(username)s","password":"%(password)s"}' % Prefs
		)
		login_request.load()
		Data.SaveObject(LOGIN_DATA_KEY,JSON.ObjectFromString(login_request.content))
	login_data = Data.LoadObject( LOGIN_DATA_KEY )
	access_token = login_data[ SECURE_STREAMING_TOKEN_KEY ]
	expires = Datetime.FromTimestamp( float(access_token.split('/')[2]))
	Log.Info(access_token)
	if( expires < Datetime.Now() ):
		Log.Info('login has expired')
		debug( Data.LoadObject( SESSION_DATA_KEY ) )
	
	Plugin.AddViewGroup("vod", viewMode='List', mediaType='items')
	Log.Debug( "parsed start" )
	
@handler('/video/hrti', TITLE, thumb = ICON)
def MainMenu():
	oc = ObjectContainer(
		objects = [
			DirectoryObject(key = Callback(VideoOnDemand), title = L('vod') )
		], no_cache = True
	)
	return oc
	
@route("video/hrti/vod")
def VideoOnDemand():
	oc = ObjectContainer( no_cache = True)
	session_data = Data.LoadObject( SESSION_DATA_KEY )
	
	try:
		uri = Data.LoadObject( SESSION_DATA_KEY )['modules']['program_category']['uri']
		programm_list = XML.ElementFromURL( uri)
		for programm_category in programm_list.xpath( '//epg_program_category' ):
			oc.add( DirectoryObject( title = XML.StringFromElement( programm_category ) ) )
	except Exception as e:
		Log.Error('chaugth e')
	return oc

IDENTIFY_URL = 'https://clientapi.hrt.hr/client_api.php/config/identify/format/json'
REQUEST_HEADERS = {'Content-Type': 'application/json'}

def identify( request ):
	HTTP.Request( IDENTIFY_URL, method='OPTIONS' ).load()
	identity = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, data=JSON.StringFromObject(request) )
	identity.load()
	return JSON.ObjectFromString( identity.content )['uuid']
	
MODULES_KEY = 'modules'
APPLICATION_ID_KEY = 'application_id'
LANGUAGE_SOURCE_KEY = 'language_source'

def parse_session(request):
	request = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, method='PUT',
		data = JSON.StringFromObject( request )
	)
	request.load()
	response_content = request.content
	response = JSON.ObjectFromString( response_content )
	Log.Debug("got session response: %s", response_content )
	try:
		Data.SaveObject(LANGUAGE_SOURCE_KEY, XML.ElementFromURL( response[LANGUAGE_SOURCE_KEY] ) )
	except Exception as e:
		Log.Exception('chaugth e')
	Dict[ MODULES_KEY ] = response[ MODULES_KEY ]
	Dict[ APPLICATION_ID_KEY ] = response[ APPLICATION_ID_KEY ]
	return response[ 'session_id' ]

def login(session_id):
	return

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
	
