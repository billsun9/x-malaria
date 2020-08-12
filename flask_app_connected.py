import os
from flask import Flask, flash, render_template, request, redirect
from werkzeug.utils import secure_filename

from detection_utils import batch_pred_detection
from classification_utils import batch_pred_classification

import shutil
from datetime import date
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'dataset'
PERSONAL_DATASET = 'personal_dataset'
DETECTION_FOLDER = os.path.join('static', 'detection')
SEGMENTATION_FOLDER = os.path.join('static', 'segmented')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'DSJLKCSDCXFYCVKSDC'
app.config['PERSONAL_DATASET'] = PERSONAL_DATASET

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename): # checks if the uploaded file has correct extension
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save(text, filepath="user_info.txt"): # save user input data
    with open(filepath, "a+") as f:
        f.write(text)
#
def show_predictions(dir):
    filelist = os.listdir(dir)
    to_show = []
    for file in filelist:
        saved_loc = os.path.join(dir, file)
        to_show.append(saved_loc)
    return to_show

def purge():
    segmented = 'static/segmented/'
    detection = 'static/detection/'
    infected_rbcs = 'static/infected_rbcs/'
    uninfected_rbcs = 'static/uninfected_rbcs/'
    plats = 'static/platelets/'
    wbcs = 'static/wbcs/'
    dataset = 'dataset/'
    data = [segmented, detection, dataset, infected_rbcs, uninfected_rbcs, plats, wbcs]
    for folder in data:
        for file in os.listdir(folder):
            os.remove(folder+file)
    # remove the zip files
    for item in os.listdir('static/download/'):
        os.remove('static/download/'+item)

def zipStuff(): # zips images to their respective folders
    shutil.make_archive('static/download/infected_rbcs', 'zip', 'static/infected_rbcs/')
    shutil.make_archive('static/download/uninfected_rbcs', 'zip', 'static/uninfected_rbcs/')
    shutil.make_archive('static/download/wbcs', 'zip', 'static/wbcs/')
    shutil.make_archive('static/download/platelets', 'zip', 'static/platelets/')

@app.route('/') # home page, with links to upload, methods discussion, and contact info
def index():
    return render_template('index.html')

@app.route('/methods_discussion') # page with model and methods information
def methods_discussion():
    return render_template('methods.html')

@app.route('/contact') # page with contact information
def contact():
    return render_template('contact.html')

@app.route('/example') # page with readme and example image
def example():
    return render_template('README.html')

@app.route('/user_info', methods=['GET', 'POST']) # form for user information
def user_info():
    return render_template('info.html')

@app.route('/continue', methods=['GET', 'POST']) # saves the user info form to "user_info.txt"
def save_info():
    country = request.form['country']
    affiliation = request.form['affiliation']
    #organization = request.form['organization']
    today = date.today()
    d = today.strftime("%b-%d-%Y")
    info = "{}\n{}\n{}\n".format(str(d), str(country), str(affiliation))
    save(info)
    return render_template('thanks_page.html') # renders page that continues to upload page

@app.route('/upload_a_file', methods=['GET', 'POST']) # page that allows upload of multiple files. Sends data to "/result"
def upload_a_file():
    return render_template('upload-batch2.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    purge()
    if request.method == 'POST': #saves the raw input images to "dataset" directory
        # check if the post request has the files part
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                shutil.copyfile(os.path.join(app.config['UPLOAD_FOLDER'], filename), os.path.join(app.config['PERSONAL_DATASET'], filename))
            #
    t1 = time.time()
    batch_pred_detection(UPLOAD_FOLDER) # performs the object detection process; saves predicted full images to "static/detection/" and segmented cells to "static/segmented/"

    message = batch_pred_classification('static/segmented/') # performs classification for segmented cells in "static/segmented/". returns message for user
    time_message = '----Time elasped: %s seconds----' % str(t1-time.time()) # prediction time
    zipStuff() # zip the segmented images
    return render_template('batch_show.html', paths = show_predictions(DETECTION_FOLDER), message = message, time_message = time_message) # page shows the frcnn predicted smear image and the percent infected


if __name__ == '__main__':
    app.run()