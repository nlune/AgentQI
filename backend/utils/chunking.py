import re

header_texts = ['Material Description', 'Certified Values', 'Informative Value', 'Handling and Safety Instructions', 'Means of Accepted Data Sets']



def is_header(line):
    line = line.strip()
    if not line:
        return False
    if line in header_texts:
        return True
    if re.search(r'(?:\bPage\s+\d+\s+of\s+\d+\b)|(?:CERTIFICATE\s+BAM-[^\s]+)', line):
        return -1
    # no digits
    if re.search(r"[0-9!\#$%&'()*+,\-./:;<=>?@\[\]^_`]", line):
        return False
    words = line.split()
    if len(words) > 3:
        return False
    if not line[0].isupper():
        return False
    return True

def split_into_chunks(text):
    chunks = []
    headers = []
    current = []
    curr_header = ""
    for i, line in enumerate(text.splitlines(keepends=True)):
        if not line.strip():
            continue
        header_check = is_header(line)
        if header_check:
            # start new chunk
            if current:
                chunks.append(''.join(current))
                headers.append(curr_header.strip())
            if header_check == -1:
                curr_header = ""
                current = []
            else:
                curr_header = line
                current =[line]

        else:
            current.append(line)
    if current:
        chunks.append(''.join(current))
    return chunks, headers

def split_wordboxes_chunks(all_word_boxes):
    chunks = []
    bboxes = []
    current = []
    headers = []
    curr_header = ""
    
    for i, word_data in enumerate(all_word_boxes):
        word_text = word_data['text'].strip()
        if not word_text:
            continue
        header_check = is_header(word_text)
        if header_check:
            # start new chunk
            if current:
                chunks.append(' '.join([wd['text'] for wd in current]))
                bboxes.append(current)
                headers.append(curr_header.strip())
            if header_check == -1:
                curr_header = ""
                current = []
            else:
                curr_header = word_text
                current = [word_data]
        else:
            current.append(word_data)