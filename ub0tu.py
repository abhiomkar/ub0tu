#!/usr/bin/env python
## ub0tu.py - A simple & Intelligent IRC bot written in python
##	      It supports - greeting, google, word definition, delicious, logging, date

#=========================================================================
"""
Copyright (C) 2007, Abhinay Omkar < abhiomkar@gmail.com >  

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
#=========================================================================

__version__="0.1"
__author__="Abhinay Omkar (abhiomkar@gmail.com)"

import socket,threading,string,re,time,os,sys
import urllib
import random

os.environ['TZ'] = 'Asia/Calcutta'
time.tzset()

SERVER='irc.freenode.net'
PORT=6667
NICK='UB0TU'
IDENT="oO"
REALNAME="BOT"
HOST='irc.freenode.net'
CHANNELS='#ubuntu-ap,#zyx'
ADMNICK='abhinay'
OWNER='abhinay - http://abhinay.nipl.net'
PASSWORD='UB0TU'
HELP= \
"""Usage : !<package_name> - gives the description of the package. !g[d][l][1-8] <keywords_to_search> - Google It (d - define, l - I'm Feeling Lucky, 1 to 8 is no. of google results). !date - current date & time."""

ircSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
ircSock.connect((SERVER,PORT))
ircSock.send("NICK %s\r\n" % NICK)
ircSock.send("PASS %s\r\n"%PASSWORD)
ircSock.send("USER %s %s bla :%s\r\n"%(IDENT,HOST,REALNAME))
ircSock.send("JOIN %s\r\n"%(CHANNELS))
ircSock.send("PRIVMSG nickserv :identify %s\r\n"%(PASSWORD))

def parse(line):
	"""
	patterns:
	:abhinay!n=abhinay@unaffiliated/abhinay JOIN :#ubuntu-ap
	:y3it221_klce!n=gopi@202.133.63.14 PRIVMSG #ubuntu-ap :abhinay: hiiiiiii
	:abhinay!n=abhinay@unaffiliated/abhinay QUIT :"Leaving"
	:abhinay!n=abhinay@unaffiliated/abhinay PRIVMSG SimpleBot :hi
	:abhinay!n=abhinay@unaffiliated/abhinay KICK #ubuntu-ap UB0TU :abhinay
	"""
	nick = ''
	nick2 = ''
	channel = ''
	msg = ''
	nick = line.split('!')[0][1:]
	
	if(((line.split(' ')[1]=='JOIN') | (line.split(' ')[1]=='QUIT') | (line.split(' ')[1]=='PART')) & (nick!=NICK)):
		try:
			open('/home/abhinay/www/botlog','a').write(time.ctime()+'\t'+line+'\n')
		except IOError:
			pass
	if(line.split(' ')[1]=='JOIN'):
		channel = line.split(' ')[2][1:].strip()
	
	elif(line.split(' ')[1]=='PRIVMSG'):
		pos =  line.find(':',1) + 1
		msg = line[pos:].strip()
		if(line.split(' ')[2][0]=='#'):   # if he talk to the channel
			channel = line.split(' ')[2].strip()
		else:
			channel = nick   # he PMs the bot, so channel is he..
	if(line.split(' ')[1]=='KICK'):
		channel = line.split(' ')[2][1:].strip()
		msg = " KICK "
	return (channel, nick, msg)

def googleIt(ircSock,channel,query,nres):
	hr='---------------------------------------------------------'
	query = query.replace(' ','+')
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect(('www.google.co.in',80))
	s.send(('GET http://www.google.co.in/search?q=%s&num=%d HTTP/1.0\r\n\r\n')%(query,int(nres)))
	f=s.makefile('r',0)
	s.close()
	data = repr(f.read())
	if(query.startswith('define:')==True):
		rdefin = re.compile(r'size=-1><li>(.*?)\s*<br>')
		if(rdefin.findall(data)):
			try:
				definition = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), rdefin.findall(data)[0])
			except:
				definition = rdefin.findall(data)[0]
			definition = re.sub('<.*?>','',definition)
			definition = re.sub('&[a-z]+;', '', definition)
			definition = definition.replace(r'\n','')
			definition = definition[:1450]
			ircSock.send('PRIVMSG %s :%s\r\n'%(channel,definition.decode('latin-1')))
			return
	url=re.compile(r'<h2 class=r><a href="(.*?)</a></h2><table border=0 cellpadding=0 cellspacing=0>')
	if(len(url.findall(data))==0):
		ircSock.send('PRIVMSG %s :Your search - %s - did not match any documents.\r\n'%(channel,query.replace('+',' ')))
	if(len(url.findall(data))>1):
		ircSock.send('PRIVMSG %s :%s-----------------------\r\n'%(channel,hr))
	for goog in url.findall(data):
	        result = goog.replace('<b>','').replace('</b>','').replace('>','')
	        result = result.split('" class=l')[1]+' - '+result.split('" class=l')[0]
		try:
			result = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), result)
		except ValueError:
			pass
		result = re.sub(r'&[a-z]+; ', '', result)
		ircSock.send('PRIVMSG %s :%s\r\n'%(channel,result))
	if(len(url.findall(data))>1):
		ircSock.send('PRIVMSG %s :%s Powered by Google ----\r\n'%(channel,hr))

	f.close()

