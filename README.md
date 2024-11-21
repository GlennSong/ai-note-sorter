# Text File Processor for Obsidian Notes

This script processes `.txt` files in a given input directory, converts them into Markdown format (`.md`), evaluates their content using OpenAI's API, and organizes them into "keep" and "junk" folders. It also adds a YAML front matter with tags and metadata to the "keep" files, allowing for better organization in Obsidian.

## Features:
- **File Conversion**: Converts `.txt` files into Markdown (.md) format.
- **Content Evaluation**: Uses OpenAI’s API to analyze each file, generating tags and deciding whether the note is worth keeping or should be discarded.
- **Metadata Extraction**: Extracts creation and modification timestamps, and appends them as YAML front matter in the Markdown files.
- **Smart File Handling**: Automatically sanitizes filenames to avoid issues with Obsidian compatibility (e.g., removes disallowed characters).
- **CSV Logging**: Outputs a CSV file containing metadata about each processed note, including decision, explanation, tags, and token count.

## Prerequisites:
Before running this script, ensure that you have the following:
- **Python 3.6+** installed on your system.
- **OpenAI API Key**: You'll need an OpenAI API key. Store this in your environment variables as `OPENAI_API_KEY`.
- **OpenAI Organization ID**: Store your OpenAI organization ID in your environment variables as `OPENAI_ORG`.

## Installation:

1. Clone the repository or download the script.
2. Install required dependencies:
    ```bash
    pip install openai tiktoken
    ```

## Usage:

Run the script from the command line, passing the input and output directories as arguments:

```bash
python process_notes.py -i <input_directory> -o <output_directory>
```

### Arguments:
- `-i` or `--input`: The path to the directory containing `.txt` files you want to process.
- `-o` or `--output`: The path to the directory where processed files will be saved. This will create `keep` and `junk` folders within the specified output directory.

### Example:
```bash
python process_notes.py -i /path/to/input -o /path/to/output
```

The script will:
- Read all `.txt` files in the specified input directory.
- Process each file, making decisions whether to "keep" or "trash" based on content analysis.
- Save the converted files into the `keep` or `junk` folder within the output directory.
- Generate a CSV file containing metadata for the processed files.

## File Structure:

- **Input Directory**: Contains `.txt` files for processing.
- **Output Directory**: Contains two subdirectories:
    - `keep`: Files that are deemed useful and tagged.
    - `junk`: Files that are discarded.
    - Additionally, a CSV metadata file will be saved inside the `keep` directory.

### Example Directory Structure:
```
/path/to/output/
├── keep/
├── junk/
└── notes-metadata_2024-11-20_14-30-00.csv
```

## Functionality:

### `sanitize_filename(filename)`
- **Purpose**: Sanitizes filenames to remove or replace characters that are not allowed in Obsidian filenames (e.g., `|`, `<`, `>`, etc.).

### `get_file_metadata(file_path)`
- **Purpose**: Retrieves the creation and modification timestamps of a file.

### `num_tokens_from_string(string, model)`
- **Purpose**: Returns the number of tokens in a text string, using the specified OpenAI model.

### `get_tags_and_decision_from_openai(content)`
- **Purpose**: Analyzes the content of the note using OpenAI's API, providing a decision ("keep" or "trash"), a brief explanation, and relevant tags.

### `clean_text(text)`
- **Purpose**: Cleans and normalizes the text by replacing smart quotes, dashes, and other characters with standard ASCII equivalents.

### `process_txt_to_md(input_path, keep_path, junk_path)`
- **Purpose**: Converts a `.txt` file to `.md`, adds metadata in YAML format, and determines whether to keep or discard the note.

### `process_files(input_root, output_root)`
- **Purpose**: Recursively processes all `.txt` files in the input directory, calling `process_txt_to_md` for each file, and organizing them into "keep" or "junk" folders.

### `output_csv_from_json(filename, make_new_file, header, data)`
- **Purpose**: Writes metadata about the processed notes into a CSV file.

## License:
This project is licensed under the MIT License - see the LICENSE file for details.
