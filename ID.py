from flask import Flask, render_template, request, send_file, url_for
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import time
import zipfile
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'png'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_id_card(csv_data, template_path, zip_file):
    # Open the template image
    template = Image.open(template_path)

    # Set up drawing context
    draw = ImageDraw.Draw(template)
    font = ImageFont.load_default()  # You can customize the font

    # Convert CSV data to a dictionary for easier processing
    csv_dict = csv_data.to_dict()

    # Define positions for each piece of information
    x_name = 280
    y_name = 51

    x_id = 280
    y_id = 110

    # Insert data from the CSV file into the template
    for key, value in csv_dict.items():
        if key == 'Name':
            text = f"{value}"
            position = (x_name, y_name)
            y_name += 30  # Adjust the vertical spacing as needed
        elif key == 'ID':
            text = f"{value}"
            position = (x_id, y_id)
            y_id += 30  # Adjust the vertical spacing as needed
        else:
            # Handle additional fields as needed
            continue

        draw.text(position, text, fill="black", font=font)

    # Save the modified image to a BytesIO buffer
    img_buffer = io.BytesIO()
    template.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Add the image to the zip file
    zip_info = zipfile.ZipInfo(f"id_card_{int(time.time())}.png")
    zip_info.date_time = time.localtime(time.time())[:6]
    zip_info.compress_type = zipfile.ZIP_DEFLATED
    zip_file.writestr(zip_info, img_buffer.getvalue())

@app.route('/', methods=['GET', 'POST'])
def id_card_generator():
    if request.method == 'POST':
        # Check if the post request has the file parts
        if 'csvFile' not in request.files or 'templateImage' not in request.files:
            return render_template('id_card_generator.html', message='Missing file parts')

        csv_file = request.files['csvFile']
        template_image = request.files['templateImage']

        # Check if the files are empty
        if csv_file.filename == '' or template_image.filename == '':
            return render_template('id_card_generator.html', message='Please select both files')

        # Check if the files have allowed extensions
        if allowed_file(csv_file.filename) and allowed_file(template_image.filename):
            # Save the files to the upload folder
            csv_filename = secure_filename(csv_file.filename)
            template_filename = secure_filename(template_image.filename)

            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
            template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)

            csv_file.save(csv_path)
            template_image.save(template_path)

            # Generate individual ID cards and add them to the zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                df = pd.read_csv(csv_path)
                for index, row in df.iterrows():
                    generate_id_card(row, template_path, zip_file)

            # Create a zip file containing the generated ID cards
            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='id_cards.zip')

        else:
            return render_template('id_card_generator.html', message='Invalid file type. Please upload a CSV and a PNG file.')

    return render_template('id_card_generator.html', message='Upload a CSV and a PNG file')

if __name__ == '__main__':
    app.run(debug=True)
