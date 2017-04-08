#######################################
# Brandon Bernier 				
# ECE 6130 - Grid and Cloud Computing
# Final Project
# Classifier for Congressional Bills
# Using Machine Learning Algorithms
#######################################

import re
import string
import json

import os.path
import subprocess

from urllib2 import urlopen
from threading import Thread

import nltk 
from nltk.corpus import stopwords


url_base 	= "https://congress.api.sunlightfoundation.com/"
api_key 	= "&apikey=99edce157d934983ad380f55ae4c1757"
per_page 	= "&per_page=50"

stop_words 	= set(stopwords.words("english"))

vote_dict 	= {}
full_texts 	= {}
bill_ids 	= {}
versions 	= set([ 'eh', 'is', 'cdh', 'ih', 'cds', 'lts', 'es', 'pap', 'pp', 
					'rs', 'pcs', 'rcs', 'enr', 'rh', 'eah', 'pcs2', 'eas', 
					'rfs2', 'rfs', 'rds', 'ath', 'ats', 'rfh'])


class VoteWhip(Thread):
	"""Thread class for multithreading to get vote history."""
	def __init__(self, thread_id):
		Thread.__init__(self)
		self.thread_id = thread_id

	def run(self):
		getVoteDataSinglePage(self.thread_id)


def getCongressmenData():
	""" Get all necessary data and create dictionary of Congressmen."""
	congressmen_query 	= url_base + "legislators?per_page=all" + api_key 
	congressmen 		= urlopen(congressmen_query)
	congressmen_data 	= congressmen.read()
	congressmen_dict	= json.loads(congressmen_data)
	congressmen_results	= congressmen_dict["results"]

	for result in range(len(congressmen_results)):
		congress_dict 	= congressmen_dict["results"][result]
		first_name 		= congress_dict["first_name"].encode('ascii', 'ignore')
		last_name 		= congress_dict["last_name"].encode('ascii', 'ignore')
		bioguide_id		= congress_dict["bioguide_id"].encode('ascii', 'ignore')
		party			= congress_dict["party"].encode('ascii', 'ignore')
		name 			= first_name + " " + last_name
		vote_dict[bioguide_id] = {"name": name, "party": party, "vote_history": {}}


def getVoteDataSinglePage(page):
	"""Get vote data for single page of results."""
	page_num		= "&page=" + str(page)
	vote_query 		= url_base + "votes?fields=voter_ids,bill_id,vote_type" + per_page + page_num + api_key
	votes			= urlopen(vote_query)		#instance
	vote_data 		= votes.read()				#JSON
	vote_dict 		= json.loads(vote_data)		#dict
	vote_results 	= vote_dict["results"]		#list

	for result in range(len(vote_results)):
		result_dict = vote_results[result]
		if "bill_id" in result_dict and result_dict["vote_type"] == "passage":
			addVotes(result_dict)


def getVoteData():
	"""Get all of the vote data available."""
	vote_query 		= url_base + "votes?fields=voter_ids,bill_id,vote_type" + api_key
	votes			= urlopen(vote_query)		#instance
	vote_data 		= votes.read()				#JSON
	vote_dict 		= json.loads(vote_data)		#dict
	vote_count 		= vote_dict["count"]		#int
	page_count		= (vote_count/50) + 1
	threads 		= []

	for page in range(page_count):				#spawn 1 thread per page here
		thread = VoteWhip(page+1)
		thread.start()
		threads.append(thread)

	for thread in threads:
		thread.join()
	

def addVotes(result_dict):
	"""Function to add a vote to Congressman's voting history."""
	bill_id = result_dict["bill_id"].encode('ascii','ignore')
	if bill_id not in bill_ids:
		bill_ids.update({bill_id: {"sponsor_party": getBillSponsor(bill_id)}})
	for voter in result_dict["voter_ids"]:
		vote = result_dict["voter_ids"][voter].encode('ascii','ignore')
		if voter in vote_dict:
			vote_dict[voter]["vote_history"][bill_id] = vote


def getBillSponsor(bill_id):
	"""Get the political party of the sponsor of a bill."""
	bill_query 		= url_base + "bills?bill_id=" + bill_id + api_key 
	bill 			= urlopen(bill_query)
	bill_data 		= bill.read()
	bill_dict		= json.loads(bill_data)
	bill_results	= bill_dict["results"]

	if bill_results and "sponsor_id" in bill_results[0]: 
		sponsor_id 	= bill_results[0]["sponsor_id"]
		if sponsor_id in vote_dict:
			sponsor_party 	= vote_dict[sponsor_id]["party"]
			return sponsor_party
	else:
		return "NA"


