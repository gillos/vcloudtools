from getpass import getpass
import os
import urllib2
from urllib2 import HTTPError
import urllib
from xml.dom.minidom import parseString
import json

vcdurl=''
def gettoken(uname,pw):
   url=vcdurl+"/api/v1.0/login"
   data=urllib.urlencode({})
   passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
   passman.add_password(None, url, uname,pw)
   authhandler = urllib2.HTTPBasicAuthHandler(passman)
   opener = urllib2.build_opener(authhandler)
   urllib2.install_opener(opener)
   req=urllib2.Request(url,data)
   r=urllib2.urlopen(req)
   return r.info()['x-vcloud-authorization']

def getraw(url,token):
   req=urllib2.Request(url)
   req.add_header('x-vcloud-authorization',token)
   res=urllib2.urlopen(req)
   return res.read()

def postraw(url,ct,data,token,rcode):
   req=urllib2.Request(url,data)
   req.add_header('Content-Type',ct)
   req.add_header('x-vcloud-authorization',token)
   try:
      r=urllib2.urlopen(req)
   except HTTPError,e:
      return False
   else:
      if r.code==rcode:
         return True
      else:
         return False

def getvdcurl(orgurl,token):
   dom=parseString(getraw(orgurl,token))
   for e in dom.getElementsByTagName("Vdcs")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
        return e.getAttribute("href")
   return ""
   
def getnetworkurl(vdcurl,token):
   dom=parseString(getraw(vdcurl,token))
   for e in dom.getElementsByTagName("AvailableNetworks")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         return e.getAttribute("href")
   return ""
   
def getnetworkname(n,token):
	dom=parseString(getraw(n,token))
	for e in dom.getElementsByTagName("OrgNetwork")[0].childNodes:
		if e.nodeType==e.ELEMENT_NODE:
			return e.getAttribute("name")
	return ""

def getcatalogurl(orgurl,name,token):
   dom=parseString(getraw(orgurl,token))
   for e in dom.getElementsByTagName("Catalogs")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         if e.getAttribute("name")==name:
            return e.getAttribute("href")
   return ""

def getcatalogitemurl(caturl,name,token):
   dom=parseString(getraw(caturl,token))
   for e in dom.getElementsByTagName("CatalogItems")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         if e.getAttribute("name")==name:
            return e.getAttribute("href")
   return ""

def getorgurl(orgname,token):
   orgurl="";roleurl=""
   dom=parseString(getraw(vcdurl+"/api/v1.0/admin",token))
   for e in dom.getElementsByTagName("OrganizationReferences")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         if e.getAttribute("name")==orgname:
            orgurl=e.getAttribute("href")
   for e in dom.getElementsByTagName("RoleReferences")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         if e.getAttribute("name")=="Organization Administrator":
            roleurl=e.getAttribute("href")
   return (orgurl,roleurl)

def insttmpl(vdcurl,networkurl,catalogurl,name,token):
   data="""<InstantiateVAppTemplateParams name="%s" xmlns="http://www.vmware.com/vcloud/v1"
xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" > 
	<Description>%s</Description> 
	<InstantiationParams>
	<NetworkConfigSection> 
		<ovf:Info>Configuration parameters for vAppNetwork</ovf:Info> 
		<NetworkConfig networkName="LANBB">
			<Configuration> 
				<ParentNetwork href="%s"/>
				<FenceMode>bridged</FenceMode>
			</Configuration>
		</NetworkConfig>
	</NetworkConfigSection> 
     </InstantiationParams>
     <Source href="%s"/>
</InstantiateVAppTemplateParams>""" % (name,name,networkurl,catalogurl)
   host=vdcurl.split('/')[2]
   vdcid=vdcurl.split('/')[-1]
   url="https://%s/api/v1.0/vdc/%s/action/instantiateVAppTemplate" % (host,vdcid)
   req=urllib2.Request(url,data)
   req.add_header('Content-Type','application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml')
   req.add_header('x-vcloud-authorization',token)
   try:
      r=urllib2.urlopen(req)
   except HTTPError,e:
      print e.code
      return ""
   else:
      if r.code==201:
         dom=parseString(r.read())
         x=dom.getElementsByTagName("VApp")[0]
         return x.getAttribute("href")
      else:
         return ""

