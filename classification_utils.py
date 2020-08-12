import os
import numpy as np
from scipy import misc
from PIL import Image
from keras.models import model_from_json
import keras
import shutil

'''
Takes an entire directory of detected cell images (platelets, wbcs, rbcs) that were detected in detection_utils.py, classifies the rbcs (infected vs uninfected)
and makes count of total infected, and puts the detected images into their respective folders (infected rbc, uninfected rbc, wbc, platelet)
'''

def load_the_model_classification():
    # load json and create model
    json_file = open('models/classification_model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights("models/classification_model.h5")
    return loaded_model

def process_imgs(dir):
    all = os.listdir(dir)
    # some detected images (mysteriously) have 0 bytes and are thus not images. They must be deleted
    for file in all:
        if os.path.getsize(dir+file) == 0:
            os.remove(dir+file)
    # list of filenames of cell types in segmented dataset
    only_rbcs = []
    only_wbcs = []
    only_plats = []
    all = os.listdir(dir) # dir after purging the 0 byte files
    for file in all:
        if file[:3] == 'RBC':
            only_rbcs.append(file)
        elif file[:9] == 'Platelets':
            only_plats.append(file)
        elif file[:3] == 'WBC':
            only_wbcs.append(file)
    # process the rbc images to the requisite shape (len(dir), 3, 100, 100)
    images = np.array([np.array(Image.open(dir+fname)) for fname in only_rbcs])
    images_list = []
    for x in range(len(images)):
        #image_resized = misc.imresize(images[x], (100,100,3)) <--scipy is deprecated
        image_resized = np.resize(images[x], (100,100,3))
        images_list.append(image_resized)
    #
    images_arr = np.array(images_list)
    #
    images_arr_reshaped = images_arr.reshape(len(images_arr),3,100,100)
    return only_rbcs, only_wbcs, only_plats, images_arr_reshaped

def file_moving(rbc_infected_flist, rbc_uninfected_flist, wbc_flist, plat_flist):
    for f in rbc_infected_flist:
        shutil.move('static/segmented/'+f, 'static/infected_rbcs/'+f)
    for f in rbc_uninfected_flist:
        shutil.move('static/segmented/'+f, 'static/uninfected_rbcs/'+f)
    for f in wbc_flist:
        shutil.move('static/segmented/'+f, 'static/wbcs/'+f)
    for f in plat_flist:
        shutil.move('static/segmented/'+f, 'static/platelets/'+f)

def return_val(pred):
    if np.array_equal(np.array([[1]], dtype='int32'), pred.astype('int32')):
        return "parasitic"
    else:
        return "uninfected"

# batch_pred_classification takes directory of already segmented cells, and classifies them as infected or uninfected and provides a ratio
# has to have / after directory (e.g. batch_pred_classification('static/segmented/'))
def batch_pred_classification(dir):
    loaded_model = load_the_model_classification()
    rbc_flist, wbc_flist, plat_flist, input_imgs = process_imgs(dir)
    rbc_infected_flist = []
    rbc_uninfected_flist = []
    num = 0
    ticks = 0

    for x in range(len(input_imgs)):
        pred = loaded_model.predict(input_imgs[x].reshape(1,3,100,100))
        num += 1
        if return_val(pred) == 'parasitic':
            ticks += 1
            rbc_infected_flist.append(rbc_flist[x])
        else:
            rbc_uninfected_flist.append(rbc_flist[x])
    keras.backend.clear_session()

    # moves all the infected/uninfected rbcs, wbcs, platelets in the segmentation folder to respective folders
    file_moving(rbc_infected_flist, rbc_uninfected_flist, wbc_flist, plat_flist)

    if num == 0: # to prevent dividing by zero error
        message = 'The model did not segment out any red blood cells. Please try another image.'
    else:
        ratio = ticks/num
        ratio *= 100
        message = 'The model segmented out %s red blood cells, in which there were %s infected by the malaria parasite. %.3f percent were infected' % (str(num), str(ticks), ratio)
    return message