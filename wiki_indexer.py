import nltk
import os
import re
import time
import xml.sax

from collections import defaultdict
from Stemmer import Stemmer

invertedIndex = {
    'title': defaultdict(lambda: defaultdict(int)),
    'body': defaultdict(lambda: defaultdict(int)), 
    'ref': defaultdict(lambda: defaultdict(int)),
    'infobox': defaultdict(lambda: defaultdict(int)),
    'link': defaultdict(lambda: defaultdict(int)),
    'category': defaultdict(lambda: defaultdict(int))
}

def simple_text_preprocessing(text):
    '''Tokenization, stemming and removal of stop words from text'''
    raw_tokens = re.split(r'[^A-Za-z0-9]+', text)
    global total_dump_tokens
    total_dump_tokens += len(raw_tokens)
    pre_tokens = [word.lower() for word in raw_tokens if len(word)>1]
    return [
        STEMMER.stemWord(word) for word in pre_tokens
        if word not in STOP_WORDS_SET]


def tokenize_single_page_text(text):
    '''Return preprocessed text by infobox, category, links and references'''

    text = re.sub('\w+:\/\/[A-Za-z\/.0-9-_\~\:\&\?\=\%]+', "", text)

    # References
    raw = text.split("==References==")
    refs = []
    if len(raw) <= 1:
        refs = []
    else:
        raw = raw[1].split("\n")
        for line in raw:
            if ("[[Category" in line) or ("==" in line) or ("DEFAULTSORT" in line):
                break
            refs.append(line)
        refs = simple_text_preprocessing(" ".join(refs))
    
    # External Links
    links = []
    lines = text.split("==External links==")
    raw_lines = []
    if len(lines) > 1:
        raw_lines = [line for line in lines[1].split('\n') if line and line[0] == '*']
        links = simple_text_preprocessing(" ".join(raw_lines))
                
    # Infoboxes
    text = re.sub('<ref(.*?)<\/ref>', "", text)
    text = re.sub('<ref(.*?)\/>', "", text)
    infoboxes = []
    lines = text.split("{{Infobox")
    raw_lines = []
    if len(lines)>1:
        lines = lines[1].split('\n')
        for line in lines:
            if line == '}}':
                break
            else:
                raw_lines.append(line)
    infoboxes += simple_text_preprocessing(" ".join(raw_lines))

    # Categories
    categories = re.findall(r"\[\[Category:(.*)\]\]", text)
    categories = simple_text_preprocessing(" ".join(categories))

    # Body
    body = simple_text_preprocessing(text)

    return sorted(categories), sorted(refs), sorted(infoboxes), sorted(links), sorted(body)


def add_to_inverted_index(tag, tokens, doc_id):    
    for token in tokens:
        invertedIndex[tag][token][doc_id] += 1


def process_single_page(title, text, page_num):
    titles = simple_text_preprocessing(title)
    categories, refs, infoboxes, links, words = tokenize_single_page_text(text)        

    # adding to index
    add_to_inverted_index('title', titles, page_num)
    add_to_inverted_index('body', words, page_num)
    add_to_inverted_index('ref', refs, page_num)
    add_to_inverted_index('infobox', infoboxes, page_num)
    add_to_inverted_index('link', links, page_num)
    add_to_inverted_index('category', categories, page_num)


def write_index_to_file(file_num):
    '''write the InvertedIndex currently in memory to files on disk.'''

    global invertedIndex
    for tag in field_type_to_index.keys():
        with open(data_dir + "/" + tag + "/" + str(file_num) + ".txt", "w+") as temp:
            for key, val in sorted(invertedIndex[tag].items()):
                posting_list = [key]
                posting_list += [str(doc_id)+ ":" +str(count)
                    for doc_id, count in sorted(val.items())]
                temp.write(" ".join(posting_list)+"\n")

    # We erase the older Index information from the memory.
    invertedIndex = {
        'title': defaultdict(lambda: defaultdict(int)),
        'body': defaultdict(lambda: defaultdict(int)), 
        'ref': defaultdict(lambda: defaultdict(int)),
        'infobox': defaultdict(lambda: defaultdict(int)),
        'link': defaultdict(lambda: defaultdict(int)),
        'category': defaultdict(lambda: defaultdict(int))
    }


