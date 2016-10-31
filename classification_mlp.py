from util.preprocessing import *
from util.dataset_io import *
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.utils import np_utils
from keras.optimizers import Adamax
import random
import numpy as np
import tensorflow as tf


tf.python.control_flow_ops = tf


def train_mlp1(x_train, y_train, x_test, y_test, input_dim, num_classes=5, data_augmentation=True):
    """

    :param x_train:
    :param y_train:
    :param x_test:
    :param y_test:
    :param input_dim:
    :param num_classes:
    :return:
    """
    model = Sequential()
    model.add(Dense(512, input_dim=input_dim))
    model.add(Activation('relu'))   # An "activation" is just a non-linear function applied to the output of the layer
                                    # above. Here, with a "rectified linear unit", we clamp all values below 0 to 0.
    model.add(Dropout(0.25))        # Dropout helps protect the model from memorizing or "overfitting" the training data
    model.add(Dense(768))
    model.add(Activation('relu'))

    model.add(Dense(256))
    model.add(Activation('relu'))

    model.add(Dropout(0.25))
    model.add(Dense(num_classes))
    model.add(Activation('softmax'))  # This special "softmax" activation among other things,
                                      # ensures the output is a valid probability distribution, that is
                                      # that its values are all non-negative and sum to 1.

    model.compile(loss='categorical_crossentropy', optimizer=Adamax(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=1e-5), metrics=["accuracy"])
    model.fit(x_train, y_train,
              batch_size=20, nb_epoch=32, verbose=1,
              validation_data=(x_test, y_test))
    score = model.evaluate(x_test, y_test, verbose=1)
    return score[1]


def classify_images(foldername="data/cropped/", num_users=20, num_classes=5):
    """

    :param foldername:
    :param num_users:
    :param num_classes:
    :return:
    """
    k_fold = 5  # Assume 5-fold CV
    num_groups = num_users//k_fold  # Number of groups to split the data into
    mlp_scores = list()
    user_group_map = dict()  # Random mapping of users to groups
    num_users_in_group = [0 for i in range(num_groups)]  # Store the number of users in a group to ensure uniform distribution

    for i in range(0, num_users):
        rand_int = random.randrange(0, num_groups)
        while num_users_in_group[rand_int] >= 5:
            rand_int = random.randrange(0, num_groups)
        user_group_map[i] = rand_int
        num_users_in_group[rand_int] = 1

    print("Loading images...")
    hog_dataset = unpickle_hog_arrays("data/cropped_hog.pkl")
    for t0 in range(0, num_groups):
        print("ITERATION:", t0+1, "\n----------")
        x_train = list()
        x_crossval = list()
        for i0 in range(1, num_classes+1):
            filelist = listdir(foldername + str(i0))
            for filename in filelist:
                hog_image = hog_dataset[filename]
                if user_group_map[int(filename.split('_')[0])-1] == t0:
                    x_crossval.append((hog_image, i0-1))
                else:
                    x_train.append((hog_image, i0-1))

        random.shuffle(x_train)
        random.shuffle(x_crossval)
        y_train = np_utils.to_categorical([x[1] for x in x_train], num_classes)
        x_train = np.array([x[0].ravel() for x in x_train])
        y_crossval = np_utils.to_categorical([x[1] for x in x_crossval], num_classes)
        x_crossval = np.array([x[0].ravel() for x in x_crossval])

        print("Size of Training Set:", len(x_train), "\nSize of Crossval Set:", len(x_crossval))

        print("Training MLP Classifier...")
        test_score = train_mlp1(x_train, y_train, x_crossval, y_crossval, input_dim=16384)
        print("\nIteration Accuracy:", test_score)
        mlp_scores.append(test_score)
        print("\n")

    print("Average MLP Accuracy:", sum(mlp_scores)/num_groups)

classify_images()
