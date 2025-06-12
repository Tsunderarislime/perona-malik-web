from flask import Flask, render_template, request, flash, redirect, url_for, abort, send_from_directory
from celery import Celery
import os
from time import time
from werkzeug.utils import secure_filename
import cv2
import scripts.pm as pm

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '1'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 4
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['RESULT_PATH'] = 'result'

# Make the folders, if they do not already exist
os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
os.makedirs(app.config['RESULT_PATH'], exist_ok=True)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Set up uploads folder cleaning task, every 5 minutes
@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(300.0, clean.s(), name='Clean Uploads Every 5 Minutes', expires=60.0)

# TODO: Process the image
@celery.task
def process_image_channel(image_channel, iterations, time_step_size, k, g_func, upload_path, result_path, image_name):
    return pm.main(image_channel, iterations, time_step_size, k, g_func - 1, upload_path, result_path, image_name)

# Cleanup task, remove images in the folders if they've been there for over an hour.
@celery.task
def clean():
    uploaded_images = [os.path.join(app.config['UPLOAD_PATH'], im) for im in os.listdir(app.config['UPLOAD_PATH'])]
    result_images = [os.path.join(app.config['RESULT_PATH'], im) for im in os.listdir(app.config['RESULT_PATH'])]

    for im in uploaded_images:
        if time() - im > 3600:
            os.remove(im)
    
    for im in result_images:
        if time() - im > 3600:
            os.remove(im)

# This should just be the file upload page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)

            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            return redirect(url_for('params', filename=filename))
        else:
            flash("Please upload a file.")

    return render_template('index.html')

# Get file from upload
@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    if filename != '':
        file_ext = os.path.splitext(filename)[1]

        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)

        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        return redirect(url_for('params', filename=filename))

    return redirect(url_for('index'))

# Parameter selection for Perona-Malik edge enhancement
@app.route('/params/<filename>', methods=['GET', 'POST'])
def params(filename):
    if request.method == 'POST':
        iterations = int(request.form['iterations'])
        time_step_size = float(request.form['time-step-size'])
        k = float(request.form['constant-k'])
        g_func = int(request.form['g-function'])

        # Process the image, call process for each colour channel
        channels = cv2.imread(os.path.join(app.config['UPLOAD_PATH'], filename)).shape[2]
        for i in range(channels):
            process_image_channel.delay(i, iterations, time_step_size, k, g_func, app.config['UPLOAD_PATH'], app.config['RESULT_PATH'], filename)

        return redirect(url_for('index'))
    return render_template('params.html', file=filename)

# Image source for uploads display
@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

# Image source for result display
@app.route('/result/<filename>')
def result(filename):
    return send_from_directory(app.config['RESULT_PATH'], filename)

# Debug mode if run directly
if __name__ == '__main__':
    app.run(debug=True)
