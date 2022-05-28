__author__ = "Andrea Galassi"
__copyright__ = "Copyright 2018, Andrea Galassi"
__license__ = "BSD 3-clause"
__version__ = "0.5.0"
__email__ = "a.galassi@unibo.it"

"""
Code for the training process
"""

import os
import pandas
import numpy as np
import sys
import time
import evaluate_net
import json
import tensorflow as tf
import argparse

from dataset_config import dataset_info
from networks import (build_net_7, build_not_res_net_7, create_crop_fn, create_sum_fn, create_average_fn,
                      create_count_nonpadding_fn, create_elementwise_division_fn, create_padding_mask_fn,
                      create_mutiply_negative_elements_fn, build_net_11,)
from tensorflow.keras.callbacks import Callback, LearningRateScheduler, ModelCheckpoint, EarlyStopping, CSVLogger
from tensorflow.keras.optimizers import RMSprop, Adam
from tensorflow.keras.models import load_model, model_from_json
from training_utils import TimingCallback, create_lr_annealing_function, get_avgF1
from glove_loader import DIM
from sklearn.metrics import f1_score
from tensorflow.compat.v1.keras import backend as K

DEBUG = False
train_info = {}
global_counter = 0

config = tf.compat.v1.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.8
config.gpu_options.allow_growth = True
K.set_session(tf.compat.v1.Session(config=config))

def load_dataset(dataset_split='total', dataset_name='cdcp_ACL17', dataset_version='new_2',
                 feature_type='embeddings', min_text_len=0, min_prop_len=0, distance=5,
                 distance_train_limit=-1, embed_name="glove300"):

    if distance < 0:
        distance = 0

    if feature_type == 'bow':
        pad = 0
        dtype = np.uint16
        ndim = 2
    elif feature_type == 'embeddings':
        pad = np.zeros(DIM)
        dtype = np.float32
        ndim = 3

    max_prop_len = min_prop_len
    max_text_len = min_text_len

    dataset_path = os.path.join(os.getcwd(), 'Datasets', dataset_name)
    dataframe_path = os.path.join(dataset_path, 'pickles', dataset_version, dataset_split + '.pkl')
    embed_path = os.path.join(dataset_path, "embeddings", embed_name, dataset_version)

    df = pandas.read_pickle(dataframe_path)

    categorical_prop = dataset_info[dataset_name]["categorical_prop"]
    categorical_link = dataset_info[dataset_name]["categorical_link"]

    dataset = {}

    for split in ('train', 'validation', 'test'):
        dataset[split] = {}
        dataset[split]['source_props'] = []
        dataset[split]['target_props'] = []
        dataset[split]['links'] = []
        dataset[split]['relations_type'] = []
        dataset[split]['sources_type'] = []
        dataset[split]['targets_type'] = []

        if distance > 0:
            dataset[split]['distance'] = []
            dataset[split]['difference'] = []

        dataset[split]['s_id'] = []
        dataset[split]['t_id'] = []

    for index, row in df.iterrows():

        s_index = int(row['source_ID'].split('_')[-1])
        t_index = int(row['target_ID'].split('_')[-1])

        difference = t_index - s_index

        split = row['set']

        # in case this is a train tuple, that the limitation on the distance is active and that the distance between
        # the two components is greater than the distance allowed, skip this row
        if split == "train" and distance_train_limit > 0 and abs(difference) > distance_train_limit:
            continue

        text_ID = row['text_ID']
        source_ID = row['source_ID']
        target_ID = row['target_ID']
        split = row['set']


        if row['source_to_target']:
            dataset[split]['links'].append([1, 0])
        else:
            dataset[split]['links'].append([0, 1])
        """
        else:
            if split == 'train':
                n = random.random()
                if n < 0.2:
                    continue
            dataset[split]['links'].append([0, 1])
        """

        dataset[split]['sources_type'].append(categorical_prop[row['source_type']])
        dataset[split]['targets_type'].append(categorical_prop[row['target_type']])


        dataset[split]['relations_type'].append(categorical_link[row['relation_type']])

        dataset[split]['s_id'].append(row['source_ID'])
        dataset[split]['t_id'].append(row['target_ID'])


        if distance > 0:
            difference_array = [0] * distance * 2
            if difference > distance:
                difference_array[-distance:] = [1] * distance
            elif difference < -distance:
                difference_array[:distance] = [1] * distance
            elif difference > 0:
                difference_array[-distance: distance + difference] = [1] * difference
            elif difference < 0:
                difference_array[distance + difference: distance] = [1] * -difference
            dataset[split]['distance'].append(difference_array)
            dataset[split]['difference'].append(difference)

        file_path = os.path.join(embed_path, source_ID + '.npz')
        embeddings = np.load(file_path)['arr_0']
        embed_length = len(embeddings)
        if embed_length > max_prop_len:
            max_prop_len = embed_length
        dataset[split]['source_props'].append(embeddings)

        file_path = os.path.join(embed_path, target_ID + '.npz')
        embeddings = np.load(file_path)['arr_0']
        embed_length = len(embeddings)
        if embed_length > max_prop_len:
            max_prop_len = embed_length
        dataset[split]['target_props'].append(embeddings)

    print(str(time.ctime()) + '\t\tPADDING...')

    sys.stdout.flush()

    for split in ('train', 'validation', 'test'):

        dataset[split]['distance'] = np.array(dataset[split]['distance'], dtype=np.int8)

        print(str(time.ctime()) + '\t\t\tPADDING ' + split)


        texts = dataset[split]['source_props']
        for j in range(len(texts)):
            text = texts[j]
            embeddings = []
            diff = max_prop_len - len(text)
            for i in range(diff):
                embeddings.append(pad)
            for embedding in text:
                embeddings.append(embedding)
            texts[j] = embeddings
        dataset[split]['source_props'] = np.array(texts, ndmin=ndim, dtype=dtype)

        texts = dataset[split]['target_props']
        for j in range(len(texts)):
            text = texts[j]
            embeddings = []
            diff = max_prop_len - len(text)
            for i in range(diff):
                embeddings.append(pad)
            for embedding in text:
                embeddings.append(embedding)
            texts[j] = embeddings
        dataset[split]['target_props'] = np.array(texts, ndmin=ndim, dtype=dtype)


    return dataset, max_text_len, max_prop_len


