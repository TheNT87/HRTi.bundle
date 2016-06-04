#Copyright NT
import inspect

TITLE = 'HRTi Plex'
ICON = 'icon-default.png'
URL = 'https://hrti.hrt.hr/'
LOGIN_URL = 'https://clientapi.hrt.hr/user/login/session_id/%s/format/json'
CLIENT_HOST = 'clientapi.hrt.hr'
SESSION_DATA_KEY = 'session_response'
LOGIN_DATA_KEY = 'login'

def Start():
	HTTP.ClearCache()
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
		Log.Info( Data.LoadObject(LOGIN_DATA_KEY) )
	Plugin.AddViewGroup("vod", viewMode='List', mediaType='items')
	
@handler('/video/hrti-%s' % Util.RandomInt(0,100), TITLE, thumb = ICON)
def MainMenu():
	#~ session_data = Data.LoadObject(SESSION_DATA_KEY)
	#~ 
	oc = ObjectContainer(
		objects = [
			DirectoryObject(key = Callback(VideoOnDemand), title = L('vod') )
		]
	)
	#~ for (k,v) in session_data['modules'].items():
		#~ oc.add(DirectoryObject( key = Callback(SecondMenu,value=v), title = k ))
		#~ 
	return oc
	
@route("video/hrti/vod")
def VideoOnDemand():
	oc = ObjectContainer()
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
	except:
		Log.Error('language_source not found')
	Dict[ MODULES_KEY ] = response[ MODULES_KEY ]
	Dict[ APPLICATION_ID_KEY ] = response[ APPLICATION_ID_KEY ]
	return response[ 'session_id' ]

def login(session_id):
	return

def debug(d):
	try:
		for k,v in d.items():
			Log.Info("%s: %s",k,v)
	except Exception:
		Log.Info("%s", inspect.getmembers( d ) )
	
