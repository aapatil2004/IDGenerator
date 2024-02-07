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
ALLOWED_EXTENSIONS = {'csv', 'png', 'jpeg'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def justify_text(draw, text, position, width, font, fill_color, justification="left"):
    text_width, text_height = draw.textsize(text, font)

    if justification == "left":
        x = position[0]
    elif justification == "center":
        x = position[0] + (width - text_width) // 2
    elif justification == "right":
        x = position[0] + (width - text_width)
    else:
        raise ValueError("Invalid justification. Use 'left', 'center', or 'right'.")

    y = position[1]

    draw.text((x, y), text, font=font, fill=fill_color)

def generate_id_card(csv_data, template_path, zip_file):
    template = Image.open(template_path)
    draw = ImageDraw.Draw(template)
    font_path = "C:/Windows/Fonts/Calibri.ttf"
    
    name_font_size = 70
    portfolio_font_size = 50
    
    name_font = ImageFont.truetype(font_path, name_font_size)
    portfolio_font = ImageFont.truetype(font_path, portfolio_font_size)

    csv_dict = csv_data.to_dict()
    
    
    x_name = (template.width - 400) // 2  # Adjust as needed
    y_name = 970
    name_width = 400  # Width for justification

    x_portfolio = (template.width - 400) // 2  # Adjust as needed
    y_portfolio = 1070
    portfolio_width = 400  # Width for justification

    for key, value in csv_dict.items():
        if key == 'Name':
            text = f"{value}"
            position = (x_name, y_name)
            justify_text(draw, text, position, name_width, name_font, "white", justification="center")
            y_name += 30
        elif key == 'portfolio':
            text = f"{value}"
            position = (x_portfolio, y_portfolio)
            justify_text(draw, text, position, portfolio_width, portfolio_font, "white", justification="center")
            y_portfolio += 30
        else:
            continue

    img_buffer = io.BytesIO()
    template.save(img_buffer, format="PNG")
    img_buffer.seek(0)

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