def perform_training(name = 'try999',
                     save_weights_only=False,
                    epochs = 1000,
                     distance_train_limit=-1,
                    feature_type = 'bow',
                    patience = 100,
                    loss_weights = [0, 10, 1, 1],
                    lr_alfa = 0.003,
                    lr_kappa = 0.001,
                    beta_1 = 0.9,
                    beta_2 = 0.999,
                    res_scale = 15,
                    resnet_layers = (2, 2),
                     space_scale=4,
                    embedding_scale = 10,
                    embedder_layers = 2,
                    avg_pad = 20,
                    final_scale = 3,
                    batch_size = 200,
                    regularizer_weight = 0.001,
                    dropout_resnet = 0.5,
                    dropout_embedder = 0.5,
                    dropout_final = 0.0,
                    cross_embed = False,
                    single_LSTM=False,
                    pooling=10,
                    text_pooling=10,
                    pooling_type='avg',
                    monitor="relations",
                    dataset_name = 'AAEC_v2',
                    dataset_version = 'new_2',
                     dataset_split = "total",
                    bn_embed=True,
                    bn_res=True,
                    bn_final=True,
                    network=2,
                     true_validation=False,
                     same_layers=False,
                     distance=5,
                     temporalBN=False,
                     iterations=1,
                     merge="a_self",
                     classification="softmax",
                     clean_previous_networks=True,
                     embed_name="glove300",
                     overwrite=False,
                     log_time=False):

    embedding_size = int(DIM/embedding_scale)
    res_size = int(DIM/res_scale)
    final_size = int(DIM/final_scale)

    parameters = locals()

    save_dir = os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version)

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    paramfile = open(os.path.join(save_dir, name + "_info.txt"),'w')

    for parameter in sorted(parameters.keys()):
        value = parameters[parameter]
        paramfile.write(parameter + " = " + str(value) + "\n")
    paramfile.close()

    output_units = ()
    min_text = 0
    min_prop = 0
    link_as_sum = [[]]

    output_units = dataset_info[dataset_name]["output_units"]
    min_text = dataset_info[dataset_name]["min_text"]
    min_prop = dataset_info[dataset_name]["min_prop"]
    link_as_sum = dataset_info[dataset_name]["link_as_sum"]


    distance_num = distance
    if distance < 0:
        distance = False
    else:
        distance = True

    print(str(time.ctime()) + "\tLAUNCHING TRAINING: " + name)
    print(str(time.ctime()) + "\tLOADING DATASET...")
    dataset, max_text_len, max_prop_len = load_dataset(dataset_name=dataset_name,
                                                       dataset_version=dataset_version,
                                                       dataset_split=dataset_split,
                                                       feature_type=feature_type,
                                                       min_text_len=min_text,
                                                       min_prop_len=min_prop,
                                                       distance=distance_num,
                                                       distance_train_limit=distance_train_limit,
                                                       embed_name=embed_name)
    print(str(time.ctime()) + "\tDATASET LOADED...")
    sys.stdout.flush()

    print(str(time.ctime()) + "\tPROCESSING DATA AND MODEL...")

    split = 'train'
    X_source_train = dataset[split]['source_props']
    del dataset[split]['source_props']
    X_target_train = dataset[split]['target_props']
    del dataset[split]['target_props']
    Y_links_train = np.array(dataset[split]['links'])
    Y_rtype_train = np.array(dataset[split]['relations_type'], dtype=np.float32)
    Y_stype_train = np.array(dataset[split]['sources_type'])
    Y_ttype_train = np.array(dataset[split]['targets_type'])

    # if they are not used, creates a mock (necessary for compatibility with other stuff)
    numdata = len(Y_links_train)
    if distance > 0:
        X_dist_train = dataset[split]['distance']
    else:
        X_dist_train = np.zeros((numdata, 2))

    Y_train = [Y_links_train, Y_rtype_train, Y_stype_train, Y_ttype_train]
    X3_train = [X_source_train, X_target_train, X_dist_train,]

    print(str(time.ctime()) + "\t\tTRAINING DATA PROCESSED...")
    print("Length: " + str(len(X3_train[0])))

    split = 'test'

    X_source_test = dataset[split]['source_props']
    del dataset[split]['source_props']
    X_target_test = dataset[split]['target_props']
    del dataset[split]['target_props']
    Y_links_test = np.array(dataset[split]['links'])
    Y_rtype_test = np.array(dataset[split]['relations_type'])
    Y_stype_test = np.array(dataset[split]['sources_type'])
    Y_ttype_test = np.array(dataset[split]['targets_type'])
    Y_test = [Y_links_test, Y_rtype_test, Y_stype_test, Y_ttype_test]

    # if they are not used, creates a mock (necessary for compatibility with other stuff)
    numdata = len(Y_links_test)
    if distance > 0:
        X_dist_test = dataset[split]['distance']
    else:
        X_dist_test= np.zeros((numdata, 2))


    X3_test = [X_source_test, X_target_test, X_dist_test]

    print(str(time.ctime()) + "\t\tTEST DATA PROCESSED...")
    print("Length: " + str(len(X3_test[0])))

    split = 'validation'
    X_source_validation = dataset[split]['source_props']
    del dataset[split]['source_props']
    X_target_validation = dataset[split]['target_props']
    del dataset[split]['target_props']
    Y_links_validation = np.array(dataset[split]['links'])
    Y_rtype_validation = np.array(dataset[split]['relations_type'])
    Y_stype_validation = np.array(dataset[split]['sources_type'])
    Y_ttype_validation = np.array(dataset[split]['targets_type'])
    Y_validation = [Y_links_validation, Y_rtype_validation, Y_stype_validation, Y_ttype_validation]

    # if they are not used, creates a mock (necessary for compatibility with other stuff)
    numdata = len(Y_links_validation)
    if distance > 0:
        X_dist_validation = dataset[split]['distance']
    else:
        X_dist_validation= np.zeros((numdata, 2))

    X3_validation = [X_source_validation, X_target_validation, X_dist_validation,]

    print(str(time.ctime()) + "\t\tVALIDATION DATA PROCESSED...")
    print("Length: " + str(len(X3_validation[0])))
    print(str(time.ctime()) + "\t\tCREATING MODEL...")

    bow = None
    if feature_type == 'bow':
        dataset_path = os.path.join(os.getcwd(), 'Datasets', dataset_name)
        vocabulary_path = os.path.join(dataset_path, 'resources', embed_name, dataset_version,'glove.embeddings.npz')
        if not os.path.exists(vocabulary_path):
            vocabulary_path = os.path.join(dataset_path, 'resources', embed_name, 'glove.embeddings.npz')
        vocabulary_list = np.load(vocabulary_path)
        embed_list = vocabulary_list['embeds']
        word_list = vocabulary_list['vocab']

        bow = np.zeros((len(word_list) + 1, DIM))
        for index in range(len(word_list)):
            bow[index + 1] = embed_list[index]
        print(str(time.ctime()) + "\t\t\tEMBEDDINGS LOADED...")

    realname = name


    # multi-iteration evaluation setting
    final_scores = {'train': [], 'test': [], 'validation': []}
    evaluation_headline = ""
    evaluation_headline = dataset_info[dataset_name]["evaluation_headline_short"]



    save_dir = os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version, realname)
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    # CLEAR FOLDER
    if overwrite:
        filelist = [f for f in os.listdir(save_dir) if f.endswith(".h5")]
        for f in filelist:
            os.remove(os.path.join(save_dir, f))

    train_times = []

    # train and test iterations
    for i in range(iterations):

        name = realname + "_" + str(i)
        model_name = realname + '_model.json'
        log_path = os.path.join(save_dir, name + '_training.log')

        # if the training of this iteration was already completed, skip it
        if os.path.isfile(log_path) and not overwrite:
            continue

        model = None
        if network == 7 or network == "7":
            model = build_net_7(bow=bow,
                                link_as_sum=link_as_sum,
                                propos_length=max_prop_len,
                                regularizer_weight=regularizer_weight,
                                dropout_embedder=dropout_embedder,
                                dropout_resnet=dropout_resnet,
                                embedding_size=embedding_size,
                                embedder_layers=embedder_layers,
                                resnet_layers=resnet_layers,
                                res_size=res_size,
                                final_size=final_size,
                                outputs=output_units,
                                bn_embed=bn_embed,
                                bn_res=bn_res,
                                bn_final=bn_final,
                                single_LSTM=single_LSTM,
                                pooling=pooling,
                                text_pooling=text_pooling,
                                pooling_type=pooling_type,
                                dropout_final=dropout_final,
                                same_DE_layers=same_layers,
                                distance=distance_num,
                                temporalBN=temporalBN,)
        elif network == "7N" or network == "7n":
            model = build_not_res_net_7(bow=bow,
                                        propos_length=max_prop_len,
                                        regularizer_weight=regularizer_weight,
                                        dropout_embedder=dropout_embedder,
                                        dropout_resnet=dropout_resnet,
                                        embedding_size=embedding_size,
                                        embedder_layers=embedder_layers,
                                        resnet_layers=resnet_layers,
                                        res_size=res_size,
                                        final_size=final_size,
                                        outputs=output_units,
                                        bn_embed=bn_embed,
                                        bn_res=bn_res,
                                        bn_final=bn_final,
                                        single_LSTM=single_LSTM,
                                        pooling=pooling,
                                        text_pooling=text_pooling,
                                        pooling_type=pooling_type,
                                        dropout_final=dropout_final,
                                        same_DE_layers=same_layers,
                                        distance=distance_num,
                                        temporalBN=temporalBN,)
        elif network == "11" or network == 11:
            model = build_net_11(bow=bow,
                                link_as_sum=link_as_sum,
                                 propos_length=max_prop_len,
                                 regularizer_weight=regularizer_weight,
                                dropout_embedder=dropout_embedder,
                                dropout_resnet=dropout_resnet,
                                embedding_size=embedding_size,
                                embedder_layers=embedder_layers,
                                resnet_layers=resnet_layers,
                                res_size=res_size,
                                final_size=final_size,
                                outputs=output_units,
                                bn_embed=bn_embed,
                                bn_res=bn_res,
                                bn_final=bn_final,
                                single_LSTM=single_LSTM,
                                dropout_final=dropout_final,
                                same_DE_layers=same_layers,
                                distance=distance_num,
                                temporalBN=temporalBN,)

        relations_labels = dataset_info[dataset_name]["link_as_sum"][0]
        not_a_link_labels = dataset_info[dataset_name]["link_as_sum"][1]

        # it is necessary to save all the custom functions
        fmeasure_0 = get_avgF1([0])
        fmeasure_1 = get_avgF1([1])
        fmeasure_2 = get_avgF1([2])
        fmeasure_3 = get_avgF1([3])
        fmeasure_4 = get_avgF1([4])
        fmeasure_0_1_2_3 = get_avgF1([0, 1, 2, 3])
        fmeasure_0_1_2_3_4 = get_avgF1([0, 1, 2, 3, 4])
        fmeasure_0_2 = get_avgF1([0, 2])
        fmeasure_0_1_2 = get_avgF1([0, 1, 2])
        fmeasure_0_1 = get_avgF1([0, 1, 2])
        fmeasure_0_2_4 = get_avgF1([0, 2, 4])

        fmeasures = [fmeasure_0, fmeasure_1, fmeasure_2, fmeasure_3, fmeasure_4, fmeasure_0_1_2_3, fmeasure_0_1_2_3_4,
                     fmeasure_0_2, fmeasure_0_1_2, fmeasure_0_1, fmeasure_0_2_4]

        props_fmeasures = []

        if dataset_name == 'cdcp_ACL17':
            props_fmeasures = [fmeasure_0_1_2_3_4]
        #elif dataset_name == 'AAEC_v2':
        #    props_fmeasures = [fmeasure_0, fmeasure_1, fmeasure_2, fmeasure_0_1_2]
        elif dataset_name == 'AAEC_v2':
            props_fmeasures = [fmeasure_0_1_2]

        # for using them during model loading
        custom_objects = {}

        for fmeasure in fmeasures:
            custom_objects[fmeasure.__name__] = fmeasure

        crop0 = create_crop_fn(1, 0, 1)
        crop1 = create_crop_fn(1, 1, 2)
        crop2 = create_crop_fn(1, 2, 3)
        crop3 = create_crop_fn(1, 3, 4)
        crop4 = create_crop_fn(1, 4, 5)

        crops = [crop0, crop1, crop2, crop3, crop4]
        for crop in crops:
            custom_objects[crop.__name__] = crop

        mean_fn = create_average_fn(1)
        sum_fn = create_sum_fn(1)
        division_fn = create_elementwise_division_fn()
        pad_fn = create_count_nonpadding_fn(1, (DIM,))
        padd_fn = create_padding_mask_fn()
        neg_fn = create_mutiply_negative_elements_fn()
        custom_objects[mean_fn.__name__] = mean_fn
        custom_objects[sum_fn.__name__] = sum_fn
        custom_objects[division_fn.__name__] = division_fn
        custom_objects[pad_fn.__name__] = pad_fn
        custom_objects[padd_fn.__name__] = padd_fn
        custom_objects[neg_fn.__name__] = neg_fn

        lr_function = create_lr_annealing_function(initial_lr=lr_alfa, k=lr_kappa)


        loss_variables = []
        for weight in loss_weights:
            loss_variables.append(K.variable(weight))

        model.compile(loss='categorical_crossentropy',
                      loss_weights=loss_weights,
                      optimizer=Adam(lr=lr_function(0),
                                     beta_1=beta_1,
                                     beta_2=beta_2),
                      metrics={'link': [fmeasure_0],
                               # 'relation': [fmeasure_0, fmeasure_2, fmeasure_0_2, fmeasure_0_1_2_3],
                               'relation': [fmeasure_0_2, fmeasure_0_1_2_3],
                               'source': props_fmeasures,
                               'target': props_fmeasures}
                      )

        model.summary()

        print("Expected input")
        print(model.input_shape)

        print(str(time.ctime()) + "\t\tMODEL COMPILED...")


        # PERSISTENCE CONFIGURATION
        complete_network_name = name + '_completemodel.{epoch:03d}.h5'
        model_name = realname + '_model.json'
        json_model = model.to_json()
        with open(os.path.join(save_dir, model_name), 'w') as outfile:
            json.dump(json_model, outfile)
        weights_name = name + '_weights.{epoch:03d}.h5'

        if not save_weights_only:
            file_path = os.path.join(save_dir, complete_network_name)
        else:
            file_path = os.path.join(save_dir, weights_name)

        # TRAINING CONFIGURATION

        if monitor == 'relations':
            monitor = 'val_relation_' + fmeasure_0_1_2_3.__name__
        elif monitor == 'pos_relations':
            monitor = 'val_relation_' + fmeasure_0_2.__name__
        elif monitor == 'links':
            monitor = 'val_link_' + fmeasure_0.__name__


        logger = CSVLogger(log_path, separator='\t', append=False)


        if true_validation:
            # modify the lr each epoch
            logger = CSVLogger(log_path, separator='\t', append=True)

            best_score = -100
            waited = 0

            log_path = os.path.join(save_dir, name + '_validation.log')
            val_file = open(log_path,'w')

            val_file.write(evaluation_headline)

            # evaluation of test values

            # begin of the evaluation of the single propositions scores
            sids = dataset['validation']['s_id']
            tids = dataset['validation']['t_id']

            s_test_scores = {}
            t_test_scores = {}
            s_pred_scores = {}
            t_pred_scores = {}


            for index in range(len(sids)):
                sid = sids[index]
                tid = tids[index]

                if sid not in s_test_scores.keys():
                    s_test_scores[sid] = []
                    s_pred_scores[sid] = []
                s_test_scores[sid].append(Y_validation[2][index])

                if tid not in t_test_scores.keys():
                    t_test_scores[tid] = []
                    t_pred_scores[tid] = []
                t_test_scores[tid].append(Y_validation[3][index])

            Y_test_prop_real_list = []

            for p_id in t_test_scores.keys():
                Y_test_prop_real_list.append(np.concatenate([s_test_scores[p_id], t_test_scores[p_id]]))

            Y_test_prop_real_list = np.array(Y_test_prop_real_list)

            Y_test_prop_real = []
            for index in range(len(Y_test_prop_real_list)):
                Y_test_prop_real.append(np.sum(Y_test_prop_real_list[index], axis=-2))

            Y_test_prop_real = np.array(Y_test_prop_real)
            Y_test_prop_real = np.argmax(Y_test_prop_real, axis=-1)

            Y_test_links_or = np.argmax(Y_validation[0], axis=-1)
            Y_test_rel_or = np.argmax(Y_validation[1], axis=-1)


            last_epoch = 0

            starttime = time.time()

            timer = TimingCallback()


            for epoch in range(1, epochs+1):
                print("\nEPOCH: " + str(epoch))
                lr_annealing_fn = create_lr_annealing_function(initial_lr=lr_alfa, k=lr_kappa, fixed_epoch=epoch)
                lr_scheduler = LearningRateScheduler(lr_annealing_fn)

                callbacks = [lr_scheduler, logger]
                if log_time:
                    callbacks.append(timer)

                model.fit(x=X3_train,
                          # y=Y_links_train,
                          y=Y_train,
                          batch_size=batch_size,
                          epochs=epoch+1,
                          verbose=2,
                          callbacks=callbacks,
                          initial_epoch=epoch
                          )

                # evaluation
                Y_pred = model.predict(X3_validation)

                Y_test_links = Y_test_links_or.copy()
                Y_test_rel = Y_test_rel_or.copy()

                for index in range(len(sids)):
                    sid = sids[index]
                    tid = tids[index]

                    s_pred_scores[sid].append(Y_pred[2][index])
                    t_pred_scores[tid].append(Y_pred[3][index])

                Y_pred_prop_real_list = []

                for p_id in t_test_scores.keys():
                    Y_pred_prop_real_list.append(np.concatenate([s_pred_scores[p_id], t_pred_scores[p_id]]))

                Y_pred_prop_real_list = np.array(Y_pred_prop_real_list)

                Y_pred_prop_real = []
                for index in range(len(Y_test_prop_real_list)):
                    Y_pred_prop_real.append(np.sum(Y_pred_prop_real_list[index], axis=-2))

                Y_pred_prop_real = np.array(Y_pred_prop_real)
                Y_pred_prop_real = np.argmax(Y_pred_prop_real, axis=-1)

                Y_pred_links = np.argmax(Y_pred[0], axis=-1)
                Y_pred_rel = np.argmax(Y_pred[1], axis=-1)


                # Remove all the symmetric links
                reflexive = []
                for index in range(len(sids)):
                    sid = sids[index]
                    tid = tids[index]
                    if sid == tid:
                        reflexive.append(index)
                if len(reflexive) > 0:
                    Y_test_rel = np.delete(Y_test_rel, reflexive, axis=0)
                    Y_pred_rel = np.delete(Y_pred_rel, reflexive, axis=0)
                    Y_test_links = np.delete(Y_test_links, reflexive, axis=0)
                    Y_pred_links = np.delete(Y_pred_links, reflexive, axis=0)
                    if len(Y_test_rel) != len(Y_pred_rel):
                        print(len(Y_test_rel))
                        print(len(Y_pred_rel))
                    if len(Y_test_links) != len(Y_pred_links):
                        print(len(Y_test_links))
                        print(len(Y_pred_links))

                positive_link_labels = dataset_info[dataset_name]["link_as_sum"][0]
                negative_link_labels = dataset_info[dataset_name]["link_as_sum"][1]

                score_f1_link = f1_score(Y_test_links, Y_pred_links, average=None, labels=[0])
                score_f1_rel = f1_score(Y_test_rel, Y_pred_rel, average=None, labels=positive_link_labels)
                score_f1_rel_AVGM = f1_score(Y_test_rel, Y_pred_rel, average='macro', labels=positive_link_labels)
                score_prop = f1_score(Y_test_prop_real, Y_pred_prop_real, average=None)
                score_prop_AVG = f1_score(Y_test_prop_real, Y_pred_prop_real, average='macro')

                score_AVG_LP = np.mean([score_f1_link, score_prop_AVG])
                score_AVG_all = np.mean([score_f1_link, score_prop_AVG, score_f1_rel_AVGM])

                string = str(epoch) + "\t" + str(round(score_AVG_all[0], 5)) + "\t" + str(round(score_AVG_LP[0], 5))
                string += "\t" + str(round(score_f1_link[0], 5)) + "\t" + str(round(score_f1_rel_AVGM, 5))
                for score in score_f1_rel:
                    string += "\t" + str(round(score, 5))
                string += "\t" + str(round(score_prop_AVG, 5))
                for score in score_prop:
                    string += "\t" + str(round(score, 5))

                monitor_score = score_f1_link

                if monitor == 'prop' or monitor == 'proposition' or monitor == 'propositions' or monitor == 'props':
                    monitor_score = score_prop_AVG
                elif monitor == 'AVG_LP':
                    monitor_score = score_AVG_LP

                if monitor_score > best_score:
                    best_score = monitor_score
                    string += "\t!"

                    file_path = os.path.join(save_dir, name + '_weights.%03d.h5' % epoch)
                    # save
                    print("Saving to " + file_path)
                    model.save_weights(file_path)
                    waited = 0
                else:
                    waited += 1
                    # early stopping
                    if waited > patience:
                        break

                val_file.write(string + "\n")

                val_file.flush()
                last_epoch = epoch

            endtime = time.time()

            val_file.close()
            waited = 0

        else:

            # save the networks each epoch
            checkpoint = ModelCheckpoint(filepath=file_path,
                                         # monitor='val_loss',
                                         monitor=monitor,
                                         verbose=1,
                                         save_best_only=True,
                                         save_weights_only=save_weights_only,
                                         mode='max'
                                         )

            # modify the lr each epoch
            lr_scheduler = LearningRateScheduler(lr_function)

            # early stopping
            early_stop = EarlyStopping(patience=patience,
                                       # monitor='val_loss',
                                       monitor=monitor,
                                       verbose=2,
                                       mode='max')

            callbacks = [lr_scheduler, logger, checkpoint, early_stop]
            if log_time:
                timer = TimingCallback()
                callbacks.append(timer)

            print(str(time.ctime()) + "\tSTARTING TRAINING")

            sys.stdout.flush()

            starttime = time.time()

            history = model.fit(x=X3_train,
                                # y=Y_links_train,
                                y=Y_train,
                                batch_size=batch_size,
                                epochs=epochs,
                                verbose=2,
                                # validation_data=(X_validation, Y_links_validation),
                                validation_data=(X3_validation, Y_validation),
                                callbacks=callbacks
                                )

            endtime = time.time()
            last_epoch = len(history.epoch)

        print(str(time.ctime()) + "\tTRAINING FINISHED")

        # END OF THE TRAINING PHASE

        train_time = endtime-starttime

        print("\t\tSECONDS PASSED: " + str(train_time))
        print("\n-----------------------\n")
        # START OF THE EVALUATION PHASE

        print(str(time.ctime()) + "\tEVALUATING MODEL")

        last_path = ""

        # load the model (the last one that was saved)
        if save_weights_only:
            model = model_from_json(json_model, custom_objects=custom_objects)

            for epoch in range(last_epoch, 0, -1):
                netpath = os.path.join(save_dir, name + '_weights.%03d.h5' % epoch)
                if os.path.exists(netpath):
                    last_path = netpath
                    last_epoch = epoch
                    break
            model.load_weights(last_path)

            print("\n\n\tCLEANING NETS BEFORE EPOCH: " + str(last_epoch) + "\n")
            if clean_previous_networks:
                for epoch in range(last_epoch-1, 0, -1):
                    netpath = os.path.join(save_dir, name + '_weights.%03d.h5' % epoch)
                    if os.path.exists(netpath):
                        os.remove(netpath)

        else:
            for epoch in range(last_epoch, 0, -1):
                netpath = os.path.join(save_dir, name + '_completemodel.%03d.h5' % epoch)
                if os.path.exists(netpath):
                    last_path = netpath
                    last_epoch = epoch
                    break

            model = load_model(last_path, custom_objects=custom_objects)


            print("\n\n\tCLEANING NETS BEFORE EPOCH: " + str(last_epoch) + "\n")

            if clean_previous_networks:
                for epoch in range(last_epoch-1, 0, -1):
                    netpath = os.path.join(save_dir, name + '_completemodel.%03d.h5' % epoch)
                    if os.path.exists(netpath):
                        os.remove(netpath)

        print("\n\n\tLOADED NETWORK: " + last_path + "\n")


        if not distance and len(model.input_shape) < 3:
            X = {'test': X3_test[:-2],
                 'train': X3_train[:-2],
                 'validation': X3_validation[:-2]}
        else:
            X = {'test': X3_test,
                 'train': X3_train,
                 'validation': X3_validation}


        Y = {'test': Y_test,
             'train': Y_train,
             'validation': Y_validation}

        testfile = open(os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version, realname,
                                     name + "_eval.txt"), 'w')

        print("\n-----------------------\n")

        testfile.write(evaluation_headline)

        for split in ['test', 'validation', 'train']:

            # 2 dim
            # ax0 = samples
            # ax1 = classes
            Y_pred = model.predict(X[split])

            # begin of the evaluation of the single propositions scores
            sids = dataset[split]['s_id']
            tids = dataset[split]['t_id']

            # dic
            # each values has 2 dim
            # ax0: ids
            # ax1: classes
            s_pred_scores = {}
            s_test_scores = {}
            t_pred_scores = {}
            t_test_scores = {}

            for index in range(len(sids)):
                sid = sids[index]
                tid = tids[index]

                if sid not in s_pred_scores.keys():
                    s_pred_scores[sid] = []
                    s_test_scores[sid] = []
                s_pred_scores[sid].append(Y_pred[2][index])
                s_test_scores[sid].append(Y[split][2][index])

                if tid not in t_pred_scores.keys():
                    t_pred_scores[tid] = []
                    t_test_scores[tid] = []
                t_pred_scores[tid].append(Y_pred[3][index])
                t_test_scores[tid].append(Y[split][3][index])

            Y_pred_prop_real_list = []
            Y_test_prop_real_list = []

            for p_id in t_pred_scores.keys():
                Y_pred_prop_real_list.append(np.concatenate([s_pred_scores[p_id], t_pred_scores[p_id]]))
                Y_test_prop_real_list.append(np.concatenate([s_test_scores[p_id], t_test_scores[p_id]]))

            # 3 dim
            # ax0: ids
            # ax1: samples
            # ax2: classes
            Y_pred_prop_real_list = np.array(Y_pred_prop_real_list)
            Y_test_prop_real_list = np.array(Y_test_prop_real_list)

            Y_pred_prop_real = []
            Y_test_prop_real = []
            for index in range(len(Y_pred_prop_real_list)):
                Y_pred_prop_real.append(np.sum(Y_pred_prop_real_list[index], axis=-2))
                Y_test_prop_real.append(np.sum(Y_test_prop_real_list[index], axis=-2))

            Y_pred_prop_real = np.array(Y_pred_prop_real)
            Y_test_prop_real = np.array(Y_test_prop_real)
            Y_pred_prop_real = np.argmax(Y_pred_prop_real, axis=-1)
            Y_test_prop_real = np.argmax(Y_test_prop_real, axis=-1)
            # end of the evaluation of the single propositions scores

            Y_pred_links = np.argmax(Y_pred[0], axis=-1)
            Y_test_links = np.argmax(Y[split][0], axis=-1)

            Y_pred_rel = np.argmax(Y_pred[1], axis=-1)
            Y_test_rel = np.argmax(Y[split][1], axis=-1)

            # predictions computed! Computing measures!

            # F1s
            positive_link_labels = dataset_info[dataset_name]["link_as_sum"][0]
            negative_link_labels = dataset_info[dataset_name]["link_as_sum"][1]
            score_f1_link = f1_score(Y_test_links, Y_pred_links, average=None, labels=[0])
            score_f1_rel = f1_score(Y_test_rel, Y_pred_rel, average=None, labels=positive_link_labels)
            score_f1_rel_AVGM = f1_score(Y_test_rel, Y_pred_rel, average='macro', labels=positive_link_labels)

            score_f1_prop_real = f1_score(Y_test_prop_real, Y_pred_prop_real, average=None)
            score_f1_prop_AVGM_real = f1_score(Y_test_prop_real, Y_pred_prop_real, average='macro')
            score_f1_prop_AVGm_real = f1_score(Y_test_prop_real, Y_pred_prop_real, average='micro')

            score_f1_AVG_LP_real = np.mean([score_f1_link, score_f1_prop_AVGM_real])
            score_f1_AVG_all_real = np.mean([score_f1_link, score_f1_prop_AVGM_real, score_f1_rel_AVGM])

            """
            # Precision-recall-fscore-support
            score_prfs_prop = precision_recall_fscore_support(Y_test_prop_real, Y_pred_prop_real, average=None)
            score_prec_prop = score_prfs_prop[0]
            score_rec_prop = score_prfs_prop[1]
            score_fscore_prop = score_prfs_prop[2]
            score_supp_prop = score_prfs_prop[3]

            score_prfs_prop_AVGM = precision_recall_fscore_support(Y_test_prop_real, Y_pred_prop_real, average='macro')
            score_prec_prop_AVGM = score_prfs_prop_AVGM[0]
            score_rec_prop_AVGM = score_prfs_prop_AVGM[1]
            score_fscore_prop_AVGM = score_prfs_prop_AVGM[2]
            score_supp_prop_AVGM = score_prfs_prop_AVGM[3]

            score_prfs_prop_AVGm = precision_recall_fscore_support(Y_test_prop_real, Y_pred_prop_real, average='micro')
            score_prec_prop_AVGm = score_prfs_prop_AVGm[0]
            score_rec_prop_AVGm = score_prfs_prop_AVGm[1]
            score_fscore_prop_AVGm = score_prfs_prop_AVGm[2]
            score_supp_prop_AVGm = score_prfs_prop_AVGm[3]
            """

            iteration_scores = []
            iteration_scores.append(score_f1_AVG_all_real[0])
            iteration_scores.append(score_f1_AVG_LP_real[0])
            iteration_scores.append(score_f1_link[0])
            iteration_scores.append(score_f1_rel_AVGM)
            for score in score_f1_rel:
                iteration_scores.append(score)
            iteration_scores.append(score_f1_prop_AVGM_real)
            for score in score_f1_prop_real:
                iteration_scores.append(score)
            iteration_scores.append(score_f1_prop_AVGm_real)

            final_scores[split].append(iteration_scores)

            # writing single iteration scores
            string = split
            for value in iteration_scores:
                string += "\t" + "{:10.4f}".format(value)

            testfile.write(string + "\n")

            testfile.flush()

        with open(log_path, "a") as train_file:
            train_file.write("\n\nTraining time:\n" + str(train_time))
        testfile.write("\n\nTraining time:\n" + str(train_time))
        testfile.close()
        train_times.append(train_time)

        # END OF A ITERATION

    train_time = np.average(train_times)
    # FINAL EVALUATION
    testfile = open(os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version,
                                 realname + "_eval.txt"), 'w')

    testfile.write(evaluation_headline)
    for split in ['test', 'validation', 'train']:
        split_scores = np.array(final_scores[split], ndmin=2)
        split_scores = np.average(split_scores, axis=0)

        string = split
        for value in split_scores:
            string += "\t" + "{:10.4f}".format(value)

        testfile.write(string + "\n")

        testfile.flush()

    testfile.write("\n\nTraining time:\n" + str(train_time))
    testfile.close()





