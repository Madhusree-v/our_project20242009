# Import necessary libraries and modules
from flask import Flask, request, jsonify, render_template  # Flask modules for web app functionalities
from werkzeug.utils import secure_filename  # Utility to secure filenames
import pytesseract  # OCR tool for text extraction from images
from PIL import Image  # Python Imaging Library for image processing
import os  # Library for operating system functionalities
import json  # Library for JSON handling
import pdfplumber  # Library for extracting text from PDF files
import re  # Regular expression library for string searching
from whoosh.index import create_in  # Function to create a Whoosh index
from whoosh.fields import Schema, TEXT  # Schema and field types for indexing
from whoosh.qparser import QueryParser  # Query parsing for search
from whoosh.writing import AsyncWriter  # Async writing to the index

# Initialize the Flask app with specified template and static folders
app = Flask(__name__, template_folder='templates', static_folder='static')

# Define the upload folder for storing uploaded files
UPLOAD_FOLDER = 'uploads/'
# Specify allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'jfif', 'webp', 'bmp', 'pdf'}
# Set the upload folder in the app's configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if the upload folder exists; create it if not
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define a Whoosh schema for indexing extracted text
schema = Schema(content=TEXT(stored=True))  # Create a schema with a single TEXT field
# Define the directory for the index
index_dir = "index"
# Check if the index directory exists; create it if not
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
# Create the Whoosh index using the defined schema
ix = create_in(index_dir, schema)

# Helper function to check if the uploaded file has an allowed extension
def allowed_file(filename):
    # Check if there's a dot in the filename and if the extension is in the allowed set
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to extract text from an image using Tesseract OCR
def extract_text_from_image(image_path):
    try:
        # Open the image file
        image = Image.open(image_path)
        # Use Tesseract to convert the image to a string
        text = pytesseract.image_to_string(image)
        return text  # Return the extracted text
    except Exception as e:
        return str(e)  # Return the error message if something goes wrong

# Helper function to extract text from a PDF file using pdfplumber
def extract_text_from_pdf(pdf_path):
    text = ""  # Initialize an empty string for the extracted text
    try:
        # Open the PDF file
        with pdfplumber.open(pdf_path) as pdf:
            # Loop through each page in the PDF
            for page in pdf.pages:
                # Extract text from the current page
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"  # Append the text to the result
    except Exception as e:
        return f"Error extracting text: {e}"  # Return error message if extraction fails
    return text  # Return the complete extracted text

# Function to index the extracted text using Whoosh
def index_text(text):
    # Create an asynchronous writer to write to the index
    writer = AsyncWriter(ix)
    # Add a document to the index with the extracted text
    writer.add_document(content=text)
    writer.commit()  # Commit changes to the index

# Function to find lines in the extracted text containing a specific keyword
def find_keyword_in_text(text, keyword):
    lines = text.split('\n')  # Split the text into lines
    # Use a set comprehension to find lines that match the keyword, ignoring case
    keyword_lines = {line for line in lines if re.search(r'\b{}\b'.format(re.escape(keyword)), line, re.IGNORECASE)}
    return keyword_lines  # Return the set of matching lines

# Function to convert the extracted text into CSV format
def text_to_csv(text):
    lines = text.splitlines()  # Split the text into individual lines
    csv_rows = []  # Initialize a list to hold CSV rows

    # Loop through each line in the text
    for line in lines:
        if line.strip():  # Skip empty lines
            fields = line.strip().split()  # Split the line into fields based on whitespace
            csv_rows.append(','.join(fields))  # Join fields with commas to form a CSV row

    # Join all CSV rows with newlines to create the final CSV output
    csv_output = '\n'.join(csv_rows)
    return csv_output  # Return the CSV formatted text

# Route to render the home page
@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML template for the home page

# Route to handle file uploads, text extraction, indexing, and output formatting
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the request contains a file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400  # Return error if no file is found
    file = request.files['file']  # Get the file from the request
    format_type = request.form.get('format')  # Get the desired output format from the form

    # Check if the filename is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400  # Return error if no file is selected

    # Check if the file has an allowed extension
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Secure the filename to prevent injection attacks
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Construct the full file path
        file.save(file_path)  # Save the uploaded file to the designated upload folder

        # Determine whether the file is a PDF or an image, and extract text accordingly
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)  # Extract text from the PDF file
        else:
            text = extract_text_from_image(file_path)  # Extract text from the image file

        index_text(text)  # Index the extracted text for future searching

        # Handle different output formats: JSON, CSV, or plain text
        if format_type == 'json':
            json_output = json.dumps({'text': text}, indent=4)  # Format the text as JSON
            return jsonify({'json': json_output})  # Return the JSON response
        elif format_type == 'csv':
            csv_output = text_to_csv(text)  # Convert the text to CSV format
            return jsonify({'csv': csv_output})  # Return the CSV response
        else:  # Default to returning plain text if no format is specified
            return jsonify({'text': text})  # Return the plain text response

    return jsonify({'error': 'Invalid file type'}), 400  # Return error if the file type is not allowed

# Route to handle search requests
@app.route('/search', methods=['POST'])
def search_text():
    data = request.json  # Get JSON data from the request
    query_str = data.get('query', '').strip()  # Extract the search query from the JSON data

    # Check if a search query has been provided
    if not query_str:
        return jsonify({'error': 'Query not provided'}), 400  # Return error if no query is provided

    results = set()  # Initialize a set to hold unique search results
    with ix.searcher() as searcher:  # Create a searcher to query the index
        query = QueryParser("content", ix.schema).parse(query_str)  # Parse the search query
        search_results = searcher.search(query, limit=None)  # Perform the search on the indexed content

        # Loop through the search results and find lines containing the search query
        for hit in search_results:
            keyword_lines = find_keyword_in_text(hit['content'], query_str)  # Find matching lines
            results.update(keyword_lines)  # Add matching lines to the results set

    results = sorted(results)  # Sort the results alphabetically

    return jsonify({'results': results})  # Return the sorted results as a JSON response

# Run the Flask app in debug mode, enabling live reloading and error tracking
if __name__ == '__main__':
    app.run(debug=True)
