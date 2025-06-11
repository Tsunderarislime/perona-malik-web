from flask import Flask, render_template, request, flash, redirect, url_for, abort, send_from_directory
from celery import Celery
import os
from time import time
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '1'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 4
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'

# Make the uploads folder, if it does not already exist
os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)

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
def process_image(image_path, iterations, time_step_size, k, g_func):
    return image_path

# Cleanup task, remove images in the uploads folder if they've been there for over an hour.
@celery.task
def clean():
    images = [os.path.join(app.config['UPLOAD_PATH'], im) for im in os.listdir('uploads')]
    for im in images:
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
        flash(f"{iterations} iterations, {time_step_size} step size, K = {k}, function {g_func}. File to change is: {os.path.join(app.config['UPLOAD_PATH'], filename)}")
        process_image.delay(os.path.join(app.config['UPLOAD_PATH'], filename), iterations, time_step_size, k, g_func)

        return redirect(url_for('index'))
    return render_template('params.html', file=filename)

# Image source for uploads display
@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

# Debug mode if run directly
if __name__ == '__main__':
    app.run(debug=True)