def RCT_routine():
    dataset_name = 'RCT'
    dataset_version = 'neo'
    split = 'total'
    # name = 'RCT7net2018'
    name = 'RCT11'

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=100,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60,  # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6,  # embedding_size=50
        embedder_layers=4,
        final_scale=15,  # final_size=20
        space_scale=10,
        batch_size=500,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=11,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
        clean_previous_networks=True,
    )

    evaluate_net.RCT_routine(netname='RCT11')


def cdcp_argmining18_routine():
    """
    Configuration almost identical to the Argmining18 paper (here multiple iterations are performed)
    """
    dataset_name = 'cdcp_ACL17'
    dataset_version = 'new_3'
    split = 'total'
    name = 'cdcp7net2018'

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=100,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60, # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6, # embedding_size=50
        embedder_layers=4,
        final_scale=15, # final_size=20
        space_scale=10,
        batch_size=500,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=7,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        classification="softmax",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
    )

def UKP_routine():
    dataset_name = 'AAEC_v2'
    dataset_version = 'new_2R'
    split = 'total'
    name = 'UKP11'

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=100,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60,  # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6,  # embedding_size=50
        embedder_layers=4,
        final_scale=15,  # final_size=20
        space_scale=10,
        batch_size=500,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=11,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
        clean_previous_networks=True,
    )

    netpath = os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version, name)

    evaluate_net.perform_evaluation(netpath, dataset_name, dataset_version, retrocompatibility=False, distance=5, ensemble=True)
    evaluate_net.perform_evaluation(netpath, dataset_name, dataset_version, retrocompatibility=False, distance=5, ensemble=True, token_wise=True)


