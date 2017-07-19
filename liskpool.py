import requests
import json
import sys
import time

NODE = "http://wallet2.shiftnrg.nl:9305"
NODEPAY = "https://wallet.shiftnrg.nl"
PUBKEY = ""
LOGFILE = '/Applications/XAMPP/htdocs/docs/poollogs.json'
PERCENTAGE = 50
MINPAYOUT = 0.5
SECRET = ""
SECONDSECRET = ""

def loadLog ():
	try:
		data = json.load (open (LOGFILE, 'r'))
	except:
		data = {
            "forged": 0,
            "topay": 0,
            "weight": 0,
			"lastpayout": 0, 
			"accounts": {},
			"skip": []
		}
		print ('error open file')
	return data
	
	
def saveLog (log):
	json.dump (log, open (LOGFILE, 'w'), indent=4, separators=(',', ': '))
	


def estimatePayouts (log):
	uri = NODE + '/api/delegates/forging/getForgedByAccount?generatorPublicKey=' + PUBKEY + '&start=' + str (log['lastpayout']) + '&end=' + str (int (time.time ()))
	d = requests.get (uri)
	rew = d.json ()['rewards']
	forged = (int (rew) / 100000000)
	if forged == 0:
		print "forged amount=0, nothing to distribute -> exiting"
		raise SystemExit
	topay = forged * PERCENTAGE / 100
#	print ('To distribute: %f SHIFT' % topay)
	log['forged'] = forged
	log['topay'] = topay
	d = requests.get (NODE + '/api/delegates/voters?publicKey=' + PUBKEY).json ()
	
	weight = 0.0
	payouts = []
	
	for x in d['accounts']:
		if x['balance'] == '0' or x['address'] in log['skip']:
			continue
			
		weight += float (x['balance']) / 100000000
		
#	print ('Total weight is: %f' % weight
	log['weight'] = weight
	
	for x in d['accounts']:
		if int (x['balance']) == 0 or x['address'] in log['skip']:
			continue

		if x['username'] is None:
			nm='.'
		else:
			nm=x['username']
		
		payouts.append ({"address": x['address'],"name": nm, "tot": 100 * (float (x['balance']) / weight / 100000000), "balance": (float (x['balance']) / 100000000 * topay) / weight})
		#print (float (x['balance']) / 100000000, payouts [x['address']], x['address'])
		
	return payouts
	
	

if __name__ == "__main__":
	log = loadLog ()
	topay = estimatePayouts(log)
	
	f = open ('payments.sh', 'w')
	for x in topay:
		if not (x['address'] in log['accounts']) and x['balance'] != 0.0:
			log['accounts'][x['address']] = {'name': x['name'], 'vwght': 0.0,'paid': 0.0, 'pending': 0.0, 'received': 0.0 }
			
		if x['balance'] < MINPAYOUT:
			log['accounts'][x['address']]['pending'] += x['balance']
			log['accounts'][x['address']]['paid'] = x['balance']
			log['accounts'][x['address']]['vwght'] = x['tot']
			continue
			
		log['accounts'][x['address']]['received'] += x['balance']
		log['accounts'][x['address']]['vwght'] = x['tot']	
		log['accounts'][x['address']]['paid'] = x['balance']	
		
		f.write ('echo Sending ' + str (x['balance']) + ' to ' + x['address'] + '\n')
		
		data = { "secret": SECRET, "amount": int (x['balance'] * 100000000), "recipientId": x['address'] }
		if SECONDSECRET != None:
			data['secondSecret'] = SECONDSECRET
		
		f.write ('curl -k -H  "Content-Type: application/json" -X PUT -d \'' + json.dumps (data) + '\' ' + NODEPAY + "/api/transactions\n\n")
		f.write ('sleep 10\n')
			
	for y in log['accounts']:
		if log['accounts'][y]['pending'] > MINPAYOUT:
			f.write ('echo Sending pending ' + str (log['accounts'][y]['pending']) + ' to ' + y + '\n')
			
			
			data = { "secret": SECRET, "amount": int (log['accounts'][y]['pending'] * 100000000), "recipientId": y }
			if SECONDSECRET != None:
				data['secondSecret'] = SECONDSECRET
			
			f.write ('curl -k -H  "Content-Type: application/json" -X PUT -d \'' + json.dumps (data) + '\' ' + NODEPAY + "/api/transactions\n\n")
			log['accounts'][y]['received'] += log['accounts'][y]['pending']
			log['accounts'][y]['paid'] = log['accounts'][y]['pending']
			log['accounts'][y]['pending'] = 0.0
			f.write ('sleep 10\n')
			
		
	f.close ()
	
	log['lastpayout'] = int (time.time ())
	
	print (json.dumps (log, indent=4, separators=(',', ': ')))
	
	if len (sys.argv) > 1 and sys.argv[1] == '-y':
		print ('Saving...')
		saveLog (log)
	else:
		yes = input ('save? y/n: ')
		if yes == 'y':
			saveLog (log)
