import bisect
import math
import os
import re
import sys
import time

from collections import defaultdict
from nltk.corpus import stopwords
from Stemmer import Stemmer

def get_page_title_by_doc_id(doc_no):
	doc_no = int(doc_no)
	with open(data_dir+'/titles/'+str((doc_no+9999)//10000)+'.txt','r') as title_file:
		req_title = ""
		line_num = doc_no%10000 if doc_no%10000 != 0 else 10000
		for i in range(line_num):
			req_title = title_file.readline().strip('\n ')
		return req_title


def simple_text_preprocessing(text):
    '''Tokenization, stemming and removal of stop words from text'''
    raw_tokens = re.split(r'[^A-Za-z0-9]+', text)
    pre_tokens = [word.lower() for word in raw_tokens if len(word)>1]
    return [
        STEMMER.stemWord(word) for word in pre_tokens
        if word not in STOP_WORDS_SET]


def get_index_doc_num_from_secondary_index(field_type, word):
	'''Returns the index file number for the word of given field
	type by looking at the secondary index (already in memory)
	corresponding to it.
	'''
	return bisect.bisect_right(secondary_index[field_type], word)


def get_posting_list_by_word_and_field_type(field_type, word):
	index_file_num = get_index_doc_num_from_secondary_index(field_type, word)
	with open(data_dir+'/'+field_type+'/'+str(index_file_num)+'.txt', 'r') as index_file:
		line = index_file.readline().strip('\n')
		while line:
			line = line.split(" ")
			if line[0] > word:
				return []
			elif line[0] == word:
				return line[1:]
			line = index_file.readline().strip('\n')
	return []


def process_query(word_dict, num_results):
	'''Query processing helper function. Recieves tokens under all tags
	relevant for the query and returns the top docIDs of the search result'''
	term_freq_dict = defaultdict(lambda : [0]*8)
	for field, tokens in word_dict.items():
		field_idx = field_type_to_index[field]
		for token in tokens:
			posting_list = get_posting_list_by_word_and_field_type(field, token)
			curr = len(posting_list)
			for term in posting_list:
				[doc_id, count] = term.split(':')
				term_freq_dict[doc_id][7] += math.log(int(count)+1) * math.log(total_docs/int(curr))
				term_freq_dict[doc_id][field_idx+1] += 1
				term_freq_dict[doc_id][0] = max(term_freq_dict[doc_id][1:7])
	total_results = len(term_freq_dict)
	results = sorted(term_freq_dict.items(), key = lambda x : (x[1], x[0]), reverse=True)
	final_result = [x[0] for x in results]
	return (final_result[:min(num_results, len(results))], total_results)

if len(sys.argv) < 3:
	print('Insufficient Arguments provided')
	exit(0)

STOP_WORDS_SET = set(stopwords.words('english'))
STEMMER = Stemmer('porter')
data_dir = os.path.join('.', "data")
field_type_to_index = {
    'title': 0, 'body': 1, 'ref': 2, 'infobox': 3, 'link': 4, 'category': 5
}
secondary_index = {
	'title': [], 'body': [], 'ref': [], 'infobox': [], 'link': [], 'category': []
}

# (1) Store the Secondary index in memory
for field in field_type_to_index.keys():
	with open(data_dir + '/sec_ind/' + field, 'r') as open_file:
		lines = open_file.readlines()
		secondary_index[field] = [line.strip('\n') for line in lines]

# (2) Start processing the query
f = open('total_docs.txt','r')
total_docs = int(f.readline().strip('\n'))
f.close()
read_queries_file_path = sys.argv[1]
write_result_file_path = sys.argv[2]
with open(read_queries_file_path, 'r') as queries_file:
	with open(write_result_file_path,'w+') as result_file:
		query = queries_file.readline().strip('\n')
		while query: # Read all lines in the file till EOF
			all_tokens = []
			st_time = time.time()
			query_words = query.split(',')
			num_results = query_words[0].strip(' \n')
			raw_query = query_words[1].strip(' \n')
			num_results = int(num_results)
			top_doc_ids = []
			tmp_dict = {}
			if ':' not in raw_query:
				tokens = simple_text_preprocessing(raw_query)
				all_tokens = tokens
				tmp_dict = {'title': tokens, 'body': tokens}
			else:
				split_raw_query = raw_query.split(':')
				for key in field_type_to_index.keys():
					tag = key[0] # like 't', 'b', 'r', 'i' etc
					if (tag + ':') not in raw_query:
						continue
					for i in range(1,len(split_raw_query)):
						if split_raw_query[i-1][-1] == tag:
							tmp_dict[key] = simple_text_preprocessing(split_raw_query[i])
							all_tokens += tmp_dict[key]
							break
			(top_doc_ids, total_results) = process_query(tmp_dict, num_results)
			
			if len(top_doc_ids) == 0:
				tmp_dict = {
					'title': all_tokens,
					'body': all_tokens,
					'ref': all_tokens,
					'infobox': all_tokens,
					'link': all_tokens,
					'category': all_tokens
				}
				(top_doc_ids, total_results) = process_query(tmp_dict, num_results)

			result_file.write('Results for query: "'+raw_query+'"\n')
			result_file.write('------------------- ')
			if len(top_doc_ids) == 0:
				result_file.write('No results found matching this query :(\n')
			else:
				result_file.write('Showing best %d results (%d found total) :\n'%(num_results,total_results))
				for doc_id in top_doc_ids:
					result_file.write(
						'Doc Id: '+str(doc_id) + ', Doc Title:'
						' ' + str(get_page_title_by_doc_id(doc_id))+'\n')
			total_time = time.time() - st_time
			result_file.write('Total query time      : '+"{:.2f}".format(total_time)+'s\n')
			result_file.write(
				'Average time per result: '+"{:.2f}".format(total_time/num_results)+'s\n\n\n')
			query = queries_file.readline().strip('\n')