# cdcp new routine
def cdcp_routine():

    dataset_name = 'cdcp_ACL17'
    dataset_version = 'new_3'
    split = 'total'
    i = 0

    i += 1
    name = 'cdcp11'+ str(i)

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=100,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60, # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6, # embedding_size=50
        embedder_layers=4,
        final_scale=15, # final_size=20
        space_scale=10,
        batch_size=500,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=11,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        classification="softmax",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
        clean_previous_networks=True,
    )

    dataset_name = 'cdcp_ACL17'
    training_dataset_version = 'new_3'
    test_dataset_version = "new_3"

    netpath = os.path.join(os.getcwd(), 'network_models', dataset_name, training_dataset_version, name)

    evaluate_net.perform_evaluation(netpath, dataset_name, test_dataset_version, retrocompatibility=False, distance=5, ensemble=True)






def scidtb_routine():

    dataset_name = 'scidtb_argmin_annotations'
    dataset_version = 'only_arg_v1'
    split = 'total'
    i = 0

    i += 1
    name = 'scidtb11'+ str(i)

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=100,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60, # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6, # embedding_size=50
        embedder_layers=4,
        final_scale=15, # final_size=20
        space_scale=10,
        batch_size=500,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=11,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        classification="softmax",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
        clean_previous_networks=True,
    )

    netpath = os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version, name)

    evaluate_net.perform_evaluation(netpath, dataset_name, dataset_version, retrocompatibility=False, distance=5, ensemble=True)
    evaluate_net.perform_evaluation(netpath, dataset_name, dataset_version, retrocompatibility=False, distance=5, ensemble=True, token_wise=True)








