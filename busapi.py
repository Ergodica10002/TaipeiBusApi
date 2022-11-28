from argparse import ArgumentParser, Namespace
from requests import get, post
import urllib.parse


app_id = 'xxxxxx-xxxxxxxx-xxxx-xxxx'
app_key = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
base_url = "https://tdx.transportdata.tw/api/basic/"
Route_url = "v2/Bus/Route/City/{City}?"
EstimatedTimeOfArrival_url = "v2/Bus/EstimatedTimeOfArrival/City/{City}?"

stopstatus = {
	0 : '正常',
	1 : '尚未發車',
	2 : '交管不停靠',
	3 : '末班車已過',
	4 : '今日未營運'
}

def get_auth_header(app_id = app_id, app_key = app_key):
	content_type = 'application/x-www-form-urlencoded'
	grant_type = 'client_credentials'
	return {
		'content-type' : content_type,
		'grant_type' : grant_type,
		'client_id' : app_id,
		'client_secret' : app_key
	}

def get_data_header(access_token):
	return {
		'authorization': 'Bearer ' + access_token
	}

def get_query_params(topint = 20, formatstr = 'JSON', orderbystr = '', filterstr = ''):
	return urllib.parse.urlencode({
				'$top' : topint,
				'$filter' : filterstr,
				'$orderby' : orderbystr,
				'$format' : formatstr
			})

def get_estimated_time(args):
	routes = args.routes.split(',')
	if args.city == 'Both':
		cities = ['Taipei', 'NewTaipei']
	else:
		cities = [args.city]
	stop = args.stop
	routestr = " or ".join([f"RouteName/Zh_tw eq '{route}'" for route in routes])

# Get Authentication Token
	auth_response = post(auth_url, get_auth_header(app_id, app_key))
	if not auth_response:
		print("Authentication Error")
		print(data_response.text)
		return
	auth_json = auth_response.json()
	access_token = auth_json['access_token']

	message = ''
	for city in cities:
		# Get Routes Direction
		filterstr = f"({routestr})"
		params = get_query_params(orderbystr = 'RouteName/Zh_tw', filterstr = filterstr)
		url = base_url + Route_url.format(City = city) + params
		data_response = get(url, headers = get_data_header(access_token))
		if not data_response:
			print("Data Error")
			print(data_response.text)
			return
		data_json = data_response.json()
		route_direction = {}
		for data in data_json:
			route_direction[data["RouteName"]["Zh_tw"]] = (data["DestinationStopNameZh"], data["DepartureStopNameZh"])

		# Get Estimated Arrival Time
		filterstr = f"contains(StopName/Zh_tw, '{stop}') and ({routestr})"
		params = get_query_params(orderbystr = 'RouteName/Zh_tw,StopName/Zh_tw', filterstr = filterstr)
		url = base_url + EstimatedTimeOfArrival_url.format(City = city) + params
		data_response = get(url, headers = get_data_header(access_token))
		if not data_response:
			print("Data Error")
			print(data_response.text)
			return
		data_json = data_response.json()
		for data in data_json:
			stopnamestr = f"Stop: {data['StopName']['Zh_tw']}"
			routenamestr = f"Route: {data['RouteName']['Zh_tw']}"
			if data['RouteName']['Zh_tw'] in route_direction.keys():
				directionstr = f"Direction: To {route_direction[data['RouteName']['Zh_tw']][data['Direction']]}"
			else:
				directionstr = f"Direction: {data['Direction']}"
			if 'EstimateTime' in data.keys():
				estimatetimestr = f"EstimateTime(s): {data.get('EstimateTime')}"
			else:
				estimatetimestr = f"EstimateTime(s): {stopstatus[data['StopStatus']]}"
			T_idx, add_idx = data['UpdateTime'].find('T'), data['UpdateTime'].find('+')
			updatetimestr = f"Update: {data['UpdateTime'][T_idx+1: add_idx]}"
			# print(' '.join([stopnamestr, routenamestr, directionstr, estimatetimestr, updatetimestr]))
			print("{:<15} {:<12} {:<20} {:<22} {:<20}".format(stopnamestr, routenamestr, directionstr, estimatetimestr, updatetimestr))
			message += "{:<15} {:<12} {:<20} {:<22} {:<20}".format(stopnamestr, routenamestr, directionstr, estimatetimestr, updatetimestr) + '\n'

	return message

def parse_args() -> Namespace:
	parser = ArgumentParser()
	parser.add_argument(
		"--city",
		type = str,
		help = "City Name ('Taipei', 'NewTaipei', or 'Both'). Default = 'Both'.",
		default = 'Both'
	)
	parser.add_argument(
		"--routes",
		type = str,
		help = "Bus Routes (separated by ','). Default = '905,906,909'.",
		default = '905,906,909'
	)
	parser.add_argument(
		"--stop",
		type = str,
		help = "Search Substring for Bus Stop. Default = '中正環河路口'.",
		default = '中正環河路口'
	)
	args = parser.parse_args()
	return args

if __name__ == '__main__':
	args = parse_args()
	message = get_estimated_time(args)
	# print(message)