def modifyvapp(vmurl,networkname,token):
	url=vmurl+"/networkConnectionSection/"
	ct="application/vnd.vmware.vcloud.networkConnectionSection+xml"
	data="""<?xml version="1.0" encoding="UTF-8"?>
<NetworkConnectionSection xmlns="http://www.vmware.com/vcloud/v1" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" type="application/vnd.vmware.vcloud.networkConnectionSection+xml" href="%s" ovf:required="false" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schemas.dmtf.org/ovf/envelope/1 http://schemas.dmtf.org/ovf/envelope/1/dsp8023_1.1.0.xsd http://www.vmware.com/vcloud/v1 http://vcd4.lan.kth.se/api/v1.0/schema/master.xsd">
    <ovf:Info>Specifies the available VM network connections</ovf:Info>
    <PrimaryNetworkConnectionIndex>0</PrimaryNetworkConnectionIndex>
    <NetworkConnection network="%s">
		<NetworkConnectionIndex>0</NetworkConnectionIndex>
        <IsConnected>true</IsConnected>
        <IpAddressAllocationMode>DHCP</IpAddressAllocationMode>
    </NetworkConnection>
    <Link rel="edit" type="application/vnd.vmware.vcloud.networkConnectionSection+xml" href="%s"/>
	</NetworkConnectionSection>""" % (url,networkname,url)
	req=urllib2.Request(url,data)
	req.add_header('Content-Type',ct)
	req.add_header('x-vcloud-authorization',token)
	req.get_method = lambda: 'PUT'
	try:
		r=urllib2.urlopen(req)
	except HTTPError,e:
		return False
	else:
		if r.code==202:
			return True
		else:
			return False

def getvm(vappurl,token):
	dom=parseString(getraw(vappurl,token))
	d2=dom.getElementsByTagName("VApp")
	d3=d2[0].getElementsByTagName("Children")
	if len(d3)>0:
		d4=d3[0].getElementsByTagName("Vm")
		return d4[0].getAttribute("href")
	else:
		return ""

def gettemplate(url,token,name):
   dom=parseString(getraw(url,token))
   for e in dom.getElementsByTagName("CatalogItem")[0].childNodes:
      if e.nodeType==e.ELEMENT_NODE:
         if e.getAttribute("name")==name:
            return e.getAttribute("href")
   return ""
   
def deploy(url,token):
	data="""<DeployVAppParams powerOn="true" xmlns="http://www.vmware.com/vcloud/v1"/>"""
	return postraw(url,'application/vnd.vmware.vcloud.deployVAppParams+xml',data,token,202)

def getmacaddr(vm,token):
	dom=parseString(getraw(vm+"/networkConnectionSection/",token))
	mac=dom.getElementsByTagName("MACAddress")
	if len(mac)>0:
		return mac[0].childNodes[0].nodeValue
	return ""
	
def readpass():
   fpath=os.path.expanduser('~/.vcloud')
   if not os.path.isdir(fpath):
      os.mkdir(fpath)
   try:
      f=open(fpath+'/.p')
      pw=f.read().strip()
      f.close()
   except:
      pw=getpass('vCloud Password:')
      f=open(fpath+'/.p','w')
      f.write(pw)
      f.close()
      print "Password saved in %s/.p" % fpath
   return pw

def readconfig(user='',org=''):
	""" config file needs to look something like this
	{"org": "INST", "user": "nisse@kth.se","host":"https://www.cloud.kth.se"}
	"""
	fpath=os.path.expanduser('~/.vcloud')
	if not os.path.isdir(fpath):
		os.mkdir(fpath)
	try:
		f=open(fpath+'/config')
		c=json.loads(f.read())
		f.close()
	except:
		if user=='':
			return {'user':'','org':''}
		f=open(fpath+'/config','w')
		c={'user':user,'org':org}
		f.write(json.dumps(c))
		f.close()
	global vcdurl
	vcdurl=c['host']
	return c
	
def createvapp(vname,cat='pub_cat',tmpl='kthmoln2'):
	config=readconfig()
	if config['user']=='': return ""
	tk=gettoken(config['user']+'@'+config['org'],readpass())
	ou=getorgurl(config['org'],tk)
	c=getcatalogurl(ou[0],cat,tk)
	ci=getcatalogitemurl(c,tmpl,tk)
	t=gettemplate(ci,tk,tmpl)
	v=getvdcurl(ou[0],tk)
	n=getnetworkurl(v,tk)
	vapp=insttmpl(v,n,t,vname,tk)
	return (vapp,n,tk)
	
import time
import sys

if __name__ == '__main__':
	if len(sys.argv)>1:
		vname=sys.argv[1]
	else:
		print "usage..."
		sys.exit()
	(vapp,n,t)=createvapp(vname)
	networkname=getnetworkname(n,t)
	vm=""
	i=0
	while vm=="":
		i+=1
		vm=getvm(vapp,t)
		time.sleep(5)
		print "cloning...%03s" % (5*i)
	if modifyvapp(vm,networkname,t):
#the sleep should be replace by polling the task returned
		time.sleep(10)
		if deploy(vapp+'/action/deploy',t):
			print "started"
			print getmacaddr(vm,t)
		else:
			print "fail!"
	else:
		print "fail!"