def getUpcomingBills():
	"""Get info for all upcoming bills."""
	new_bills_query = url_base + "upcoming_bills?" + per_page + api_key
	new_bills_url	= urlopen(new_bills_query)		#instance
	new_bills_data 	= new_bills_url.read()			#JSON
	new_bills_dict 	= json.loads(new_bills_data)	#dict
	results 		= new_bills_dict["results"]		#list
	new_bills 		= {}

	for result in range(len(results)):
		new_bill 		= results[result]["bill_id"].encode('ascii', 'ignore')
		sponsor_party 	= getBillSponsor(new_bill).encode('ascii', 'ignore')
		new_bills.update({new_bill: {"sponsor_party": sponsor_party}})
		readBill(new_bill)

	return new_bills


def printBills():
	"""Print all bills in the vote history."""
	for bill in bill_ids:
		print bill, bill_ids[bill]["sponsor_party"]


def printBillInfo(bill_id):
	"""Print all info for bill with bill_id."""
	print bill_id, bill_ids[bill_id]["sponsor_party"]


def printCongressmen():
	"""Print list of all Congressmen."""
	for congressman in sorted(vote_dict):
		print congressman, vote_dict[congressman]["name"], vote_dict[congressman]["party"]


def getIDVoteHistory(bioguide_id):
	"""Get the vote history of a single Congressman by ID."""
	return vote_dict[bioguide_id]["vote_history"]


def printIDVoteHistory(bioguide_id):
	"""Print the vote history of a single Congressman by ID."""
	print bioguide_id + ":", vote_dict[bioguide_id]["name"], vote_dict[bioguide_id]["party"]
	vote_history = getIDVoteHistory(bioguide_id)
	for vote in sorted(vote_history):
		print "\t" + vote + ":", vote_history[vote]


def printVoteHistoryAll():
	"""Print the vote history of all Congressmen."""
	for congressman in sorted(vote_dict):
		printIDVoteHistory(congressman)


def getBillVersion(bill_id):
	"""Get the last version of a bill."""
	bill_query 		= url_base + "bills?bill_id=" + bill_id + api_key 
	bill 			= urlopen(bill_query)
	bill_data 		= bill.read()
	bill_dict		= json.loads(bill_data)
	bill_results	= bill_dict["results"]

	if bill_results and "last_version" in bill_results[0]: 
		version = bill_results[0]["last_version"]["version_code"].encode('ascii','ignore')
		return version
	else:
		return "NA"


def getBillVersionsAll():
	"""Create a set of all possible bill versions."""
	for bill in bill_ids:
		version = getBillVersion(bill)
		versions.add(version)
	print versions 


def readBill(bill_id):
	"""Read in the full text version of a bill."""
	split		= bill_id.split("-")
	bill 		= split[0]
	session		= split[1]
	bill_split	= re.split('(\d+)', bill)
	bill_type	= bill_split[0]
	version 	= getBillVersion(bill_id)
	folder_path = "congress-master/data/" + session + "/bills/" + bill_type + "/" + bill + "/text-versions/"
	file_path	= folder_path + version + "/document.txt"


	if os.path.exists(file_path):
		with open(file_path, "r") as full_text:
			bill_text = full_text.read()
			full_texts[bill_id] = bill_text
	else:
		for vers in versions:
			file_path = folder_path + vers + "/document.txt"
			if os.path.exists(file_path):
				with open(file_path, "r") as full_text:
					bill_text = full_text.read()
					full_texts[bill_id] = bill_text
					break
			else:
				pass


def readAllBills():
	"""Read in the full text version of all bills."""
	for bill_id in bill_ids:
		print bill_id
		readBill(bill_id)


def getBillWords(bill_id):
	"""Parse a bill and return a list of all meaningful words in the bill."""
	bill_words	= []
	if bill_id in full_texts:
		bill_text 		= full_texts[bill_id] 
		replacement		= string.maketrans(string.punctuation, ' '*len(string.punctuation))
		bill_formatted 	= bill_text.lower().translate(replacement, string.digits)
		all_words 		= filter(lambda w: not w in stop_words, bill_formatted.split())
		bill_words 		= [ word for word in all_words if len(word) >= 3 ]
	else: 
		pass

	return bill_words


