import os
import subprocess
import openai
import argparse
import tiktoken
import re
import csv
from datetime import datetime

def sanitize_filename(filename):
    """
    Remove or replace characters that are not allowed in Obsidian filenames.
    """
    # Define a regex pattern for disallowed characters
    disallowed_chars = r'[\\/*"<>:|?]'
    # Replace disallowed characters with an underscore
    sanitized = re.sub(disallowed_chars, "_", filename)
    return sanitized

def get_file_metadata(file_path):
    """Get original creation and modification time."""
    stat = os.stat(file_path)
    created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified_time = datetime.fromtimestamp(stat.mtime).isoformat()
    return created_time, modified_time

def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_tags_and_decision_from_openai(content):

    system_prompt = '''
        You are my note assistant. Your role is to manage, organize, and maintain only the most useful and relevant notes. You independently decide whether a note should be retained or discarded. Use the following criteria to make your decisions:

        ### **Criteria for Retaining Notes**
        1. **Actionable or Referable Information**: Notes that involve tasks, project details, references, or ideas that have ongoing relevance or future use.
        2. **Contextual Significance**: Notes containing meaningful information tied to larger goals, projects, or recurring needs (e.g., recipes, event details, or significant insights).
        3. **Creative or Professional Value**: Notes that contribute to creative, professional, or intellectual endeavors (e.g., story ideas, character dialogue, research findings, brainstorming, or work-related information).

        ### **Criteria for Rejecting Notes**
        1. **Ephemeral Notes**: Notes that were time-sensitive or relevant to a specific moment but no longer have value (e.g., reminders about past events or one-off tasks).
        2. **Low-Value Content**: Notes that are single words, fragments, or basic lists (e.g., grocery lists) unless they provide meaningful context or align with the retention criteria.
        3. **Duplicated or Outdated Information**: Notes that replicate existing, more complete information or are no longer applicable.
        4. **No Clear Use Case**: Notes that lack actionable, referable, or meaningful purpose after reasonable evaluation.

        ### **Process for Decision-Making**
        1. **Retention**: If a note meets retention criteria, organize it and store it appropriately.
        2. **Rejection**: If a note meets rejection criteria, discard it immediately without asking for confirmation. Briefly summarize why the note was rejected if necessary.
        3. **Ambiguity Handling**: If a note is unclear but appears to have potential value, attempt a brief clarification or infer its purpose based on context before making a decision.

        ### **Objective**
        Your priority is to maintain a clean and efficient notes system by rejecting unnecessary clutter while retaining only the most useful, meaningful, and relevant content.

        ### **Tag Creation Rules** 
        1. In my notes you may come across notes that read like stories, please tag them with 'writing'. 
        2. If you see links tag them with 'link'. 
        3. If it looks like the title of a book, comic, manga, paper, etc. use 'to-read'. 
        4. If it's a movie or show use 'to-watch'. 
        5. If the note is in another language, tag it with the language.
        6. Prioritize adding the special case tags.
        7. After that, use your descretion produce up to 5 additional tags with broad but relevant information about the note. These tags should be lowercase, single word, nouns. Do not wrap the list of tags in anything. Example: Instead of "daily journaling" pick "journal". Instead of "personal finance" pick "finance".
        
        ### **Output**
        You must always follow this output format. 
        decision: [use must the lowercase word 'keep' or 'trash']
        explanation: [Give a brief 20-30 word explanation why you decided 'keep' versus 'trash'.]
        tags: [list of tags you generated based on the tagging rules]
        
        Be thorough as possible. Thank you.
    '''

    user_prompt = f'Please analyze the note. Text:\n\n{content}'

    # the model to use.
    model = 'gpt-4o-mini'

    # get the encoding for the model and find the number of tokens in the user prompt
    num_tokens = num_tokens_from_string(user_prompt, model)

    # set the openai api key and organization from the environment variables
    openai.api_key = os.getenv('OPENAI_API_KEY')
    openai.organization = os.getenv('OPENAI_ORG')

    try: 
        responseStream = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                },
            ],
            temperature=1,
            max_tokens=4095,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stream=True,
        )

        # Print the response stream
        collected_content = []
        print (f'\nResponse Stream:\n')
        for chunk in responseStream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                collected_content.append(chunk.choices[0].delta.content)

        # Parse response from OpenAI
        response_content = ''.join(collected_content)

        # Split the response content into lines
        lines = response_content.splitlines()

        # Initialize default values
        decision = "keep"
        explanation = ""
        tags = []

        # Parse lines for decision, explanation, and tags
        for line in lines:
            if line.lower().startswith("decision:"):
                decision = line.lower().split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                explanation = line.lower().split(":", 1)[1].strip()
            elif line.lower().startswith("tags:"):
                if isinstance(line, str):
                    tag_string = line.split(":", 1)[1].strip()  # Ensure it's a string before calling split
                    tags = [tag.strip() for tag in tag_string.split(",")]
                else:
                    print(f"Error: Expected string, but found {type(line)}")

        # Print results for debugging
        print("Decision:", decision)
        print("Explanation:", explanation)
        print("Tags:", tags)
        print("Tokens:", num_tokens)

        return decision, explanation, tags, num_tokens
    except Exception as e:
        print(f"Error generating decision and tags: {e}")
        return "keep", "Error in explanation", ["misc"]

