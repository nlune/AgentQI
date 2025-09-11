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

def split_wordboxes_chunks(line_boxes):
    chunks_data = {'chunk_text': [], 'bboxes': [], 'pages': []}

    current = []
    headers = []
    curr_header = ""
    start_page = None
    
    bboxes = []

    for i, line_box in enumerate(line_boxes):
        line_text = line_box['text'].strip()
        bbox = line_box['bbox']
        page = line_box['page']
        word_data = {'text': line_text, 'bbox': bbox, 'page': page}
        
        if not line_text:
            continue
            
        header_check = is_header(line_text)
        
        # Check if we need to start a new chunk (header found or page change)
        if header_check or (start_page is not None and start_page != page):
            # Save current chunk if it exists
            if current:
                chunks_data['chunk_text'].append(' '.join([wd['text'] for wd in current]))
                chunks_data['bboxes'].append(merge_bboxes(bboxes))
                chunks_data['pages'].append(start_page)
                headers.append(curr_header.strip())
                bboxes = []

            # Start new chunk
            if header_check == -1:
                curr_header = ""
                current = []
            else:
                curr_header = line_text if header_check else ""
                bboxes.append(bbox)
                current = [word_data]
                start_page = page
        else:
        # Add to current chunk
            bboxes.append(bbox)
            start_page = page
            current.append(word_data)

    # Don't forget the last chunk
    if current:
        chunks_data['chunk_text'].append(' '.join([wd['text'] for wd in current]))
        chunks_data['bboxes'].append(merge_bboxes(bboxes))
        chunks_data['pages'].append(start_page)
        headers.append(curr_header.strip())
        
    return chunks_data, headers

def merge_bboxes(bboxes):
    if not bboxes:
        return None
    x0 = min(bbox[0] for bbox in bboxes)
    y0 = min(bbox[1] for bbox in bboxes)
    x1 = max(bbox[2] for bbox in bboxes)
    y1 = max(bbox[3] for bbox in bboxes)
    return [x0, y0, x1, y1]