def write_titles_to_file(file_num, titles):
    '''write the titles currently in memory to files on disk.'''
    with open(data_dir + "/titles" + "/" + "1.txt", "a+") as temp:
        temp.write("\n".join(titles)+'\n')


class PageHandler(xml.sax.ContentHandler):

    def __init__(self):
        self.page_title = ''
        self.page_text = ''
        self.titles_for_the_block = []
        self.is_title_tag = False
        self.is_text_tag = False
        self.wiki_pages_processed = 0
        self.data_files_written = 0

    def startElement(self, tag, attributes):
        if tag == 'title':
            self.is_title_tag = True
            self.page_title = ''
        elif tag == 'text':
            self.page_text = ''
            self.is_text_tag = True

    def endElement(self, tag):
        if tag == 'page':
            self.wiki_pages_processed += 1
            (self.titles_for_the_block).append(self.page_title)
            process_single_page(
                self.page_title, self.page_text, self.wiki_pages_processed)
            if self.wiki_pages_processed % 10000 == 0:
                self.data_files_written += 1
                write_index_to_file(self.data_files_written)
                write_titles_to_file(
                    self.data_files_written, self.titles_for_the_block)
                self.titles_for_the_block = []
        elif tag == 'title':
            self.is_title_tag = False
        elif tag == 'text':
            self.is_text_tag = False
        elif tag == 'mediawiki' :
            self.data_files_written += 1
            write_index_to_file(self.data_files_written)
            write_titles_to_file(
                    self.data_files_written, self.titles_for_the_block)
            self.titles_for_the_block = []

    def characters(self, content):
        if self.is_title_tag:
            self.page_title += content
        elif self.is_text_tag:
            self.page_text += content

STOP_WORDS_SET = set(nltk.corpus.stopwords.words('english'))
STEMMER = Stemmer('porter')

total_dump_tokens = 0
total_inverted_index_tokens = 0

field_type_to_index = {
    'title' : 0, 'body' : 1, 'ref' : 2, 'infobox' : 3, 'link' : 4, 'category': 5
}


# Make the required folders
data_dir = os.path.join('.', "data")
if os.path.isdir(data_dir) == False:
    os.mkdir(data_dir)
if os.path.isdir(data_dir + "/titles") is False:
    os.mkdir(data_dir + "/titles")
for field in field_type_to_index.keys():
    if os.path.isdir(data_dir + "/" + field) == False:
        os.mkdir(data_dir + "/" + field)


# Creating the parser
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
Handler = PageHandler()
parser.setContentHandler(Handler)


# Parsing and Creating preliminary index.
overall_start_time = time.time()
print('Starting...')
dump_files = [
    ('./uncompressed-dump/'+file, os.path.getsize('./uncompressed-dump/'+file)) 
    for file in os.listdir('./uncompressed-dump')]
dump_files.sort(key=lambda filename: filename[1], reverse=False)
for count,fname in enumerate(dump_files):
    local_start = time.time()
    print('Parsing file ' + str('(')+str(count+1)+str('):'),fname[0],'of size',fname[1]/1048576,'MB')
    parser.parse(fname[0])
    print('Completed parsing file '+ str('(')+str(count+1)+str(').'), 'in', time.time()-local_start,'seconds')

print("\n##########################################################")
print('Preliminary indexing complete after',time.time()-overall_start_time,'seconds\n')


# Merge and split the index files to create final index.
merge_st_time = time.time()

