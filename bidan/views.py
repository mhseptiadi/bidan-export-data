from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from polls.models import Question
from django.core.urlresolvers import reverse
from django.views import generic
import urllib2, base64, json
import socket
import xlwt
import json
import inflection
import sys
from datetime import datetime 
from .models import Response

# set timeout
# timeout in seconds
timeout = 10000
socket.setdefaulttimeout(timeout)

URL = "http://118.91.130.18:9979"
USERLOGIN = "demo1"
PASSWORDLOGIN = "1"

USERGROUP1 = ['user1', 'user2', 'user3', 'user4', 'user5', 'user6', 'user8']
USERGROUP2 = ['user9', 'user10', 'user11', 'user12', 'user13', 'user14']

# set xls style
style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on; borders: top medium, bottom medium, left medium, right medium;',
    num_format_str='#,##0.00')

style1= xlwt.easyxf('font: name Times New Roman, color-index black, bold off; borders: top thin, bottom thin, left thin, right thin;',
    num_format_str='#,##0.00')

def get_width(num_characters):
    return int((1+num_characters) * 256)

def index(request):
	context = {'title' : "Hello World", 'users1' : USERGROUP1, 'users2' : USERGROUP2}
	return render(request, 'bidan/index.html', context)

def get(request):
	username = request.POST["username"]
	batchSize = request.POST["batch_size"]
	batchSizeString = ""
	arguments = ""

	if batchSize :
		batchSizeString = "&batch-size="+batchSize
	listResponse = []
	listUser = []
	listUser.extend(request.POST.getlist('users[]'))

	if username.strip():
		listUser.append(username)

	if not listUser :
		return render(request, 'bidan/index.html', {'error_message' : "No user selected", 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

	for user in listUser:
		apiUrl = URL + "/form-submissions?anm-id="+user+"&timestamp=0"+batchSizeString
		listResponse.append(fetch(USERLOGIN, PASSWORDLOGIN, apiUrl, user))

	for obj in listResponse :
		arguments+=str(obj[0].id) + "/"
	arguments = arguments[:-1]
	return HttpResponseRedirect(reverse('bidan:result', args=(arguments,)))

def get_all(request):
	batchSize = request.POST["batch_size"]
	apiUrl = URL + "/all-form-submissions?timestamp=0&batch-size="+batchSize
	responses = fetch(USERLOGIN, PASSWORDLOGIN, apiUrl, "all")
	return HttpResponseRedirect(reverse('bidan:result_all', args=(responses[0].id,)))

def fetch(username, password, url, dataname):
	try:
		req = urllib2.Request(url)
		base64String = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
		req.add_header("Authorization", "Basic %s" % base64String)
		result = urllib2.urlopen(req)
		result_json = json.load(result.fp)
		result.close()
		responses = Response.objects.update_or_create(response_username=dataname,defaults=dict(response_text=json.dumps(result_json),response_password=password))
		return responses
	except (socket.timeout, urllib2.HTTPError) as e:
		# return HttpResponse("Error: %s" % e)
		# Redisplay the question voting form.
		return render(request, 'bidan/index.html', {'error_message' : e, 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

def result(request, response_id):
	pieces = response_id.split('/')
	xlsfile = []
	xlsfiles = ""
	for piece in pieces:
		response = get_object_or_404(Response, pk=piece)
		xlsfile.append(response)
		xlsfiles += str(response.id) + "/"

	xlsfiles = xlsfiles[:-1]
	context = {'xlsfile' : xlsfile, 'xlsfiles' : xlsfiles, 'users1' : USERGROUP1, 'users2' : USERGROUP2 }
	return render(request, 'bidan/index.html', context)

def result_all(request, response_id):
	xlsfile = get_object_or_404(Response, pk=response_id)
	context = {'allxlsfile' : xlsfile, 'users1' : USERGROUP1, 'users2' : USERGROUP2 }
	return render(request, 'bidan/index.html', context)

def download_all(request, responses_id):
	formNames = {}
	userid = responses_id.split("/")
	xlsfile = []

	for uid in userid :
		_object = get_object_or_404(Response, pk=uid)
		xlsfile.append(_object)
		result_json = json.loads(_object.response_text)
		for row in result_json:
			if not row["formName"] in formNames:
				formNames[row["formName"]] = []
			jsondata = (json.loads(row["formInstance"]))
			jsonfield = []
			jsonfield.append({'name' : "User ID", 'value' : row["anmId"]})
			jsonfield.extend(jsondata["form"]["fields"])
			jsonfield.append({'name' : "clientVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["clientVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
			jsonfield.append({'name' : "serverVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["serverVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
			formNames[row["formName"]].append(jsonfield)

	xlsname = ""
	for xls in xlsfile :
		xlsname += xls.response_username + "+"
	xlsname = xlsname[:-1]
	xlsname += ".xls"

	return xls_to_response(make_xls(formNames), xlsname)	

def download(request, response_id):
	formNames = {}
	wb = xlwt.Workbook()
	xlsfile = get_object_or_404(Response, pk=response_id)
	jsonData = json.loads(xlsfile.response_text)

	for row in jsonData:
		if not row["formName"] in formNames:
			formNames[row["formName"]] = []
		jsondata = (json.loads(row["formInstance"]))
		jsonfield = []
		jsonfield.append({'name' : "User ID", 'value' : row["anmId"]})
		jsonfield.extend(jsondata["form"]["fields"])
		jsonfield.append({'name' : "clientVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["clientVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		jsonfield.append({'name' : "serverVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["serverVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		formNames[row["formName"]].append(jsonfield)

	return xls_to_response(make_xls(formNames), xlsfile.response_username+'.xls')	

def make_xls(formNames):
	wb = xlwt.Workbook()

	for sheet in formNames:
		# create worksheet
		worksheetTitle = sheet[0:30]
		wa = wb.add_sheet(inflection.humanize(worksheetTitle))
		num_width = 0
		titleArray = []
		formData = []
		
		# put the json data to array
		for idx1, data1 in enumerate(formNames[sheet]):
			formData.append([])
			formData[idx1] = {}
			for idx2, data2 in enumerate(data1):
				if not data2['name'] in titleArray:
					titleArray.insert(idx2, data2['name'])
				value = data2.get('value')
				if value is None:
					value = '-'
				formData[idx1][data2['name']] = value

		# write al data to worksheet
		for idx1, data1 in enumerate(formData):
			for idx2, data2 in enumerate(titleArray):
				if idx1 == 0:
					wa.write(0, idx2, inflection.titleize(data2), style0)
				if data2 in data1:
					value = data1[data2]
					wa.col(idx2).width = get_width(len(value)) if get_width(len(value)) > wa.col(idx2).width else wa.col(idx2).width
					wa.write(idx1+1, idx2, inflection.humanize(value), style1)
				else:
					wa.write(idx1+1, idx2, '-', style1)

	return wb

def xls_to_response(xls, fname):
    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

