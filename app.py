from flask import Flask, render_template, request, flash, redirect, url_for, abort, send_from_directory, jsonify
from celery import Celery
from celery.result import AsyncResult
import os
from time import time
from werkzeug.utils import secure_filename
import cv2
from numpy import stack
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
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['result_backend'] = 'redis://redis:6379/0'

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

# Cleanup task, remove images in the folders if they've been there for over 15 minutes.
@celery.task
def clean():
    uploaded_images = [os.path.join(app.config['UPLOAD_PATH'], im) for im in os.listdir(app.config['UPLOAD_PATH'])]
    result_images = [os.path.join(app.config['RESULT_PATH'], im) for im in os.listdir(app.config['RESULT_PATH'])]
    now = time()

    for im in uploaded_images:
        if now - os.path.getmtime(im) > 900:
            os.remove(im)
    
    for im in result_images:
        if now - os.path.getmtime(im) > 900:
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
        iterations = request.form['iterations']
        time_step_size = request.form['time-step-size']
        k = request.form['constant-k']
        g_func = request.form['g-function']

        return redirect(url_for('results', filename=filename, iterations=iterations, time_step_size=time_step_size, k=k, g_func=g_func))

    return render_template('params.html', file=filename)

@app.route('/results/<filename>', methods=['GET'])
def results(filename):
    iterations = int(request.args['iterations'])
    time_step_size = float(request.args['time_step_size'])
    k = float(request.args['k'])
    g_func = int(request.args['g_func'])

    # Process the image, call process for each colour channel
    channels = cv2.imread(os.path.join(app.config['UPLOAD_PATH'], filename), cv2.IMREAD_UNCHANGED).shape[2]
    tasks = [process_image_channel.delay(i, iterations, time_step_size, k, g_func, app.config['UPLOAD_PATH'], app.config['RESULT_PATH'], filename) for i in range(channels)]

    # Reconstruct the image, then return the result
    channel_data = [cv2.imread(tasks[i].get(), cv2.IMREAD_UNCHANGED) for i in range(channels)]
    img = stack(channel_data, axis=2)
    cv2.imwrite(os.path.join(app.config['RESULT_PATH'], filename), img)

    return render_template('results.html', file=filename)

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