def merge_func(n1, n2, field_type):
    f1_name = data_dir + "/" + field_type + "/" + str(n1) + ".txt"
    f2_name = data_dir + "/" + field_type + "/" + str(n2) + ".txt"
    tmp_name = data_dir + "/" + field_type + "/" + "temp.txt"
    final_name = data_dir + "/" + field_type + "/" + str(n2//2) + ".txt"
    final = open(tmp_name, "w+")
    file1 = open(f1_name, "r")
    file2 = open(f2_name, "r")
    line1 = file1.readline().strip('\n')
    line2 = file2.readline().strip('\n')
    while line1 and line2:
        word1 = line1.split(' ')[0]
        word2 = line2.split(' ')[0]
        if word1 < word2:
            final.write(line1 + '\n')
            line1 = file1.readline().strip('\n')
        elif word2 < word1:
            final.write(line2 + '\n')
            line2 = file2.readline().strip('\n')
        else:
            list1 = ' '.join(line1.split(' ')[1:])
            list2 = ' '.join(line2.split(' ')[1:])
            final.write(word1 + ' ' + list1 + ' ' + list2 + '\n')
            line1 = file1.readline().strip('\n')
            line2 = file2.readline().strip('\n')
    while line1:
        final.write(line1)
        line1 = file1.readline()
    while line2:
        final.write(line2)
        line2 = file2.readline()
    os.remove(f1_name)
    os.remove(f2_name)
    os.rename(tmp_name, final_name)

all_fields_list = list(field_type_to_index.keys())
all_fields_list.append('titles')
print('Starting to prepare final index by merging, splitting of preliminary index..')
for field_type in all_fields_list:
    if field_type != 'titles':
        num_files_present = Handler.data_files_written
        while num_files_present > 1:
            for i in range(1, num_files_present+1, 2):
                if i == num_files_present:
                    f1_name = data_dir + "/" + field_type + "/" + str(i) + ".txt"
                    f2_name = data_dir + "/" + field_type + "/" + str((i+1)//2) + ".txt"
                    os.rename(f1_name, f2_name)
                else:
                    merge_func(i, i+1, field_type)
            num_files_present = (num_files_present + 1) // 2


    os.rename(
        data_dir + "/" + field_type + "/1.txt",
        data_dir + "/" + field_type + "/final.txt"
    )

    unique_tokens = 0
    current_file_count = 1
    with open(data_dir + "/" + field_type + "/final.txt", "r") as temp:
        line = temp.readline()
        while line:
            line_count = 0
            new_file = open(data_dir + "/" + field_type + "/" + str(current_file_count) + ".txt", "w+")
            while line_count < 10000 and line:
                new_file.write(line)
                line = temp.readline()
                line_count += 1
                unique_tokens += 1
            new_file.close()
            current_file_count += 1
    os.remove(data_dir + "/" + field_type + "/final.txt")
    print('----',' Total:',current_file_count-1,'index files created for',field_type,'with',unique_tokens,'unique_tokens')

    if field_type == 'titles':
        continue    
    
    if os.path.isdir(data_dir + "/sec_ind") == False:
        os.mkdir(data_dir + "/sec_ind")
    with open(data_dir + "/sec_ind/" + field_type, "w+") as sec_file:
        for i in range(1,current_file_count):
            with open(data_dir + "/" + field_type + "/" + str(i) + '.txt', "r") as read_file:
                sec_file.write(read_file.readline().split(' ')[0]+'\n')

print('Merging, splitting and creating secondary index took',time.time()-merge_st_time,'\n')

print('Final index ready after',time.time()-overall_start_time,'seconds')

print('total wikipedia pages processed', Handler.wiki_pages_processed)
f = open('total_docs.txt','w+')
f.write(str(Handler.wiki_pages_processed)+'\n')
f.close()
print('total number of token encountered in the dump', total_dump_tokens)

f = open('InvertedIndexStat.txt','w+')
f.write('total number of tokens in the dump'+str(total_dump_tokens)+'\n')
f.close()