def delicious(ircSock,channel,tag,nres):
	"""http://del.icio.us"""
	url = 'http://del.icio.us/'+tag
	data = urllib.urlopen(url).read()
	rdel = re.compile(r'class="desc"><a href="(.*?)</a>')
	for delic in rdel.findall(data):
		if(nres == 0):
			break
		delic_url, delic_desc = delic.split('" rel="nofollow">')
		delic_url = delic_url.replace('&amp;','&')
		delic_desc = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), delic_desc)
		delic_desc = re.sub('&[a-z]+;', '',delic_desc)
		ircSock.send('PRIVMSG %s :%s - %s\r\n'%(channel,delic_desc,delic_url))
		nres = nres-1
		
readbuffer=""
while 1:
	readbuffer = readbuffer+ircSock.recv(1024)
	lines = string.split(readbuffer,"\n")
	readbuffer = lines.pop()

	for line in lines:
		#debug messages on - uncomment the below line
		#print line
		#print '----------------------------------------------------------'
		if(line[:4]=='PING'):
			ircSock.send('PONG %s\r\n'%line[6:].strip())
			continue
		

		channel, nick, msg = parse(line)
		if(msg==" KICK "):
			print nick+" has KICKed me. Go beat him ! X-)"

			
			
		splt = msg.rfind('|') # find out the nick address & slice the msg
		if(splt>=0):
			msg = msg[:splt]

		if(re.match(r'!.+?>.+?', msg)):
			channel = msg.split('>')[1].strip()
			msg = msg.split('>')[0].strip()

		if(line.split(' ')[1]=='JOIN'):
			print 'CHANNEL : '+channel
			print 'NICK : '+nick
			ircSock.send(("PRIVMSG %s :Welcome %s ! Enjoy your stay here :)\r\n")%(channel,nick))
		
		if(line.split(' ')[1]=='PRIVMSG'):
			reply = ''
			if(msg.find(NICK)>=0):
				message = msg.replace(NICK,'')[1:].strip()    ## what did he say to the bot ?
				if(message.startswith('+') | message.startswith('-')):
					deb = message.split(' ')
					for d in deb:
						if(d.startswith('+')):
							if(os.popen("grep ^"+d[1:]+"$ /home/abhinay/www/newbiecd").read()==''):
								os.popen("echo "+d[1:]+">> /home/abhinay/www/newbiecd")
						if(d.startswith('-')):
							os.popen("sed -i '/^$/d' /home/abhinay/www/newbiecd")
							os.popen("sed -i '/"+d[1:]+"/d' /home/abhinay/www/newbiecd")
				if(re.search('^(h(i|ey|ola)|d(ude|00de))',message.lower())):
					reply = random.choice(['Hi', 'y0 !', 'hi ! wassup ?', 'Hey', 'dude !', 'Hello', 'd0000000de !', 'hi, welcome ! :)'])
				
				if(re.search('^who',message.lower())):	
					reply = "I'm %s. I'm a program, Author : %s."%(NICK, OWNER)
				if(re.search('^ping$',message.lower())):
					reply = "pong"
				if(message.lower().find('thank')>=0):	
					reply = "you are welcome !  :)"

				if(reply!=''):
					ircSock.send(("PRIVMSG %s :%s: %s \r\n")%(channel,nick, reply))
				
## user inputs : !g key words to search
## result google search		
		MAX_GOOGLE = 8
		nres = 3
		if(re.match('!g[ld1-8]* ',msg)):   # accepts '!gl keyword','!g[number] keyword'&, '!g keyword'
			par = msg.split(' ')[0][2:]
			query = msg[3:].strip()
			try:
				if(int(par) > MAX_GOOGLE):
					nres = MAX_GOOGLE
				else:
					nres = int(par)
			except ValueError:
				if(par=='l'):
					nres = 1
				if(par=='d'):
					query = 'define:'+query
			googleIt(ircSock,channel,query,nres)		
			break
		
		MAX_DELICIOUS = 5	
		nres = 3
		if(re.match('^!del .*',msg)):
			tag = msg.split(' ')[1]
			try:
				nres = int(msg.split(' ')[2])
			except:
				pass
			if(nres>MAX_DELICIOUS):
				nres = MAX_DELICIOUS
			delicious(ircSock,channel,tag,nres)
			break

				
## user inputs : !mplayer
## bot gives description about mplayer
## user inputs : !date
## display date

		if(msg.startswith('!')==True):
			word = msg.split(' ')[0][1:].strip()		## word = mplayer
			if(os.popen("apt-cache show %s"%(word)).read()==''):	## check if package exists or not
				if(word=='date'):
					ircSock.send(("PRIVMSG %s :%s\r\n")%(channel,time.strftime('%c IST')))
				elif(word=='help'):
					ircSock.send(("PRIVMSG %s :%s\r\n")%(channel,HELP))

				elif(word=='ask'):
					ASK = "Don't ask to ask a question. Just ask your question :)"
					ircSock.send(("PRIVMSG %s :%s\r\n")%(channel,ASK))
				else:
					ircSock.send('PRIVMSG '+channel+' :Unable to locate package '+word+'\r\n')
				break

			desc = os.popen("apt-cache show %s"%(word)).read()
			desc = re.search(r'Description:(.*?)(\\n \.\\n|\\n\\n)',repr(desc)).group()
			desc = desc.replace('Description: ',word+': ')
			sep = desc.find('\\n')
			ircSock.send(("PRIVMSG %s :%s\r\n")%(channel,desc[:sep]))
			ircSock.send(("PRIVMSG %s :%s\r\n")%(channel,desc[sep:].replace('\\n','')))

		
