from requests import *
from requests.auth import HTTPBasicAuth
from xml.dom.minidom import parseString

def getraw(url,token):
	r=get(url,headers={'x-vcloud-authorization':token,'Accept':'application/*+xml;version=1.5'})
	return r.text

def getorgurl(orgname,token):
	orgurl=[];roleurl=""
	dom=parseString(getraw('https://www.cloud.kth.se/api/admin',token))
	for e in dom.getElementsByTagName("OrganizationReferences")[0].childNodes:
		if e.nodeType==e.ELEMENT_NODE:
			orgurl.append(e.getAttribute("href"))
	for e in dom.getElementsByTagName("RoleReferences")[0].childNodes:
		if e.nodeType==e.ELEMENT_NODE:
			if e.getAttribute("name")=="Organization Administrator":
				roleurl=e.getAttribute("href")
	return (orgurl,roleurl)

def getvdcurl(orgurl,token):
	dom=parseString(getraw(orgurl,token))
	return {e.getAttribute("name"):e.getAttribute("href") for e in dom.getElementsByTagName("Vdcs")[0].childNodes if e.nodeType==e.ELEMENT_NODE}

def getcapacity(vdcurl,token):
	dom=parseString(getraw(vdcurl,token))
	#print {e.parentNode.tagName:e.childNodes[0].data for e in dom.getElementsByTagName("Units")}
	return {e.parentNode.tagName:int(e.childNodes[0].data) for e in dom.getElementsByTagName("Allocated")}

if __name__ == "__main__":
	url='https://www.cloud.kth.se/api/sessions'
	with open('.c') as f:
		(u,pw)=f.read().strip().split(':')
		org=u.split('@')[-1]
	r=post(url,auth=HTTPBasicAuth(u, pw),headers={'Accept':'application/*+xml;version=1.5'})
	token=r.headers['x-vcloud-authorization']
	(orgurl,roleurl)=getorgurl(org,token)
	for o in orgurl: 
		vdcs=getvdcurl(o,token)
		for (vdc,u) in vdcs.items():
			print vdc,getcapacity(u,token)