def getFreqDist(bill_id):
	"""Gets the frequency distribution for a given bill."""
	bill_words 	= getBillWords(bill_id)
	freq_dist 	= nltk.FreqDist(bill_words)
	
	print bill_id
	for word in freq_dist.most_common():
		print word

	return freq_dist.most_common()


def getIDFreqDist(bioguide_id):
	"""Gets the frequency distribution of words in all bills voted on by specific legislator."""
	vote_history 			= getIDVoteHistory(bioguide_id)
	word_dict				= {"bill_words": [], "yea_words": [], "nay_words": []}
	temp_words				= []
	yea_words_set			= set()
	nay_words_set			= set()

	for vote in sorted(vote_history):
		temp_words = getBillWords(vote)
		word_dict['bill_words'] += temp_words
		if vote_history[vote] == "Yea":
			word_dict['yea_words'] += temp_words
			for word in temp_words:
				yea_words_set.add(word)
		elif vote_history[vote] == "Nay":
			word_dict['nay_words'] += temp_words
			for word in temp_words:
				nay_words_set.add(word)
		else:
			pass
	
	yea_wordss = yea_words_set.difference(nay_words_set)
	nay_wordss = nay_words_set.difference(yea_words_set)
	
	yea_words  = [x for x in word_dict['yea_words'] if x in yea_wordss]
	nay_words  = [x for x in word_dict['nay_words'] if x in nay_wordss]

	yea_freq_dist	= nltk.FreqDist(yea_words).most_common()
	nay_freq_dist 	= nltk.FreqDist(nay_words).most_common()

	freq_dist 		= {"yea": yea_freq_dist, "nay": nay_freq_dist}

	return freq_dist


def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii', 'ignore')
    return dict(map(ascii_encode, pair) for pair in data.items())


def loadData():
	"""Either gets all necessary data or loads previously stored data."""
	global vote_dict, bill_ids, full_texts
	print "Loading Data"
	#subprocess.Popen("./run fdsys --collections=BILLS --congress=114 --store=text", 
	#				 cwd="congress-master/", stdout=subprocess.PIPE, shell=True)
	if os.path.exists("json/vote_history.json") and os.path.exists("json/bill_ids.json"):
		with open('json/vote_history.json','r') as votes_json:
			vote_dict 	= json.load(votes_json)
		with open('json/bill_ids.json','r') as bill_ids_json:
			bill_ids 	= json.load(bill_ids_json)
	else:
		getCongressmenData()
		getVoteData()	
		with open("json/vote_history.json", 'w') as votes_json: 
			json.dump(vote_dict, votes_json)
		with open("json/bill_ids.json", 'w') as bill_ids_json: 
			json.dump(bill_ids, bill_ids_json)

 	if os.path.exists("json/full_texts.json"):
 		with open("json/full_texts.json", 'r') as full_texts_json:
 			full_texts 	= json.load(full_texts_json, object_hook=ascii_encode_dict)
 	else:
 		getBillVersionsAll()
 		readAllBills()
 		with open("json/full_texts.json", 'w') as full_texts_json:
 			json.dump(full_texts, full_texts_json)
 	print "Loading Data Complete"


def classifierByParty(bioguide_id):
	"""Returns predictions for all upcoming bills based solely on the voter and sponsor's political parties."""
	voter_party	= vote_dict[bioguide_id]["party"]
	new_bills 	= getUpcomingBills()

	for bill in new_bills:
		sponsor_party = new_bills[bill]["sponsor_party"]
		if voter_party == sponsor_party:
			new_bills[bill].update({"vote": "Yea"})
		else:
			new_bills[bill].update({"vote": "Nay"})
	
	print bioguide_id, vote_dict[bioguide_id]["name"], voter_party
	for bill in new_bills:
		print bill, new_bills[bill]["sponsor_party"], new_bills[bill]["vote"]

	return new_bills


def classifierByWords(bioguide_id):
	"""Returns a set of predictions for all upcoming bills based on the words in the bill."""
	new_bills 	= getUpcomingBills()
	freq_dist 	= getIDFreqDist(bioguide_id)
	yea_common	= dict(freq_dist["yea"])
	nay_common	= dict(freq_dist["nay"])

	for bill in new_bills:
		bill_text = getBillWords(bill)
		yea_count = 0
		nay_count = 0
		for word in bill_text:
			if word in yea_common:
				yea_count += yea_common[word]
			if word in nay_common:
				nay_count += nay_common[word]
		if yea_count >= nay_count:
			new_bills[bill].update({"vote": "Yea"})
		else:
			new_bills[bill].update({"vote": "Nay"})
		if yea_count > 10*nay_count or nay_count > 10*yea_count:	# If difference is overwhelming, set confidence high
			new_bills[bill].update({"confidence": 1})
		else:
			new_bills[bill].update({"confidence": 0})
		#print "Yea: ", yea_count, "Nay: ", nay_count

	print bioguide_id, vote_dict[bioguide_id]["name"], vote_dict[bioguide_id]["party"]
	for bill in new_bills:
		print bill, new_bills[bill]["sponsor_party"], new_bills[bill]["vote"]#, new_bills[bill]["confidence"]

	return new_bills


