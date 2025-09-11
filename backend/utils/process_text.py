
def process_text(text_path):
    with open(text_path, "r") as f:
        lines = f.readlines()
        
    stripped_lines = [line.strip() + '\n' for line in lines]
    # stripped_lines = [ " ".join(line.split()) + '\n' for line in lines]
    with open(text_path, "w") as f:
        f.writelines(stripped_lines)

    return "".join(stripped_lines)