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
# from datetime import date, timedelta 
import dateutil.relativedelta
from .models import Response

# set timeout
# timeout in seconds
timeout = 10000
socket.setdefaulttimeout(timeout)

URL = "http://13.229.79.91:9080/opensrp/"
USERLOGIN = "antaravato1"
PASSWORDLOGIN = "Mahery123"

USERGROUP1 = ['Antaravato', 'Maintambato']
USERGROUP2 = ['Vinanibe','Marofototra']

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
	date = request.POST["date"]
	if date == "" : 
		# today = datetime.date.today()
		# first = today.replace(day=1)
		# lastMonth = first - datetime.timedelta(days=1)
		# date = lastMonth.strftime("%d/%m/%Y")
		now = datetime.datetime.now()
		lastMonth = now + dateutil.relativedelta.relativedelta(months=-1)
		date = lastMonth.strftime("%d/%m/%Y")


	timestamp = time.mktime(datetime.datetime.strptime(date, "%d/%m/%Y").timetuple())

	return HttpResponse("{\"test\":"+lastMonth+" | "+timestamp+"}", content_type="application/json")

	# batchSize = "500"
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
		return render(request, 'bidan/index.html', {'error_message' : "No location selected", 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

	for user in listUser:
		apiUrl = URL + "/form-submissions-by-loc?locationId="+user+"&timestamp=0"+batchSizeString
		result = fetch(request,USERLOGIN, PASSWORDLOGIN, apiUrl, user)
		if result["responses"] is not None :
			listResponse.append(result["responses"])
		elif result["err"] is not None :
			return render(request, 'bidan/index.html', {'error_message' : result["err"], 'users1' : USERGROUP1, 'users2' : USERGROUP2 })


	for obj in listResponse :
		arguments+=str(obj[0].id) + "/"
	arguments = arguments[:-1]
	return HttpResponseRedirect(reverse('bidan:result', args=(arguments,)))

def get_all(request):
	batchSize = "1000"
	apiUrl = URL + "/all-form-submissions?timestamp=0&batch-size="+batchSize
	result = fetch(request,USERLOGIN, PASSWORDLOGIN, apiUrl, "all")
	if result["responses"] is not None :
		return HttpResponseRedirect(reverse('bidan:result_all', args=(result["responses"][0].id,)))
	elif result["err"] is not None :
		return render(request, 'bidan/index.html', {'error_message' : result["err"], 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

def fetch(request, username, password, url, dataname):
	try:
		req = urllib2.Request(url)
		base64String = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
		req.add_header("Authorization", "Basic %s" % base64String)
		result = urllib2.urlopen(req)
		result_json = json.load(result.fp)
		result.close()
		responses = Response.objects.update_or_create(response_username=dataname,defaults=dict(response_text=json.dumps(result_json),response_password=password))
		result = {}
		result["responses"] = responses
		result["err"] = None
		return result
	except (socket.timeout, urllib2.HTTPError) as e:
		# return HttpResponse("Error: %s" % e)
		# Redisplay the question voting form.
		# return render(request, 'bidan/index.html', {'error_message' : e, 'users1' : USERGROUP1, 'users2' : USERGROUP2 })
		result = {}
		result["responses"] = None
		result["err"] = e
		return result

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
	instanceIds = []
	hhHeads = {}
	memberHHIds = {}
	memberName = {}

	userid = responses_id.split("/")
	xlsfile = []

	for uid in userid :
		_object = get_object_or_404(Response, pk=uid)
		xlsfile.append(_object)
		result_json = json.loads(_object.response_text)
		for row in result_json:
			if not row["instanceId"] in instanceIds:
				instanceIds.append(row["instanceId"])
			else:
				continue
			if not row["formName"] in formNames:
				formNames[row["formName"]] = []
			jsondata = (json.loads(row["formInstance"]))
			jsonfield = []
			jsonfield.append({'name' : "User ID", 'value' : row["anmId"]})

			if row["formName"] == "HHRegistration":
				hhHeads[row["entityId"]] = jsondata["form"]["mapOfFieldsByName"]["name_household_head"]
			if row["formName"] == "open_census":
				memberName[jsondata["form"]["mapOfFieldsByName"]["memberId"]] = jsondata["form"]["mapOfFieldsByName"]["Name_family_member"]
				memberHHIds[jsondata["form"]["mapOfFieldsByName"]["memberId"]] = jsondata["form"]["mapOfFieldsByName"]["id"]
				jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[jsondata["form"]["mapOfFieldsByName"]["memberId"]]]})
			if row["formName"] == "open_census_edit":
				jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[jsondata["form"]["mapOfFieldsByName"]["id"]]]})
			if row["formName"] == "follow_up" or row["formName"] == "child_health" or row["formName"] == "dietary_intake":
				jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[row["entityId"]]]})
				jsonfield.append({'name' : "HH Member Name", 'value' : memberName[row["entityId"]]})
			if row["formName"] == "follow_up_edit" or row["formName"] == "child_health_edit" or row["formName"] == "dietary_intake_edit":
                                jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[row["entityId"]]]})
                                jsonfield.append({'name' : "HH Member Name", 'value' : memberName[row["entityId"]]})


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
	instanceIds = []
	hhHeads = {}
	memberHHIds = {}
	memberName = {}
	wb = xlwt.Workbook()
	xlsfile = get_object_or_404(Response, pk=response_id)
	jsonData = json.loads(xlsfile.response_text)

	for row in jsonData:
		if not row["instanceId"] in instanceIds:
			instanceIds.append(row["instanceId"])
		else:
			continue
		if not row["formName"] in formNames:
			formNames[row["formName"]] = []

		jsondata = (json.loads(row["formInstance"]))
		jsonfield = []
		jsonfield.append({'name' : "User ID", 'value' : row["anmId"]})

		if row["formName"] == "HHRegistration":
			hhHeads[row["entityId"]] = jsondata["form"]["mapOfFieldsByName"]["name_household_head"]
		if row["formName"] == "open_census":
			memberName[jsondata["form"]["mapOfFieldsByName"]["memberId"]] = jsondata["form"]["mapOfFieldsByName"]["Name_family_member"]
			memberHHIds[jsondata["form"]["mapOfFieldsByName"]["memberId"]] = jsondata["form"]["mapOfFieldsByName"]["id"]
			jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[jsondata["form"]["mapOfFieldsByName"]["memberId"]]]})
		if row["formName"] == "open_census_edit":
                        jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[jsondata["form"]["mapOfFieldsByName"]["id"]]]})
		if row["formName"] == "follow_up" or row["formName"] == "child_health" or row["formName"] == "dietary_intake":
			jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[row["entityId"]]]})
			jsonfield.append({'name' : "HH Member Name", 'value' : memberName[row["entityId"]]})
		if row["formName"] == "follow_up_edit" or row["formName"] == "child_health_edit" or row["formName"] == "dietary_intake_edit":
			if row["entityId"] in memberHHIds:
                        	jsonfield.append({'name' : "HH Head Name", 'value' : hhHeads[memberHHIds[row["entityId"]]]})
			else:
				jsonfield.append({'name' : "HH Head Name", 'value' : 'not found:'+row["entityId"]})
			if row["entityId"] in memberName:
                        	jsonfield.append({'name' : "HH Member Name", 'value' : memberName[row["entityId"]]})
			else:
				jsonfield.append({'name' : "HH Member Name", 'value' : 'not found:'+row["entityId"]})

		jsonfield.extend(jsondata["form"]["fields"])
		jsonfield.append({'name' : "clientVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["clientVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		jsonfield.append({'name' : "serverVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["serverVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		formNames[row["formName"]].append(jsonfield)

	return xls_to_response(make_xls(formNames), xlsfile.response_username+'.xls')	

def make_xls(formNames):
	wb = xlwt.Workbook()

	if formNames:
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
						col_width = get_width(len(value))
						if col_width > 65535:
							col_width = 65535
						wa.col(idx2).width = col_width  # if get_width(len(value)) > wa.col(idx2).width else wa.col(idx2).width
						wa.write(idx1+1, idx2, inflection.humanize(value), style1)
					else:
						wa.write(idx1+1, idx2, '-', style1)
	else :
		wa = wb.add_sheet(inflection.humanize('sheet1'))

	return wb

def xls_to_response(xls, fname):
    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response

def download_raw(request, response_id):
	xlsfile = get_object_or_404(Response, pk=response_id)
	jsonData = json.loads(xlsfile.response_text)
	return HttpResponse(json.dumps(jsonData), content_type="application/json")    
	# response = HttpResponse(content_type="application/json")
    # response['Content-Disposition'] = 'attachment; filename=%s' % response_id
    # xls.save(response)
    # return response