def clean_text(text):
    # Replace smart quotes with regular quotes
    text = text.replace('“', '"').replace('”', '"')  # Replace curly double quotes with straight double quotes
    text = text.replace('‘', "'").replace('’', "'")  # Replace curly single quotes with straight apostrophes
    text = text.replace('–', '-')  # Replace en dash with hyphen
    text = text.replace('—', '-')  # Replace em dash with hyphen

    # Remove any other non-ASCII or non-standard characters (optional)
    #text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Normalize spaces (in case there are non-breaking spaces or other weird space characters)
    #text = text.replace('\u00A0', ' ')  # Replace non-breaking space with normal space
    #text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with one

    return text

def process_txt_to_md(input_path, keep_path, junk_path):
    """
    Process a .txt file by converting it to Markdown using pandoc,
    determining whether to keep or trash the note, generating tags,
    and adding a YAML frontmatter.
    """
    if not os.path.exists(input_path):
        print(f"Input file {input_path} does not exist.")
        return

    # Read the original content to evaluate
    try: 
        with open(input_path, "r", encoding='utf-8') as f:
            content_raw = f.read()
    except UnicodeDecodeError as e:
        print(f"Error reading file: {e}")

    # Generate decision, explanation, and tags using OpenAI API
    decision, explanation, tags, num_tokens = get_tags_and_decision_from_openai(content_raw)

    #strip out special characters.
    content = clean_text(content_raw)

    # default with junk path
    output_path = junk_path
    if decision == "trash":
        print(f"Skipping {input_path}: Marked as trash ({explanation}).")

        # Write back to the Markdown file
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(content)

    elif decision == "keep":
        output_path = keep_path

        # Convert the tags list into a YAML-compatible format
        tags_yaml = "\n  - ".join(tags) if tags else "[]"

        # Ensure the tags list is in proper YAML format
        tags_yaml = "\n  - " + tags_yaml if tags else "[]"

        # Get the original file's last modified time
        original_date = datetime.fromtimestamp(os.path.getmtime(input_path)).strftime("%Y-%m-%d")

        # Create the YAML header
        yaml_header = (
            f"---\n"
            f"tags:{tags_yaml}\n"
            f"date: {original_date}\n"
            f"---\n\n"
        )
        
        # Combine YAML frontmatter and file content
        content_with_header = yaml_header + content

        # Write back to the Markdown file
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(content_with_header)

        print(f"Processed and converted: {input_path} -> {output_path}")

    return {'filename': input_path, 'decision': decision, 'explanation': explanation, 'tags': ",".join(tags), 'num_tokens': num_tokens }

def process_files(input_root, output_root):
    """
    Process all .txt files in nested folders, separating into 'keep' and 'junk'.
    """
    # Create the keep and junk directories in the output directory
    keep_dir = os.path.join(output_root, "keep")
    junk_dir = os.path.join(output_root, "junk")
    os.makedirs(keep_dir, exist_ok=True)
    os.makedirs(junk_dir, exist_ok=True)

    metadata = []

    # Regex to match and remove the timestamp portion
    timestamp_pattern = r"-\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}Z"

    # Process all .txt files in the input directory
    for root, _, files in os.walk(input_root):
        for file in files:
            if file.endswith(".txt"):
                try: 

                    input_path = os.path.normpath(os.path.join(root, file))

                    # strip any unncessary stuff off of the filename.
                    new_filename = re.sub(timestamp_pattern, "", file)
                    output_file = sanitize_filename(new_filename.replace(".txt", ".md"))

                    # Convert and process the file
                    keep_output_path = os.path.join(keep_dir, output_file)
                    junk_output_path = os.path.join(junk_dir, output_file)

                    # Check if the file already exists in the keep directory
                    if os.path.exists(keep_output_path) or os.path.exists(junk_output_path):
                        print(f"Skipping {output_file} as it already exists in the keep directory.")
                        continue  # Skip processing this file if it already exists in keep

                    return_val = process_txt_to_md(input_path, keep_output_path, junk_output_path)
                    metadata.append(return_val)
                except Exception as e: 
                    print(f"Error looping through files. File is {file}. Exception thrown is {e}\n")

    # Output CSV of all the metadata for review
    headers = ['filename', 'decision', 'explanation', 'tags', 'num_tokens']

    if len(metadata) > 0: 
        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Append the timestamp to the filename
        meta_filename = f'notes-metadata_{timestamp}'

        csv_output_file = os.path.join(keep_dir, meta_filename)

        output_csv_from_json(csv_output_file, True, headers, metadata)
        print(f'Wrote {csv_output_file}.csv. Process Complete.\n')

def output_csv_from_json(filename, make_new_file, header, data):
    # Append to a CSV file from the JSON data. Can handle data being an object or list.

    filename = filename + '.csv'

    # overwrite the file if it exists
    if make_new_file:
        # create the file
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()

            # write the data
            if (isinstance(data, list)):
                for row in data:
                    try: 
                        writer.writerow(row)
                    except Exception as e: 
                        print(f"CSV output failed on row {row}. Exception thrown is {e}\n")

            elif (isinstance(data, dict)):
                writer.writerow(data)
        return

    # append to the file
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)

        # write the data
        if (isinstance(data, list)):
            for row in data:
                writer.writerow(row)
        elif (isinstance(data, dict)):
            writer.writerow(data)


if __name__ == "__main__":
    # Set up argument parser for command-line options
    parser = argparse.ArgumentParser(description="Process .txt files and organize into keep/junk folders.")
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input directory containing .txt files."
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the output directory where keep and junk folders will be created."
    )
    
    args = parser.parse_args()

    # Validate the input directory
    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist.")
        exit(1)

    # Validate or create the output directory
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)

    # Process the files
    process_files(args.input, args.output)