def drinv_routine():
    dataset_name = 'DrInventor'
    dataset_version = 'arg10'
    split = 'total'
    name = 'drinv11'

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=20,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60, # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6, # embedding_size=50
        embedder_layers=4,
        final_scale=15, # final_size=20
        space_scale=10,
        batch_size=1000,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=11,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        classification="softmax",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
    )
    netpath = os.path.join(os.getcwd(), 'network_models', dataset_name, dataset_version, name)

    evaluate_net.perform_evaluation(netpath, dataset_name, dataset_version, retrocompatibility=False, distance=5, ensemble=True, token_wise=True)




def ECHR_routine():
    dataset_name = 'ECHR2018'
    dataset_version = 'arg0'
    split = 'total'
    name = 'echr7net2018'

    perform_training(
        name=name,
        save_weights_only=True,
        epochs=10000,
        feature_type='bow',
        patience=50,
        loss_weights=[0, 10, 1, 1],
        lr_alfa=0.005,
        lr_kappa=0.001,
        beta_1=0.9,
        beta_2=0.9999,
        res_scale=60, # res_siz =5
        resnet_layers=(1, 2),
        embedding_scale=6, # embedding_size=50
        embedder_layers=4,
        final_scale=15, # final_size=20
        space_scale=10,
        batch_size=1000,
        regularizer_weight=0.0001,
        dropout_resnet=0.1,
        dropout_embedder=0.1,
        dropout_final=0.1,
        bn_embed=True,
        bn_res=True,
        bn_final=True,
        network=7,
        monitor="links",
        true_validation=True,
        temporalBN=False,
        same_layers=False,
        distance=5,
        iterations=10,
        merge=None,
        single_LSTM=True,
        pooling=10,
        text_pooling=50,
        pooling_type='avg',
        classification="softmax",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=split,
    )


if __name__ == '__main__':

    global DIM
    DIM = 300

    parser = argparse.ArgumentParser(description="Perform training procedure")
    parser.add_argument('-c', '--corpus',
                        choices=["rct", "drinv", "cdcp", "echr", "ukp", "scidtb"],
                        help="corpus", default="cdcp")

    args = parser.parse_args()

    corpus = args.corpus

    if corpus.lower() == "rct":
        RCT_routine()
    elif corpus.lower() == "cdcp":
        cdcp_routine()
    elif corpus.lower() == "drinv":
        drinv_routine()
    elif corpus.lower() == "ukp":
        UKP_routine()
    elif corpus.lower() == "scidtb":
        scidtb_routine()