def classifier(bioguide_id):
	"""Combines data from classifying by party and by words to return predictions."""
	by_party 	= classifierByParty(bioguide_id)
	by_words	= classifierByWords(bioguide_id)
	predictions	= {}

	for bill in by_words:
		if by_words[bill]["vote"] == by_party[bill]["vote"]:
			predictions.update({bill: {"vote": by_party[bill]["vote"]}})
		elif by_words[bill]["confidence"]:
			predictions.update({bill: {"vote": by_words[bill]["vote"]}})
		else:
			predictions.update({bill: {"vote": by_party[bill]["vote"]}})

	print bioguide_id, vote_dict[bioguide_id]["name"], vote_dict[bioguide_id]["party"]
	for bill in predictions:
		print bill, by_party[bill]["sponsor_party"], predictions[bill]["vote"]


def classifierByWordsTEST(bioguide_id):
	"""Tests the algorithm against the dataset itself."""
	new_bills 	= getIDVoteHistory(bioguide_id) #Pull all bills from vote history.
	freq_dist 	= getIDFreqDist(bioguide_id)
	yea_common	= dict(freq_dist["yea"])
	nay_common	= dict(freq_dist["nay"])
	new_bill_votes = {}
	right = 0
	total = 0

	for bill in new_bills:
		bill_text = getBillWords(bill)
		yea_count = 0
		nay_count = 0
		for word in bill_text:
			if word in yea_common:
				yea_count += yea_common[word]
				#print bill, word, yea_common[word], "Yea: ", yea_count, "Nay: ", nay_count 
			if word in nay_common:
				nay_count += nay_common[word]
				#print bill, word, nay_common[word], "Yea: ", yea_count, "Nay: ", nay_count 
		if yea_count == nay_count:
			new_bill_votes.update({bill: {"vote": "EQUAL"}})
		elif yea_count > nay_count:
			new_bill_votes.update({bill: {"vote": "Yea"}})
		else:
			new_bill_votes.update({bill: {"vote": "Nay"}})

	for bill in new_bill_votes:
		if vote_dict[bioguide_id]["vote_history"][bill] == "Not Voting":
			pass
		else:
			if new_bill_votes[bill]["vote"] == vote_dict[bioguide_id]["vote_history"][bill]:
				right += 1
				total += 1
				#print 	"predicted: ", new_bill_votes[bill]["vote"], 
				#		"actual: ", vote_dict[bioguide_id]["vote_history"][bill], 
			else:
				total += 1
				#print 	"predicted: ", new_bill_votes[bill]["vote"], 
				#		"actual: ", vote_dict[bioguide_id]["vote_history"][bill], 

	print bioguide_id, "Right: ", right, "Total: ", total, "Percentage: ", float(right)/total
	

def main():
	"""Used for testing with different values."""
	loadData()
	#printCongressmen()
	#printBills()
	classifier("Z000018")
	classifierByWordsTEST("Z000018")
	#classifierByParty("Z000018")
	#classifierByWords("W000817")
	#print getIDFreqDist("Z000018")
	#printIDVoteHistory("W000817")
	#print full_texts["hr3521-113"]
	#getFreqDist("hr3521-113")
	#getFreqDist("hr4923-114")  #UPCOMING BILL


if __name__ == '__main__':
	main()


"""
Bill Version Reference:
	ENR - Enrolled Bill passed by both chambers
	ES 	- Engrossed in Senate
	EH 	- Engrossed in House
	ATS - Agreed to Senate
	CPS	- Considered and Passed Senate
	EAS - Engrossed Amendment Senate
	EAH - Engrossed Amendment House
	RFS - Referred in Senate
	RFS2- Referred in Senate 2?
	PCR - Placed on Calendar Senate
	RDS	- Received in Senate
	RS 	- Reported in Senate
	RH 	- Reported in House
	IS 	- Introduced in Senate
	IH	- Introduced in House
"""