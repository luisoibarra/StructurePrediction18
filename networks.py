__author__ = "Andrea Galassi"
__copyright__ = "Copyright 2018, Andrea Galassi"
__license__ = "BSD 3-clause"
__version__ = "0.0.1"
__email__ = "a.galassi@unibo.it"


"""
Code for creating some neural network models. Don't judge them, please. They are just born this way.
"""

from tensorflow.python.ops import math_ops
import tensorflow as tf
import tensorflow.keras as keras
import numpy as np
import tensorflow.keras.backend as K
from tensorflow.keras.layers import (BatchNormalization, Dropout, Dense, Input, Activation, LSTM, Conv1D, Add, Lambda, MaxPool1D,
                          Bidirectional, Concatenate, Flatten, Embedding, TimeDistributed, AveragePooling1D, Multiply,
                          GlobalAveragePooling1D, GlobalMaxPooling1D, Reshape, Permute, RepeatVector, Masking)
# from keras.utils.vis_utils import plot_model
# from tensorflow.contrib.sparsemax import sparsemax
import pydot
from glove_loader import DIM
import sys
from attentionLayers import AdditiveAttention

def make_resnet(input_layer, regularizer_weight, layers=(2, 2), res_size=int(DIM/3)*3, dropout=0, bn=True):
    prev_layer = input_layer
    prev_block = prev_layer
    blocks = layers[0]
    res_layers = layers[1]

    shape = int(np.shape(input_layer)[1])

    for i in range(1, blocks + 1):
        for j in range(1, res_layers):
            if bn:
                prev_layer = BatchNormalization(name='resent_BN_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Dropout(dropout, name='resnet_Dropout_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Activation('relu', name='resnet_ReLU_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Dense(units=res_size,
                               activation=None,
                               kernel_initializer='he_normal',
                               kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                               bias_regularizer=keras.regularizers.l2(regularizer_weight),
                               name='resnet_dense_' + str(i) + '_' + str(j)
                               )(prev_layer)
        if bn:
            prev_layer = BatchNormalization(name='BN_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Dropout(dropout, name='resnet_Dropout_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Activation('relu', name='resnet_ReLU_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Dense(units=shape,
                           activation=None,
                           kernel_initializer='he_normal',
                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                           name='resnet_dense_' + str(i) + '_' + str(res_layers)
                           )(prev_layer)

        prev_layer = Add(name='resnet_sum' + str(i))([prev_block, prev_layer])
        prev_block = prev_layer

    return prev_block



def make_ffnet(input_layer, regularizer_weight, layers=(2, 2), res_size=int(DIM/3)*3, dropout=0, bn=True):
    prev_layer = input_layer
    prev_block = prev_layer
    blocks = layers[0]
    res_layers = layers[1]

    shape = int(np.shape(input_layer)[1])

    for i in range(1, blocks + 1):
        for j in range(1, res_layers):
            if bn:
                prev_layer = BatchNormalization(name='resent_BN_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Dropout(dropout, name='resnet_Dropout_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Activation('relu', name='resnet_ReLU_' + str(i) + '_' + str(j))(prev_layer)

            prev_layer = Dense(units=res_size,
                               activation=None,
                               kernel_initializer='he_normal',
                               kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                               bias_regularizer=keras.regularizers.l2(regularizer_weight),
                               name='resnet_dense_' + str(i) + '_' + str(j)
                               )(prev_layer)
        if bn:
            prev_layer = BatchNormalization(name='BN_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Dropout(dropout, name='resnet_Dropout_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Activation('relu', name='resnet_ReLU_' + str(i) + '_' + str(res_layers))(prev_layer)

        prev_layer = Dense(units=shape,
                           activation=None,
                           kernel_initializer='he_normal',
                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                           name='resnet_dense_' + str(i) + '_' + str(res_layers)
                           )(prev_layer)

        prev_block = prev_layer

    return prev_block


def make_embedder(input_layer, layer_name, regularizer_weight,
                  layers=2, layers_size=int(DIM/10), embedding_size=int(DIM/3), dropout=0, use_conv=True):
    prev_layer = input_layer

    shape = int(np.shape(input_layer)[2])
    for i in range(1, layers):

        prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(i))(prev_layer)

        prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(i))(prev_layer)

        prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(i))(prev_layer)

        if use_conv:

            prev_layer = Conv1D(filters=layers_size,
                                kernel_size=3,
                                padding='same',
                                activation=None,
                                kernel_initializer='he_normal',
                                kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                name=layer_name + '_conv_' + str(i)
                                )(prev_layer)
        else:
            prev_layer = TimeDistributed(Dense(units=layers_size,
                                               activation=None,
                                               kernel_initializer='he_normal',
                                               kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                               bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                               name=layer_name + '_dense_' + str(i)
                                               ))(prev_layer)

    prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(layers))(prev_layer)

    prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(layers))(prev_layer)

    prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(layers))(prev_layer)

    if use_conv:
        prev_layer = Conv1D(filters=shape,
                            kernel_size=3,
                            padding='same',
                            activation=None,
                            kernel_initializer='he_normal',
                            kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                            bias_regularizer=keras.regularizers.l2(regularizer_weight),
                            name=layer_name + '_conv_' + str(layers)
                            )(prev_layer)
    else:
        prev_layer = TimeDistributed(Dense(units=shape,
                                           activation=None,
                                           kernel_initializer='he_normal',
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           name=layer_name + '_dense_' + str(layers)
                                           ))(prev_layer)

    prev_layer = Add(name=layer_name + '_sum')([input_layer, prev_layer])

    prev_layer = BatchNormalization(name=layer_name + '_BN')(prev_layer)

    text_LSTM = Bidirectional(LSTM(units=embedding_size,
                                   dropout=dropout,
                                   recurrent_dropout=dropout,
                                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                   recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                   return_sequences=False,
                                   unroll=False, # not possible to unroll if the time shape is not specified
                                   name=layer_name + '_LSTM'),
                              merge_mode='mul',
                              )(prev_layer)

    return text_LSTM


def make_deep_word_embedder(input_layer, layer_name, regularizer_weight,
                            layers=2, layers_size=int(DIM/10), dropout=0, bn=True):
    prev_layer = input_layer

    shape = int(np.shape(input_layer)[2])
    for i in range(1, layers):

        if bn:
            prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(i))(prev_layer)

        prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(i))(prev_layer)

        prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(i))(prev_layer)

        prev_layer = TimeDistributed(Dense(units=layers_size,
                                           activation=None,
                                           kernel_initializer='he_normal',
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           name=layer_name + '_dense_' + str(i)
                                           ),
                                     name=layer_name + '_TD_' + str(i))(prev_layer)
    if bn:
        prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(layers))(prev_layer)

    prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(layers))(prev_layer)

    prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(layers))(prev_layer)

    prev_layer = TimeDistributed(Dense(units=shape,
                                       activation=None,
                                       kernel_initializer='he_normal',
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       name=layer_name + '_dense_' + str(layers)
                                       ),
                                 name=layer_name + '_TD_' + str(layers))(prev_layer)

    prev_layer = Add(name=layer_name + '_sum')([input_layer, prev_layer])

    return prev_layer


def make_embedder_layers(regularizer_weight, shape, layers=2, layers_size=int(DIM/10), dropout=0.1,
                         temporalBN=False):
    bn_list_prop = []
    layers_list = []
    dropout_list = []
    activation_list = []
    bn_list_text = []

    if layers > 0:
        layer = Dense(units=shape,
                      activation=None,
                      kernel_initializer='he_normal',
                      kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                      bias_regularizer=keras.regularizers.l2(regularizer_weight),
                      name='dense_' + str(layers))
        layers_list.append(layer)
        if temporalBN:
            bn_list_prop.append(BatchNormalization(axis=-2, name="TBN_prop_" + str(layers)))
            bn_list_text.append(BatchNormalization(axis=-2, name="TBN_text_" + str(layers)))
        else:
            bn_list_prop.append(BatchNormalization(name="BN_" + str(layers)))
        dropout_list.append(Dropout(dropout, name='Dropout_' + str(layers)))
        activation_list.append(Activation('relu', name='ReLU_' + str(layers)))

    for i in range(1, layers):
        layer = Dense(units=layers_size,
                      activation=None,
                      kernel_initializer='he_normal',
                      kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                      bias_regularizer=keras.regularizers.l2(regularizer_weight),
                      name='dense_' + str(i))
        if temporalBN:
            bn_list_prop.append(BatchNormalization(axis=-2, name="TBN_prop_" + str(i)))
            bn_list_text.append(BatchNormalization(axis=-2, name="TBN_text_" + str(i)))
        else:
            bn_list_prop.append(BatchNormalization(name="BN_" + str(i)))
        layers_list.append(layer)
        dropout_list.append(Dropout(dropout, name='Dropout_' + str(i)))
        activation_list.append(Activation('relu', name='ReLU_' + str(i)))

    add_layer = Add(name='sum')

    return layers_list, bn_list_prop, dropout_list, activation_list, add_layer, bn_list_text


def make_embedder_with_layers(input_layer, layer_name, layers, dropout=0, bn=True, temporalBN=False, residual=True):
    prev_layer = input_layer

    for i in range(1, len(layers)):

        if bn:
            if temporalBN:
                prev_layer = BatchNormalization(axis=-2, name=layer_name + '_TBN_' + str(i))(prev_layer)
            else:
                prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(i))(prev_layer)

        prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(i))(prev_layer)

        prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(i))(prev_layer)

        prev_layer = TimeDistributed(layers[i],
                                     name=layer_name + '_TD_' + str(i))(prev_layer)
    if bn:
        if temporalBN:
            prev_layer = BatchNormalization(axis=-2, name=layer_name + '_TBN_' + str(len(layers)))(prev_layer)
        else:
            prev_layer = BatchNormalization(name=layer_name + '_BN_' + str(len(layers)))(prev_layer)

    prev_layer = Dropout(dropout, name=layer_name + '_Dropout_' + str(len(layers)))(prev_layer)

    prev_layer = Activation('relu', name=layer_name + '_ReLU_' + str(len(layers)))(prev_layer)

    prev_layer = TimeDistributed(layers[0],
                                 name=layer_name + '_TD_' + str(len(layers)))(prev_layer)

    if residual:
        prev_layer = Add(name=layer_name + '_sum')([input_layer, prev_layer])

    return prev_layer


def make_embedder_with_all_layers(input_layer, layer_name, layers, bn=True, temporalBN=False, residual=True):
    prev_layer = input_layer

    bn_layers = layers[1]
    dropout_layers = layers[2]
    activation_layers = layers[3]
    add_layer = layers[4]
    bn_t_layers = layers[5]
    layers = layers[0]

    for i in range(1, len(layers)):

        if bn:
            if temporalBN:
                if layer_name == 'text':
                    prev_layer = bn_t_layers[i](prev_layer)
                else:
                    prev_layer = bn_layers[i](prev_layer)
            else:
                prev_layer = bn_layers[i](prev_layer)

        prev_layer = dropout_layers[i](prev_layer)

        prev_layer = activation_layers[i](prev_layer)

        prev_layer = TimeDistributed(layers[i],
                                     name=layer_name + '_TD_' + str(i))(prev_layer)
    if bn:
        if temporalBN:
            if layer_name == 'text':
                prev_layer = bn_t_layers[0](prev_layer)
            else:
                prev_layer = bn_layers[0](prev_layer)
        else:
            prev_layer = bn_layers[0](prev_layer)

    prev_layer = dropout_layers[0](prev_layer)

    prev_layer = activation_layers[0](prev_layer)

    prev_layer = TimeDistributed(layers[0],
                                 name=layer_name + '_TD_' + str(len(layers)))(prev_layer)

    if residual:
        prev_layer = add_layer([input_layer, prev_layer])

    return prev_layer


# net 7 with attention
def build_net_10(bow,
                propos_length,
                outputs,
                link_as_sum,
                distance,
                text_length=200,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0,
                embedding_size=int(25),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_size=50,
                final_size=int(20),
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                single_LSTM=False,
                pooling=0,
                text_pooling=0,
                pooling_type='avg',
                same_DE_layers=False,
                context=True,
                temporalBN=False, ):
    """
    Creates a neural network that takes as input two components (propositions) and ouputs the class of the two
    components, whether a relation between the two exists, and the class of that relation.



    :param bow: If it is different from None, it is the matrix with the pre-trained embeddings used by the Embedding
                layer of keras, the input is supposed in BoW form.
                If it is None, the input is supposed to already contain pre-trained embeddings.
    :param text_length: The temporal length of the text input
    :param propos_length: The temporal length of the proposition input
    :param regularizer_weight: Regularization weight
    :param dropout_embedder: Dropout used in the embedder
    :param dropout_resnet: Dropout used in the residual network
    :param dropout_final: Dropout used in the final classifiers
    :param embedding_size: Size of the spatial reduced embeddings
    :param embedder_layers: Number of layers in the initial embedder (int)
    :param resnet_layers: Number of layers in the final residual network. Tuple where the first value indicates the
                          number of blocks and the second the number of layers per block
    :param res_size: Number of neurons in the residual blocks
    :param final_size: Number of neurons of the final layer
    :param outputs: Tuple, the classes of the four classifiers: link, relation, source, target
    :param link_as_sum: if None, the link classifier will be built as usual. If it is an array of arrays: the outputs
                        of the relation classifier will be summed together according to the values in the arrays.
                        Example: if the link classification is binary, and its contributions from relation
                        classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                        [[0, 2], [1, 3, 4]]
    :param bn_embed: Whether the batch normalization should be used in the embedding block
    :param bn_res: Whether the batch normalization should be used in the residual blocks
    :param bn_final: Whether the batch normalization should be used in the final layer
    :param single_LSTM: Whether the same LSTM should be used both for processing the target and the source
    :param pooling:
    :param text_pooling:
    :param pooling_type: 'avg' or 'max' pooling
    :param same_DE_layers: Whether the deep embedder layers should be shared between source and target
    :param context: If the context (the original text) should be used as input
    :param distance: The maximum distance that is taken into account
    :param temporalBN: Whether temporal batch-norm is applied
    :return:
    """

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    if distance > 0:
        dist_il = Input(shape=(int(distance * 2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])
    layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                  layers_size=embedding_size, temporalBN=temporalBN)
    if same_DE_layers:
        make_embedder = make_embedder_with_all_layers
    else:
        make_embedder = make_embedder_with_layers
        layers = layers[0]

    if embedder_layers > 0:
        prev_text_l = make_embedder(prev_text_l, 'text', dropout=dropout_embedder, layers=layers,
                                    bn=bn_embed, temporalBN=temporalBN)

        prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)
        prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_text_l = bn_layer_t(prev_text_l)
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_text_l = drop_layer(prev_text_l)
        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_text_l = BatchNormalization(axis=-2)(prev_text_l)
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_text_l = BatchNormalization()(prev_text_l)
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_text_l = Dropout(dropout_embedder)(prev_text_l)
        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    # COARSE-GRAINED CO-ATTENTION (Ma et al) + ADDITIVE ATTENTION (Bahdanau et al):
    # average of the two act as query on the other

    # create keys using dense layer
    print("Source shape")
    print(prev_source_l.shape)
    source_linearity = Dense(units=embedding_size,
                          name='att_linearity_K_source')
    source_keys = TimeDistributed(source_linearity, name='att_K_source')(prev_source_l)
    print("Keys shape")
    print(source_keys.shape)
    target_linearity = Dense(units=embedding_size,
                          name='att_linearity_K_target')
    target_keys = TimeDistributed(target_linearity, name='att_K_target')(prev_target_l)

    # create query elements doing average and then multiplication
    source_avg = GlobalAveragePooling1D(name="avg_query_source")(prev_source_l)
    print("source avg")
    print(source_avg.shape)
    target_avg = GlobalAveragePooling1D(name="avg_query_target")(prev_target_l)
    source_query = source_linearity(target_avg)
    target_query = source_linearity(source_avg)
    print("target query")
    print(target_query.shape)

    time_shape = (source_keys.shape)[1]
    space_shape = (source_keys.shape)[2]

    # repeat the query and sum
    source_query = RepeatVector(time_shape, name='repeat_query_source')(source_query)
    target_query = RepeatVector(time_shape, name='repeat_query_target')(target_query)
    print("repeat target query")
    print(target_query.shape)
    source_score = Add(name='att_addition_source')([source_query, source_keys])
    target_score = Add(name='att_addition_target')([target_query, target_keys])
    print("target score (sum)")
    print(target_score.shape)

    # activation and dot product with importance vector
    target_score = Activation(activation='relu', name='att_activation_target')(target_score)
    source_score = Activation(activation='relu', name='att_activation_source')(source_score)
    print("target score (activation)")
    print(target_score.shape)
    imp_v_target = Dense(units=1,
                          kernel_initializer='he_normal',
                          name='importance_vector_target')
    target_score = TimeDistributed(imp_v_target, name='att_scores_target')(target_score)
    imp_v_source = Dense(units=1,
                          kernel_initializer='he_normal',
                          name='importance_vector_source')
    source_score = TimeDistributed(imp_v_source, name='att_scores_source')(source_score)
    print("target score (dot product)")
    print(target_score.shape)

    # application of mask: padding layer are associated to very negative scores to improve softmax
    source_score = Flatten(name='att_scores_flat_source')(source_score)
    target_score = Flatten(name='att_scores_flat_target')(target_score)
    print("target score (flat)")
    print(target_score.shape)
    maskLayer = Lambda(create_padding_mask_fn(), name='masking')
    negativeLayer = Lambda(create_mutiply_negative_elements_fn(), name='negative_mul')
    mask_source = maskLayer(sourceprop_il)
    mask_target = maskLayer(targetprop_il)
    print("target mask (01)")
    print(mask_target.shape)
    neg_source = negativeLayer(mask_source)
    neg_target = negativeLayer(mask_target)
    print("target mask (negative)")
    print(neg_target.shape)
    source_score = Add(name='att_masked_addition_source')([neg_source, source_score])
    target_score = Add(name='att_masked_addition_target')([neg_target, target_score])
    print("target score (masked)")
    print(neg_target.shape)

    # softmax application
    source_weight = Activation(activation='softmax', name='att_weights_source')(source_score)
    target_weight = Activation(activation='softmax', name='att_weights_target')(target_score)
    print("target weights (softmax)")
    print(target_weight.shape)

    # weighted sum
    source_weight = Reshape(target_shape=(source_weight.shape[-1], 1), name='att_weights_reshape_source')(source_weight)
    target_weight = Reshape(target_shape=(target_weight.shape[-1], 1), name='att_weights_reshape_target')(target_weight)
    print("target weights (reshape)")
    print(target_weight.shape)
    source_weighted = Multiply(name='att_multiply_source')([source_weight, prev_source_l])
    target_weighted = Multiply(name='att_multiply_target')([target_weight, prev_target_l])
    print("target weighted values")
    print(target_weighted.shape)
    source_embed2 = Lambda(create_sum_fn(1), name='att_cv_source')(source_weighted)
    target_embed2 = Lambda(create_sum_fn(1), name='att_cv_target')(target_weighted)
    print("target context vector")
    print(target_embed2.shape)

    """
    # ATTENTION FOLLOWING KERAS LIBRARY (WRONG!!!!!!!!!!)
    # reshape for compatibility
    source_query = Reshape((1, embedding_size), input_shape=(embedding_size,), name='expand_source')(source_query)
    print("target query reshaped")
    print(source_query.shape)
    target_query = Reshape((1, embedding_size), input_shape=(embedding_size,), name='expand_target')(target_query)
    # apply attention
    source_embed2 = AdditiveAttention(name="att_source", use_scale=True)([source_query, prev_source_l, source_keys])
    print("attention source")
    print(source_embed2.shape)
    target_embed2 = AdditiveAttention(name="att_target", use_scale=True)([target_query, prev_target_l, target_keys])
    # average of context vectors (it should be only 1 context vector, use of average for compatibility with other ideas)
    source_embed2 = GlobalAveragePooling1D(name="avg_att_source")(source_embed2)
    print("attention source averaged")
    print(source_embed2.shape)
    target_embed2 = GlobalAveragePooling1D(name="avg_att_target")(target_embed2)
    """

    if context and distance > 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                        name='link',
                        activation='softmax',
                        )(prev_l)
    else:
        link_scores = []
        rel_scores = []
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i + 1), name='rel' + str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute = []
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_' + str(i))(link_contribute)
            link_scores.append(link_class)

        link_ol = Concatenate(name='link')(link_scores)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=[text_il, sourceprop_il, targetprop_il, dist_il, mark_il],
                             outputs=[link_ol, rel_ol, source_ol, target_ol],
                             )

    return full_model




# net 7 with attention
def build_net_9(bow,
                propos_length,
                outputs,
                link_as_sum,
                distance,
                text_length=200,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0,
                embedding_size=int(25),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_size=50,
                final_size=int(20),
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                single_LSTM=False,
                pooling=0,
                text_pooling=0,
                pooling_type='avg',
                same_DE_layers=False,
                context=True,
                temporalBN=False, ):
    """
    Creates a neural network that takes as input two components (propositions) and ouputs the class of the two
    components, whether a relation between the two exists, and the class of that relation.



    :param bow: If it is different from None, it is the matrix with the pre-trained embeddings used by the Embedding
                layer of keras, the input is supposed in BoW form.
                If it is None, the input is supposed to already contain pre-trained embeddings.
    :param text_length: The temporal length of the text input
    :param propos_length: The temporal length of the proposition input
    :param regularizer_weight: Regularization weight
    :param dropout_embedder: Dropout used in the embedder
    :param dropout_resnet: Dropout used in the residual network
    :param dropout_final: Dropout used in the final classifiers
    :param embedding_size: Size of the spatial reduced embeddings
    :param embedder_layers: Number of layers in the initial embedder (int)
    :param resnet_layers: Number of layers in the final residual network. Tuple where the first value indicates the
                          number of blocks and the second the number of layers per block
    :param res_size: Number of neurons in the residual blocks
    :param final_size: Number of neurons of the final layer
    :param outputs: Tuple, the classes of the four classifiers: link, relation, source, target
    :param link_as_sum: if None, the link classifier will be built as usual. If it is an array of arrays: the outputs
                        of the relation classifier will be summed together according to the values in the arrays.
                        Example: if the link classification is binary, and its contributions from relation
                        classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                        [[0, 2], [1, 3, 4]]
    :param bn_embed: Whether the batch normalization should be used in the embedding block
    :param bn_res: Whether the batch normalization should be used in the residual blocks
    :param bn_final: Whether the batch normalization should be used in the final layer
    :param single_LSTM: Whether the same LSTM should be used both for processing the target and the source
    :param pooling:
    :param text_pooling:
    :param pooling_type: 'avg' or 'max' pooling
    :param same_DE_layers: Whether the deep embedder layers should be shared between source and target
    :param context: If the context (the original text) should be used as input
    :param distance: The maximum distance that is taken into account
    :param temporalBN: Whether temporal batch-norm is applied
    :return:
    """

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    if distance > 0:
        dist_il = Input(shape=(int(distance * 2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])
    layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                  layers_size=embedding_size, temporalBN=temporalBN)
    if same_DE_layers:
        make_embedder = make_embedder_with_all_layers
    else:
        make_embedder = make_embedder_with_layers
        layers = layers[0]

    if embedder_layers > 0:
        prev_text_l = make_embedder(prev_text_l, 'text', dropout=dropout_embedder, layers=layers,
                                    bn=bn_embed, temporalBN=temporalBN)

        prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)
        prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_text_l = bn_layer_t(prev_text_l)
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_text_l = drop_layer(prev_text_l)
        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_text_l = BatchNormalization(axis=-2)(prev_text_l)
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_text_l = BatchNormalization()(prev_text_l)
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_text_l = Dropout(dropout_embedder)(prev_text_l)
        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    relu_embedder = Dense(units=embedding_size,
                          activation='relu',
                          kernel_initializer='he_normal',
                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                          name='relu_embedder')

    prev_text_l = TimeDistributed(relu_embedder, name='TD_text_embedder')(prev_text_l)
    TD_prop = TimeDistributed(relu_embedder, name='TD_prop_embedder')
    prev_source_l = TD_prop(prev_source_l)
    prev_target_l = TD_prop(prev_target_l)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    '''
    if pooling > 0:
        if pooling_type == 'max':
            pooling_class = MaxPool1D
        else:
            pooling_class = AveragePooling1D
        prop_pooling = pooling_class(pool_size=pooling, name='prop_pooling')
        prev_source_l = prop_pooling(prev_source_l)
        prev_target_l = prop_pooling(prev_target_l)

        if context:
            # if text_pooling is negative, the same pooling of the propositions is used
            if not text_pooling > 0:
                text_pooling = pooling
            prev_text_l = pooling_class(pool_size=text_pooling, name='text_pooling')(prev_text_l)
    '''
    if bn_embed:
        if temporalBN:
            prev_text_l = BatchNormalization(name="TBN_LSTM_text", axis=-2)(prev_text_l)
        else:
            prev_text_l = BatchNormalization(name="BN_LSTM_text")(prev_text_l)

    # COARSE-GRAINED CO-ATTENTION (Ma et al) + ADDITIVE ATTENTION (Bahdanau et al):
    # average of the two act as query on the other

    # create keys using dense layer
    print("Source shape")
    print(prev_source_l.shape)
    source_linearity = Dense(units=embedding_size,
                          name='att_linearity_K_source')
    source_keys = TimeDistributed(source_linearity, name='att_K_source')(prev_source_l)
    print("Keys shape")
    print(source_keys.shape)
    target_linearity = Dense(units=embedding_size,
                          name='att_linearity_K_target')
    target_keys = TimeDistributed(target_linearity, name='att_K_target')(prev_target_l)

    # create query elements doing average and then multiplication
    source_avg = GlobalAveragePooling1D(name="avg_query_source")(prev_source_l)
    print("source avg")
    print(source_avg.shape)
    target_avg = GlobalAveragePooling1D(name="avg_query_target")(prev_target_l)
    source_query = source_linearity(target_avg)
    target_query = source_linearity(source_avg)
    print("target query")
    print(target_query.shape)

    time_shape = (source_keys.shape)[1]
    space_shape = (source_keys.shape)[2]

    # repeat the query and sum
    source_query = RepeatVector(time_shape, name='repeat_query_source')(source_query)
    target_query = RepeatVector(time_shape, name='repeat_query_target')(target_query)
    print("repeat target query")
    print(target_query.shape)
    source_score = Add(name='att_addition_source')([source_query, source_keys])
    target_score = Add(name='att_addition_target')([target_query, target_keys])
    print("target score (sum)")
    print(target_score.shape)

    # activation and dot product with importance vector
    target_score = Activation(activation='relu', name='att_activation_target')(target_score)
    source_score = Activation(activation='relu', name='att_activation_source')(source_score)
    print("target score (activation)")
    print(target_score.shape)
    imp_v_target = Dense(units=1,
                          kernel_initializer='he_normal',
                          name='importance_vector_target')
    target_score = TimeDistributed(imp_v_target, name='att_scores_target')(target_score)
    imp_v_source = Dense(units=1,
                          kernel_initializer='he_normal',
                          name='importance_vector_source')
    source_score = TimeDistributed(imp_v_source, name='att_scores_source')(source_score)
    print("target score (dot product)")
    print(target_score.shape)

    # application of mask: padding layer are associated to very negative scores to improve softmax
    source_score = Flatten(name='att_scores_flat_source')(source_score)
    target_score = Flatten(name='att_scores_flat_target')(target_score)
    print("target score (flat)")
    print(target_score.shape)
    maskLayer = Lambda(create_padding_mask_fn(), name='masking')
    negativeLayer = Lambda(create_mutiply_negative_elements_fn(), name='negative_mul')
    mask_source = maskLayer(sourceprop_il)
    mask_target = maskLayer(targetprop_il)
    print("target mask (01)")
    print(mask_target.shape)
    neg_source = negativeLayer(mask_source)
    neg_target = negativeLayer(mask_target)
    print("target mask (negative)")
    print(neg_target.shape)
    source_score = Add(name='att_masked_addition_source')([neg_source, source_score])
    target_score = Add(name='att_masked_addition_target')([neg_target, target_score])
    print("target score (masked)")
    print(neg_target.shape)

    # softmax application
    source_weight = Activation(activation='softmax', name='att_weights_source')(source_score)
    target_weight = Activation(activation='softmax', name='att_weights_target')(target_score)
    print("target weights (softmax)")
    print(target_weight.shape)

    # weighted sum
    source_weight = Reshape(target_shape=(source_weight.shape[-1], 1), name='att_weights_reshape_source')(source_weight)
    target_weight = Reshape(target_shape=(target_weight.shape[-1], 1), name='att_weights_reshape_target')(target_weight)
    print("target weights (reshape)")
    print(target_weight.shape)
    source_weighted = Multiply(name='att_multiply_source')([source_weight, prev_source_l])
    target_weighted = Multiply(name='att_multiply_target')([target_weight, prev_target_l])
    print("target weighted values")
    print(target_weighted.shape)
    source_embed2 = Lambda(create_sum_fn(1), name='att_cv_source')(source_weighted)
    target_embed2 = Lambda(create_sum_fn(1), name='att_cv_target')(target_weighted)
    print("target context vector")
    print(target_embed2.shape)

    """
    # ATTENTION FOLLOWING KERAS LIBRARY (WRONG!!!!!!!!!!)
    # reshape for compatibility
    source_query = Reshape((1, embedding_size), input_shape=(embedding_size,), name='expand_source')(source_query)
    print("target query reshaped")
    print(source_query.shape)
    target_query = Reshape((1, embedding_size), input_shape=(embedding_size,), name='expand_target')(target_query)
    # apply attention
    source_embed2 = AdditiveAttention(name="att_source", use_scale=True)([source_query, prev_source_l, source_keys])
    print("attention source")
    print(source_embed2.shape)
    target_embed2 = AdditiveAttention(name="att_target", use_scale=True)([target_query, prev_target_l, target_keys])
    # average of context vectors (it should be only 1 context vector, use of average for compatibility with other ideas)
    source_embed2 = GlobalAveragePooling1D(name="avg_att_source")(source_embed2)
    print("attention source averaged")
    print(source_embed2.shape)
    target_embed2 = GlobalAveragePooling1D(name="avg_att_target")(target_embed2)
    """

    if context and distance > 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                        name='link',
                        activation='softmax',
                        )(prev_l)
    else:
        link_scores = []
        rel_scores = []
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i + 1), name='rel' + str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute = []
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_' + str(i))(link_contribute)
            link_scores.append(link_class)

        link_ol = Concatenate(name='link')(link_scores)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=[text_il, sourceprop_il, targetprop_il, dist_il, mark_il],
                             outputs=[link_ol, rel_ol, source_ol, target_ol],
                             )

    return full_model


# Space reduction, LSTM, attention
def build_net_11(bow,
                propos_length,
                outputs,
                link_as_sum,
                distance,
                text_length=200,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0,
                embedding_size=int(25),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_size=50,
                final_size=int(20),
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                single_LSTM=False,
                pooling=0,
                text_pooling=0,
                pooling_type='avg',
                same_DE_layers=False,
                context=True,
                temporalBN=False, ):
    """
    Creates a neural network that takes as input two components (propositions) and ouputs the class of the two
    components, whether a relation between the two exists, and the class of that relation.



    :param bow: If it is different from None, it is the matrix with the pre-trained embeddings used by the Embedding
                layer of keras, the input is supposed in BoW form.
                If it is None, the input is supposed to already contain pre-trained embeddings.
    :param text_length: The temporal length of the text input
    :param propos_length: The temporal length of the proposition input
    :param regularizer_weight: Regularization weight
    :param dropout_embedder: Dropout used in the embedder
    :param dropout_resnet: Dropout used in the residual network
    :param dropout_final: Dropout used in the final classifiers
    :param embedding_size: Size of the spatial reduced embeddings
    :param embedder_layers: Number of layers in the initial embedder (int)
    :param resnet_layers: Number of layers in the final residual network. Tuple where the first value indicates the
                          number of blocks and the second the number of layers per block
    :param res_size: Number of neurons in the residual blocks
    :param final_size: Number of neurons of the final layer
    :param outputs: Tuple, the classes of the four classifiers: link, relation, source, target
    :param link_as_sum: if None, the link classifier will be built as usual. If it is an array of arrays: the outputs
                        of the relation classifier will be summed together according to the values in the arrays.
                        Example: if the link classification is binary, and its contributions from relation
                        classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                        [[0, 2], [1, 3, 4]]
    :param bn_embed: Whether the batch normalization should be used in the embedding block
    :param bn_res: Whether the batch normalization should be used in the residual blocks
    :param bn_final: Whether the batch normalization should be used in the final layer
    :param single_LSTM: Whether the same LSTM should be used both for processing the target and the source
    :param pooling:
    :param text_pooling:
    :param pooling_type: 'avg' or 'max' pooling
    :param same_DE_layers: Whether the deep embedder layers should be shared between source and target
    :param context: If the context (the original text) should be used as input
    :param distance: The maximum distance that is taken into account
    :param temporalBN: Whether temporal batch-norm is applied
    :return:
    """

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    if distance > 0:
        dist_il = Input(shape=(int(distance * 2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])
    layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                  layers_size=embedding_size, temporalBN=temporalBN)
    if same_DE_layers:
        make_embedder = make_embedder_with_all_layers
    else:
        make_embedder = make_embedder_with_layers
        layers = layers[0]

    if embedder_layers > 0:
        prev_text_l = make_embedder(prev_text_l, 'text', dropout=dropout_embedder, layers=layers,
                                    bn=bn_embed, temporalBN=temporalBN)

        prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)
        prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_text_l = bn_layer_t(prev_text_l)
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_text_l = drop_layer(prev_text_l)
        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_text_l = BatchNormalization(axis=-2)(prev_text_l)
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_text_l = BatchNormalization()(prev_text_l)
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_text_l = Dropout(dropout_embedder)(prev_text_l)
        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    relu_embedder = Dense(units=embedding_size,
                          activation='relu',
                          kernel_initializer='he_normal',
                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                          name='relu_embedder')

    prev_text_l = TimeDistributed(relu_embedder, name='TD_text_embedder')(prev_text_l)
    TD_prop = TimeDistributed(relu_embedder, name='TD_prop_embedder')
    prev_source_l = TD_prop(prev_source_l)
    prev_target_l = TD_prop(prev_target_l)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    if bn_embed:
        if temporalBN:
            prev_text_l = BatchNormalization(name="TBN_LSTM_text", axis=-2)(prev_text_l)
        else:
            prev_text_l = BatchNormalization(name="BN_LSTM_text")(prev_text_l)

    if single_LSTM:
        if bn_embed:

            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_LSTM_prop", axis=-2)
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)
            else:
                bn_layer = BatchNormalization(name="BN_LSTM_prop")
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)

        embed2 = Bidirectional(LSTM(units=embedding_size,
                                    dropout=dropout_embedder,
                                    recurrent_dropout=dropout_embedder,
                                    kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                    recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                    bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                    return_sequences=True,
                                    unroll=False,  # not possible to unroll if the time shape is not specified
                                    name='prop_LSTM',
                                    ),
                               merge_mode='mul',
                               name='biLSTM'
                               )

        source_embed2 = embed2(prev_source_l)
        target_embed2 = embed2(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=True,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='text_LSTM'),
                                    merge_mode='mul',
                                    name='text_biLSTM'
                                    )(prev_text_l)
    else:
        if bn_embed:
            if temporalBN:
                prev_source_l = BatchNormalization(name="TBN_LSTM_source", axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(name="TBN_LSTM_target", axis=-2)(prev_target_l)
            else:
                prev_source_l = BatchNormalization(name="BN_LSTM_source")(prev_source_l)
                prev_target_l = BatchNormalization(name="BN_LSTM_target")(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=True,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='text_LSTM'),
                                    merge_mode='mul',
                                    name='text_biLSTM'
                                    )(prev_text_l)

        source_embed2 = Bidirectional(LSTM(units=embedding_size,
                                           dropout=dropout_embedder,
                                           recurrent_dropout=dropout_embedder,
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           return_sequences=True,
                                           unroll=False,  # not possible to unroll if the time shape is not specified
                                           name='source_LSTM'),
                                      merge_mode='mul',
                                      name='source_biLSTM'
                                      )(prev_source_l)

        target_embed2 = Bidirectional(LSTM(units=embedding_size,
                                           dropout=dropout_embedder,
                                           recurrent_dropout=dropout_embedder,
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           return_sequences=True,
                                           unroll=False,  # not possible to unroll if the time shape is not specified
                                           name='target_LSTM'),
                                      merge_mode='mul',
                                      name='target_biLSTM'
                                      )(prev_target_l)

    # COARSE-GRAINED CO-ATTENTION (Ma et al) + ADDITIVE ATTENTION (Bahdanau et al):
    # average of the two act as query on the other

    # create keys using dense layer
    print("Source shape")
    print(source_embed2.shape)
    source_linearity = Dense(units=embedding_size,
                             name='att_linearity_K_source')
    source_keys = TimeDistributed(source_linearity, name='att_K_source')(source_embed2)
    print("Keys shape")
    print(source_keys.shape)
    target_linearity = Dense(units=embedding_size,
                             name='att_linearity_K_target')
    target_keys = TimeDistributed(target_linearity, name='att_K_target')(target_embed2)

    # create query elements doing average and then multiplication
    source_avg = GlobalAveragePooling1D(name="avg_query_source")(source_embed2)
    print("source avg")
    print(source_avg.shape)
    target_avg = GlobalAveragePooling1D(name="avg_query_target")(target_embed2)
    source_query = source_linearity(target_avg)
    target_query = source_linearity(source_avg)
    print("target query")
    print(target_query.shape)

    time_shape = (source_keys.shape)[1]
    space_shape = (source_keys.shape)[2]

    # repeat the query and sum
    source_query = RepeatVector(time_shape, name='repeat_query_source')(source_query)
    target_query = RepeatVector(time_shape, name='repeat_query_target')(target_query)
    print("repeat target query")
    print(target_query.shape)
    source_score = Add(name='att_addition_source')([source_query, source_keys])
    target_score = Add(name='att_addition_target')([target_query, target_keys])
    print("target score (sum)")
    print(target_score.shape)

    # activation and dot product with importance vector
    target_score = Activation(activation='relu', name='att_activation_target')(target_score)
    source_score = Activation(activation='relu', name='att_activation_source')(source_score)
    print("target score (activation)")
    print(target_score.shape)
    imp_v_target = Dense(units=1,
                         kernel_initializer='he_normal',
                         name='importance_vector_target')
    target_score = TimeDistributed(imp_v_target, name='att_scores_target')(target_score)
    imp_v_source = Dense(units=1,
                         kernel_initializer='he_normal',
                         name='importance_vector_source')
    source_score = TimeDistributed(imp_v_source, name='att_scores_source')(source_score)
    print("target score (dot product)")
    print(target_score.shape)

    # application of mask: padding layer are associated to very negative scores to improve softmax
    source_score = Flatten(name='att_scores_flat_source')(source_score)
    target_score = Flatten(name='att_scores_flat_target')(target_score)
    print("target score (flat)")
    print(target_score.shape)
    maskLayer = Lambda(create_padding_mask_fn(), name='masking')
    negativeLayer = Lambda(create_mutiply_negative_elements_fn(), name='negative_mul')
    mask_source = maskLayer(sourceprop_il)
    mask_target = maskLayer(targetprop_il)
    print("target mask (01)")
    print(mask_target.shape)
    neg_source = negativeLayer(mask_source)
    neg_target = negativeLayer(mask_target)
    print("target mask (negative)")
    print(neg_target.shape)
    source_score = Add(name='att_masked_addition_source')([neg_source, source_score])
    target_score = Add(name='att_masked_addition_target')([neg_target, target_score])
    print("target score (masked)")
    print(neg_target.shape)

    # softmax application
    source_weight = Activation(activation='softmax', name='att_weights_source')(source_score)
    target_weight = Activation(activation='softmax', name='att_weights_target')(target_score)
    print("target weights (softmax)")
    print(target_weight.shape)

    # weighted sum
    source_weight = Reshape(target_shape=(source_weight.shape[-1], 1), name='att_weights_reshape_source')(
        source_weight)
    target_weight = Reshape(target_shape=(target_weight.shape[-1], 1), name='att_weights_reshape_target')(
        target_weight)
    print("target weights (reshape)")
    print(target_weight.shape)
    source_weighted = Multiply(name='att_multiply_source')([source_weight, prev_source_l])
    target_weighted = Multiply(name='att_multiply_target')([target_weight, prev_target_l])
    print("target weighted values")
    print(target_weighted.shape)
    source_embed2 = Lambda(create_sum_fn(1), name='att_cv_source')(source_weighted)
    target_embed2 = Lambda(create_sum_fn(1), name='att_cv_target')(target_weighted)
    print("target context vector")
    print(target_embed2.shape)







    if context and distance > 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                        name='link',
                        activation='softmax',
                        )(prev_l)
    else:
        link_scores = []
        rel_scores = []
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i + 1), name='rel' + str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute = []
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_' + str(i))(link_contribute)
            link_scores.append(link_class)

        link_ol = Concatenate(name='link')(link_scores)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=(text_il, sourceprop_il, targetprop_il, dist_il, mark_il),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model


def build_net_7(bow,
                propos_length,
                outputs,
                link_as_sum,
                distance,
                text_length=200,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0,
                embedding_size=int(25),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_size=50,
                final_size=int(20),
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                single_LSTM=False,
                pooling=0,
                text_pooling=0,
                pooling_type='avg',
                same_DE_layers=False,
                context=True,
                temporalBN=False,):
    """
    Creates a neural network that takes as input two components (propositions) and ouputs the class of the two
    components, whether a relation between the two exists, and the class of that relation.



    :param bow: If it is different from None, it is the matrix with the pre-trained embeddings used by the Embedding
                layer of keras, the input is supposed in BoW form.
                If it is None, the input is supposed to already contain pre-trained embeddings.
    :param text_length: The temporal length of the text input
    :param propos_length: The temporal length of the proposition input
    :param regularizer_weight: Regularization weight
    :param dropout_embedder: Dropout used in the embedder
    :param dropout_resnet: Dropout used in the residual network
    :param dropout_final: Dropout used in the final classifiers
    :param embedding_size: Size of the spatial reduced embeddings
    :param embedder_layers: Number of layers in the initial embedder (int)
    :param resnet_layers: Number of layers in the final residual network. Tuple where the first value indicates the
                          number of blocks and the second the number of layers per block
    :param res_size: Number of neurons in the residual blocks
    :param final_size: Number of neurons of the final layer
    :param outputs: Tuple, the classes of the four classifiers: link, relation, source, target
    :param link_as_sum: if None, the link classifier will be built as usual. If it is an array of arrays: the outputs
                        of the relation classifier will be summed together according to the values in the arrays.
                        Example: if the link classification is binary, and its contributions from relation
                        classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                        [[0, 2], [1, 3, 4]]
    :param bn_embed: Whether the batch normalization should be used in the embedding block
    :param bn_res: Whether the batch normalization should be used in the residual blocks
    :param bn_final: Whether the batch normalization should be used in the final layer
    :param single_LSTM: Whether the same LSTM should be used both for processing the target and the source
    :param pooling:
    :param text_pooling:
    :param pooling_type: 'avg' or 'max' pooling
    :param same_DE_layers: Whether the deep embedder layers should be shared between source and target
    :param context: If the context (the original text) should be used as input
    :param distance: The maximum distance that is taken into account
    :param temporalBN: Whether temporal batch-norm is applied
    :return:
    """

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    if distance > 0:
        dist_il = Input(shape=(int(distance*2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])
    layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                                   layers_size=embedding_size, temporalBN=temporalBN)
    if same_DE_layers:
        make_embedder = make_embedder_with_all_layers
    else:
        make_embedder = make_embedder_with_layers
        layers = layers[0]

    if embedder_layers > 0:
        prev_text_l = make_embedder(prev_text_l, 'text', dropout=dropout_embedder, layers=layers,
                                                 bn=bn_embed, temporalBN=temporalBN)

        prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                                  layers=layers, bn=bn_embed, temporalBN=temporalBN)
        prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                                  layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_text_l = bn_layer_t(prev_text_l)
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_text_l = drop_layer(prev_text_l)
        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_text_l = BatchNormalization(axis=-2)(prev_text_l)
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_text_l = BatchNormalization()(prev_text_l)
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_text_l = Dropout(dropout_embedder)(prev_text_l)
        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    relu_embedder = Dense(units=embedding_size,
                              activation='relu',
                              kernel_initializer='he_normal',
                              kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                              bias_regularizer=keras.regularizers.l2(regularizer_weight),
                              name='relu_embedder')

    prev_text_l = TimeDistributed(relu_embedder, name='TD_text_embedder')(prev_text_l)
    TD_prop = TimeDistributed(relu_embedder, name='TD_prop_embedder')
    prev_source_l = TD_prop(prev_source_l)
    prev_target_l = TD_prop(prev_target_l)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    if pooling > 0:
        if pooling_type == 'max':
            pooling_class = MaxPool1D
        else:
            pooling_class = AveragePooling1D
        prop_pooling = pooling_class(pool_size=pooling, name='prop_pooling')
        prev_source_l = prop_pooling(prev_source_l)
        prev_target_l = prop_pooling(prev_target_l)

        if context:
            # if text_pooling is negative, the same pooling of the propositions is used
            if not text_pooling > 0:
                text_pooling = pooling
            prev_text_l = pooling_class(pool_size=text_pooling, name='text_pooling')(prev_text_l)

    if bn_embed:
        if temporalBN:
            prev_text_l = BatchNormalization(name="TBN_LSTM_text", axis=-2)(prev_text_l)
        else:
            prev_text_l = BatchNormalization(name="BN_LSTM_text")(prev_text_l)

    if single_LSTM:
        if bn_embed:

            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_LSTM_prop", axis=-2)
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)
            else:
                bn_layer = BatchNormalization(name="BN_LSTM_prop")
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)

        embed2 = Bidirectional(LSTM(units=embedding_size,
                                    dropout=dropout_embedder,
                                    recurrent_dropout=dropout_embedder,
                                    kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                    recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                    bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                    return_sequences=False,
                                    unroll=False, # not possible to unroll if the time shape is not specified
                                    name='prop_LSTM',
                                    ),
                               merge_mode='mul',
                               name='biLSTM'
                               )

        source_embed2 = embed2(prev_source_l)
        target_embed2 = embed2(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=False,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='text_LSTM'),
                                    merge_mode='mul',
                                    name='text_biLSTM'
                                    )(prev_text_l)
    else:
        if bn_embed:
            if temporalBN:
                prev_source_l = BatchNormalization(name="TBN_LSTM_source", axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(name="TBN_LSTM_target", axis=-2)(prev_target_l)
            else:
                prev_source_l = BatchNormalization(name="BN_LSTM_source")(prev_source_l)
                prev_target_l = BatchNormalization(name="BN_LSTM_target")(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=False,
                                       unroll=False, # not possible to unroll if the time shape is not specified
                                       name='text_LSTM'),
                                  merge_mode='mul',
                                  name='text_biLSTM'
                                  )(prev_text_l)

        source_embed2 = Bidirectional(LSTM(units=embedding_size,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=False,
                                       unroll=False,  # not possible to unroll if the time shape is not specified
                                       name='source_LSTM'),
                                      merge_mode='mul',
                                      name='source_biLSTM'
                                      )(prev_source_l)

        target_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=False,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='target_LSTM'),
                                    merge_mode='mul',
                                  name='target_biLSTM'
                                    )(prev_target_l)

    if context and distance > 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                       name='link',
                       activation='softmax',
                       )(prev_l)
    else:
        link_scores=[]
        rel_scores=[]
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i+1), name='rel'+str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute=[]
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_'+str(i))(link_contribute)
            link_scores.append(link_class)

        link_ol = Concatenate(name='link')(link_scores)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)
    
    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=(text_il, sourceprop_il, targetprop_il, dist_il, mark_il),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model


def build_net_7_nc(bow,
                   propos_length,
                   outputs,
                   link_as_sum,
                   distance,
                   regularizer_weight=0.0001,
                   dropout_embedder=0.1,
                   dropout_resnet=0.1,
                   dropout_final=0,
                   embedding_size=int(50),
                   embedder_layers=4,
                   resnet_layers=(1, 2),
                   res_size=5,
                   final_size=int(20),
                   bn_embed=True,
                   bn_res=True,
                   bn_final=True,
                   single_LSTM=True,
                   pooling=10,
                   text_pooling=50,
                   pooling_type='avg',
                   same_DE_layers=False,
                   temporalBN=False, ):
    """
    Creates a neural network that classifies two argumentative components and their relation.
    It takes as input two components (propositions) and their distance.
    It ouputs the classes of the two components, whether a relation from source to target does exists (link class),
    and the class of that relation.
    The two components must be represented as a bi-dimensional tensors of features, or as mono-dimensional tensors if a
    matrix to convert each mono-dimensional feature into a bidimensional one is provided (bow input of the function).
    For example if the bow matrix contains the pre-trained embeddings of each word, the input to the network can be the
    integer sequence that represent the words.
    The distance must be encoded with twice the number of features as it is specified in the parameters.
    The oputputs will be, in order, the link class, the relation class, the source class, and the target class.

    :param bow: If it is different from None, it is the matrix with the pre-trained embeddings used by the Embedding
                layer of keras, the input is supposed to be a list of integer which represent the words.
                If it is None, the input is supposed to already contain pre-trained embeddings.
    :param propos_length: The temporal length of the proposition input
    :param outputs: Tuple, the classes of the four classifiers: link, relation, source, target
    :param link_as_sum: if None, the link classifier will be built as a Dense layer.
                        If it is an array of arrays: the outputs
                        of the relation classifier will be summed together according to the values in the arrays.
                        Example: if the link classification is binary, and its contributions from relation
                        classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                        [[0, 2], [1, 3, 4]]
    :param distance: The maximum distance that is taken into account, the input is expected to be twice that size.
    :param regularizer_weight: Regularization weight
    :param dropout_embedder: Dropout used in the embedder
    :param dropout_resnet: Dropout used in the residual network
    :param dropout_final: Dropout used in the final classifiers
    :param embedding_size: Size of the spatial reduced embeddings
    :param embedder_layers: Number of layers in the initial embedder (int)
    :param resnet_layers: Number of layers in the final residual network. Tuple where the first value indicates the
                          number of blocks and the second the number of layers per block
    :param res_size: Number of neurons in the residual blocks
    :param final_size: Number of neurons of the final layer
    :param bn_embed: Whether the batch normalization should be used in the embedding block
    :param bn_res: Whether the batch normalization should be used in the residual blocks
    :param bn_final: Whether the batch normalization should be used in the final layer
    :param single_LSTM: Whether the same LSTM should be used both for processing the target and the source
    :param pooling:
    :param text_pooling:
    :param pooling_type: 'avg' or 'max' pooling
    :param same_DE_layers: Whether the deep embedder layers should be shared between source and target
    :param temporalBN: Whether temporal batch-norm is applied
    :return:
    """

    if bow is not None:
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    if distance > 0:
        dist_il = Input(shape=(int(distance * 2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_source_l)[2])
    layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                  layers_size=embedding_size, temporalBN=temporalBN)
    if same_DE_layers:
        make_embedder = make_embedder_with_all_layers
    else:
        make_embedder = make_embedder_with_layers
        layers = layers[0]

    if embedder_layers > 0:

        prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)
        prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                      layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    relu_embedder = Dense(units=embedding_size,
                          activation='relu',
                          kernel_initializer='he_normal',
                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                          name='relu_embedder')

    TD_prop = TimeDistributed(relu_embedder, name='TD_prop_embedder')
    prev_source_l = TD_prop(prev_source_l)
    prev_target_l = TD_prop(prev_target_l)


    if pooling > 0:
        if pooling_type == 'max':
            pooling_class = MaxPool1D
        else:
            pooling_class = AveragePooling1D
        prop_pooling = pooling_class(pool_size=pooling, name='prop_pooling')
        prev_source_l = prop_pooling(prev_source_l)
        prev_target_l = prop_pooling(prev_target_l)

    if single_LSTM:
        if bn_embed:

            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_LSTM_prop", axis=-2)
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)
            else:
                bn_layer = BatchNormalization(name="BN_LSTM_prop")
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)

        embed2 = Bidirectional(LSTM(units=embedding_size,
                                    dropout=dropout_embedder,
                                    recurrent_dropout=dropout_embedder,
                                    kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                    recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                    bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                    return_sequences=False,
                                    unroll=False,  # not possible to unroll if the time shape is not specified
                                    name='prop_LSTM',
                                    ),
                               merge_mode='mul',
                               name='biLSTM'
                               )

        source_embed2 = embed2(prev_source_l)
        target_embed2 = embed2(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_source_l = BatchNormalization(name="TBN_LSTM_source", axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(name="TBN_LSTM_target", axis=-2)(prev_target_l)
            else:
                prev_source_l = BatchNormalization(name="BN_LSTM_source")(prev_source_l)
                prev_target_l = BatchNormalization(name="BN_LSTM_target")(prev_target_l)


        source_embed2 = Bidirectional(LSTM(units=embedding_size,
                                           dropout=dropout_embedder,
                                           recurrent_dropout=dropout_embedder,
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           return_sequences=False,
                                           unroll=False,  # not possible to unroll if the time shape is not specified
                                           name='source_LSTM'),
                                      merge_mode='mul',
                                      name='source_biLSTM'
                                      )(prev_source_l)

        target_embed2 = Bidirectional(LSTM(units=embedding_size,
                                           dropout=dropout_embedder,
                                           recurrent_dropout=dropout_embedder,
                                           kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                           recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                           bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                           return_sequences=False,
                                           unroll=False,  # not possible to unroll if the time shape is not specified
                                           name='target_LSTM'),
                                      merge_mode='mul',
                                      name='target_biLSTM'
                                      )(prev_target_l)

    if distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                        name='link',
                        activation='softmax',
                        )(prev_l)
    else:
        link_scores = []
        rel_scores = []
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i + 1), name='rel' + str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute = []
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_' + str(i))(link_contribute)
            link_scores.append(link_class)

        link_ol = Concatenate(name='link')(link_scores)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=(sourceprop_il, targetprop_il, dist_il),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model







def build_not_res_net_7(bow=None,
                        text_length=200, propos_length=75,
                        regularizer_weight=0.001,
                        dropout_embedder=0.1,
                        dropout_resnet=0.1,
                        dropout_final=0,
                        embedding_size=int(25),
                        embedder_layers=2,
                        resnet_layers=(2, 2),
                        res_size=50,
                        final_size=int(20),
                        outputs=(2, 5, 5, 5),
                        bn_embed=True,
                        bn_res=True,
                        bn_final=True,
                        single_LSTM=False,
                        pooling=0,
                        text_pooling=0,
                        pooling_type='avg',
                        same_DE_layers=False,
                        context=True,
                        distance=5,
                        temporalBN=False,):

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    if distance > 0:
        dist_il = Input(shape=(int(distance*2),), name="dist_input_L")
    else:
        dist_il = Input(shape=(2,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])

    if embedder_layers > 0:
        layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                                       layers_size=embedding_size, temporalBN=temporalBN)
        if same_DE_layers:
            make_embedder = make_embedder_with_all_layers
        else:
            make_embedder = make_embedder_with_layers
            layers = layers[0]

        if embedder_layers > 0:
            prev_text_l = make_embedder(prev_text_l, 'text', dropout=dropout_embedder, layers=layers,
                                                     bn=bn_embed, temporalBN=temporalBN, residual=False)

            prev_source_l = make_embedder(prev_source_l, 'source', dropout=dropout_embedder,
                                                      layers=layers, bn=bn_embed, temporalBN=temporalBN, residual=False)
            prev_target_l = make_embedder(prev_target_l, 'target', dropout=dropout_embedder,
                                                  layers=layers, bn=bn_embed, temporalBN=temporalBN, residual=False)

    if same_DE_layers:
        if bn_embed:
            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
                bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
            else:
                bn_layer = BatchNormalization(name="BN_DENSE_generic")
                bn_layer_t = bn_layer
            prev_text_l = bn_layer_t(prev_text_l)
            prev_source_l = bn_layer(prev_source_l)
            prev_target_l = bn_layer(prev_target_l)

        drop_layer = Dropout(dropout_embedder)

        prev_text_l = drop_layer(prev_text_l)
        prev_source_l = drop_layer(prev_source_l)
        prev_target_l = drop_layer(prev_target_l)

    else:
        if bn_embed:
            if temporalBN:
                prev_text_l = BatchNormalization(axis=-2)(prev_text_l)
                prev_source_l = BatchNormalization(axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(axis=-2)(prev_target_l)
            else:
                prev_text_l = BatchNormalization()(prev_text_l)
                prev_source_l = BatchNormalization()(prev_source_l)
                prev_target_l = BatchNormalization()(prev_target_l)

        prev_text_l = Dropout(dropout_embedder)(prev_text_l)
        prev_source_l = Dropout(dropout_embedder)(prev_source_l)
        prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    relu_embedder = Dense(units=embedding_size,
                              activation='relu',
                              kernel_initializer='he_normal',
                              kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                              bias_regularizer=keras.regularizers.l2(regularizer_weight),
                              name='relu_embedder')

    prev_text_l = TimeDistributed(relu_embedder, name='TD_text_embedder')(prev_text_l)
    TD_prop = TimeDistributed(relu_embedder, name='TD_prop_embedder')
    prev_source_l = TD_prop(prev_source_l)
    prev_target_l = TD_prop(prev_target_l)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    if pooling > 0:
        if not text_pooling > 0:
            text_pooling = pooling
        if pooling_type == 'max':
            pooling_class = MaxPool1D
        else:
            pooling_class = AveragePooling1D
            prev_text_l = pooling_class(pool_size=text_pooling, name='text_pooling')(prev_text_l)
        prop_pooling = pooling_class(pool_size=pooling, name='prop_pooling')
        prev_source_l = prop_pooling(prev_source_l)
        prev_target_l = prop_pooling(prev_target_l)

    if bn_embed:
        if temporalBN:
            prev_text_l = BatchNormalization(name="TBN_LSTM_text", axis=-2)(prev_text_l)
        else:
            prev_text_l = BatchNormalization(name="BN_LSTM_text")(prev_text_l)

    if single_LSTM:
        if bn_embed:

            if temporalBN:
                bn_layer = BatchNormalization(name="TBN_LSTM_prop", axis=-2)
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)
            else:
                bn_layer = BatchNormalization(name="BN_LSTM_prop")
                prev_source_l = bn_layer(prev_source_l)
                prev_target_l = bn_layer(prev_target_l)

        embed2 = Bidirectional(LSTM(units=embedding_size,
                                    dropout=dropout_embedder,
                                    recurrent_dropout=dropout_embedder,
                                    kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                    recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                    bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                    return_sequences=False,
                                    unroll=False, # not possible to unroll if the time shape is not specified
                                    name='prop_LSTM',
                                    ),
                               merge_mode='mul',
                               name='biLSTM'
                               )

        source_embed2 = embed2(prev_source_l)
        target_embed2 = embed2(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=False,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='text_LSTM'),
                                    merge_mode='mul',
                                    name='text_biLSTM'
                                    )(prev_text_l)
    else:
        if bn_embed:
            if temporalBN:
                prev_source_l = BatchNormalization(name="TBN_LSTM_source", axis=-2)(prev_source_l)
                prev_target_l = BatchNormalization(name="TBN_LSTM_target", axis=-2)(prev_target_l)
            else:
                prev_source_l = BatchNormalization(name="BN_LSTM_source")(prev_source_l)
                prev_target_l = BatchNormalization(name="BN_LSTM_target")(prev_target_l)

        text_embed2 = Bidirectional(LSTM(units=embedding_size,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=False,
                                       unroll=False, # not possible to unroll if the time shape is not specified
                                       name='text_LSTM'),
                                  merge_mode='mul',
                                  name='text_biLSTM'
                                  )(prev_text_l)

        source_embed2 = Bidirectional(LSTM(units=embedding_size,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=False,
                                       unroll=False,  # not possible to unroll if the time shape is not specified
                                       name='source_LSTM'),
                                      merge_mode='mul',
                                      name='source_biLSTM'
                                      )(prev_source_l)

        target_embed2 = Bidirectional(LSTM(units=embedding_size,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=False,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='target_LSTM'),
                                    merge_mode='mul',
                                  name='target_biLSTM'
                                    )(prev_target_l)

    if context and distance > 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance > 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_ffnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=(text_il, sourceprop_il, targetprop_il, dist_il, mark_il),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model




def build_net_6(bow=None,
                text_length=200, propos_length=75,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0,
                embedding_size=int(25),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_size=50,
                final_size=int(20),
                outputs=(2, 5, 5, 5),
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                pooling_type='avg'):

    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il

    mark_il = Input(shape=(text_length, 2), name="mark_input_L")
    dist_il = Input(shape=(10,), name="dist_input_L")

    shape = int(np.shape(prev_text_l)[2])
    dense_layers = make_embedder_layers(regularizer_weight, shape=shape, layers=embedder_layers,
                                        layers_size=embedding_size)

    if embedder_layers > 0:
        prev_text_l = make_embedder_with_layers(prev_text_l, 'text',
                                             dropout=dropout_embedder, layers=dense_layers, bn=bn_embed)
        prev_source_l = make_embedder_with_layers(prev_source_l, 'source',
                                                   dropout=dropout_embedder, layers=dense_layers, bn=bn_embed)
        prev_target_l = make_embedder_with_layers(prev_target_l, 'target',
                                                   dropout=dropout_embedder, layers=dense_layers, bn=bn_embed)

    prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    if bn_embed:
        prev_text_l = BatchNormalization()(prev_text_l)
        prev_source_l = BatchNormalization()(prev_source_l)
        prev_target_l = BatchNormalization()(prev_target_l)

    prev_text_l = Dropout(dropout_embedder)(prev_text_l)
    prev_source_l = Dropout(dropout_embedder)(prev_source_l)
    prev_target_l = Dropout(dropout_embedder)(prev_target_l)

    prev_text_l = TimeDistributed(Dense(units=embedding_size,
                                          activation='relu',
                                          kernel_initializer='he_normal',
                                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                          name='relu_text_embedder'),
                                  name='TD_text_embedder')(prev_text_l)

    prev_source_l = TimeDistributed(Dense(units=embedding_size,
                                          activation='relu',
                                          kernel_initializer='he_normal',
                                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                          name='relu_source_embedder'),
                                        name='TD_source_embedder')(prev_source_l)

    prev_target_l = TimeDistributed(Dense(units=embedding_size,
                                          activation='relu',
                                          kernel_initializer='he_normal',
                                          kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                          bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                          name='relu_target_embedder'),
                                        name='TD_target_embedder')(prev_target_l)

    if pooling_type == 'max':
        pooling_class = GlobalMaxPooling1D
    else:
        pooling_class = GlobalAveragePooling1D
    prop_pooling = pooling_class(name='pooling')
    prev_source_l = prop_pooling(prev_source_l)
    prev_target_l = prop_pooling(prev_target_l)
    prev_text_l = prop_pooling(prev_text_l)

    prev_l = Concatenate(name='embed_merge')([prev_text_l, prev_source_l, prev_target_l, dist_il])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation='softmax',
                   )(prev_l)

    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation='softmax',
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation='softmax',
                      )(prev_l)

    full_model = keras.Model(inputs=(text_il, sourceprop_il, targetprop_il, dist_il, mark_il),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model




def build_net_8(bow=None,
                text_length=200,
                propos_length=75,
                regularizer_weight=0.001,
                dropout_embedder=0.1,
                dropout_resnet=0.1,
                dropout_final=0.1,
                embedding_scale=int(10),
                embedder_layers=2,
                resnet_layers=(2, 2),
                res_scale=int(15),
                final_scale=int(10),
                outputs=(2, 5, 5, 5),
                link_as_sum=None,
                bn_embed=True,
                bn_res=True,
                bn_final=True,
                context=True,
                distance=5,
                temporalBN=False,
                merge="a_self",
                distribution="softmax",
                classification="softmax",
                space_scale=2,
                use_lstm=True):
    """
    Creates a network that (1) has a residual block to refine embeddings, (2) uses attention on the sequences,
    (3) uses a residual network to elaborate the vectors, (4) performs the classifications
    :param bow: a matrix used to convert the BoW model into embeddings, None if the input are already embeddings
    :param text_length: the maximum length of a complete document
    :param propos_length: the maximum length of an argumentative component
    :param regularizer_weight: regularization term to use in the architecture
    :param dropout_embedder: dropout used in (1)
    :param dropout_resnet: dropout used in (3)
    :param dropout_final: dropout used the last layer
    :param embedding_scale: how many times the embeddings size is reduced in the residual blocks of the embedder (1)
    :param embedder_layers: how many layers are inside (1)
    :param resnet_layers: couple of values: the first one indicates the number of residual blocks, the other the number
                          of layers inside each block
    :param res_scale: how many times the embeddings size is reduced in the residual blocks
    :param final_scale: how many times the embeddings size is reduced in the last block of the network
    :param outputs: the number of classes for link prediction, relation classification, source classification,
                    target classification
    :param link_as_sum: if None, the link classifier will be built as usual. If it is an array of arrays: the outputs
                    of the relation classifier will be summed together according to the values in the arrays.
                    Example: if the link classification is binary, and its contributions from relation
                    classification are classes 0 and 2 for positive and 1, 3, 4 for negative, it will be
                    [[0, 2], [1, 3, 4]]
    :param bn_embed: if batch normalization is applied in (1)
    :param bn_res: if batch normalization is applied in (3)
    :param bn_final: if batch normalization is applied in the end
    :param context: make use of the full text or not
    :param distance: if it's greater than 0 indicates the maximum number of distance (both for positive and negative),
                     if it's lower or equal to 0 it's not used. Using 1, the feature will represent the cocept of
                     previous and following
    :param temporalBN: if the batch normalization is computed along the temporal axis
    :param merge: "a_self" to use self-attention, "a_self_shared" to use self-attention with a shared model for all
                  the 3 inputs, "a_coars" to use parallel coarse co-attention (problem to solve: the average is
                  computed also with the padding"
    :param distribution: distribution function for the attention model, "softmax" or "sparsemax"
    :param classification: "softmax" or "sparsemax"
    :param space_scale: if each temporal data has to be mapped in a smaller space through a dense layer,
                        the scale of the reduction; -1 to avoid this feature
    :param lstm: whether a biLSTM has to be applied before attention; the two LSTMs output feature of the same dimension
                 of the input /2 and *2
    :return:
    """


    if distribution == "sparsemax":
        distribution = sparsemax
    if classification == "sparsemax":
        classification = sparsemax

    # input: BOW model, this piece of code loads the pre-trained embeddings
    if bow is not None:
        text_il = Input(shape=(text_length,), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length,), name="source_input_L")
        targetprop_il = Input(shape=(propos_length,), name="target_input_L")

        prev_text_l = Embedding(bow.shape[0],
                                bow.shape[1],
                                weights=[bow],
                                input_length=text_length,
                                trainable=False,
                                name="text_embed")(text_il)

        prev_source_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="source_embed")(sourceprop_il)

        prev_target_l = Embedding(bow.shape[0],
                                  bow.shape[1],
                                  weights=[bow],
                                  input_length=propos_length,
                                  trainable=False,
                                  name="target_embed")(targetprop_il)
    else:
        text_il = Input(shape=(text_length, DIM), name="text_input_L")
        sourceprop_il = Input(shape=(propos_length, DIM), name="source_input_L")
        targetprop_il = Input(shape=(propos_length, DIM), name="target_input_L")
        prev_text_l = text_il
        prev_source_l = sourceprop_il
        prev_target_l = targetprop_il


    mark_il = Input(shape=(text_length, 2), name="mark_input_L")

    # distance feature
    if distance > 0:
        dist_il = Input(shape=(int(distance*2),), name="dist_input_L")
    # no feature
    else:
        dist_il = Input(shape=(0,), name="dist_input_L")

    source_padding = Lambda(create_count_nonpadding_fn(axis=-2, pad_dims=(DIM,)), name="source_nonpad_L")(prev_source_l)
    target_padding = Lambda(create_count_nonpadding_fn(axis=-2, pad_dims=(DIM,)), name="target_nonpad_L")(prev_target_l)
    text_padding = Lambda(create_count_nonpadding_fn(axis=-2, pad_dims=(DIM,)), name="text_nonpad_L")(prev_text_l)

    original_space_shape = int(np.shape(prev_source_l)[2])

    # TODO: find an alternative to masking since it can't be applied
    # mask = Masking(mask_value=0, name="masking_l")
    # prev_text_l = mask(prev_text_l)
    # prev_source_l = mask(prev_source_l)
    # prev_target_l = mask(prev_target_l)

    # DEEP EMBEDDER
    if embedder_layers > 0:
        embedding_size = int(original_space_shape/embedding_scale)
        layers = make_embedder_layers(regularizer_weight, shape=original_space_shape, layers=embedder_layers,
                                      layers_size=embedding_size, temporalBN=temporalBN, dropout=dropout_embedder)

        make_embedder = make_embedder_with_all_layers

        prev_text_l = make_embedder(prev_text_l, 'text', layers=layers,
                                                 bn=bn_embed, temporalBN=temporalBN)

        prev_source_l = make_embedder(prev_source_l, 'source',
                                                  layers=layers, bn=bn_embed, temporalBN=temporalBN)

        prev_target_l = make_embedder(prev_target_l, 'target',
                                                  layers=layers, bn=bn_embed, temporalBN=temporalBN)

    if bn_embed:
        if temporalBN:
            bn_layer = BatchNormalization(name="TBN_DENSE_prop", axis=-2)
            bn_layer_t = BatchNormalization(name="TBN_DENSE_text", axis=-2)
        else:
            bn_layer = BatchNormalization(name="BN_DENSE_generic")
            bn_layer_t = bn_layer
        prev_text_l = bn_layer_t(prev_text_l)
        prev_source_l = bn_layer(prev_source_l)
        prev_target_l = bn_layer(prev_target_l)

    drop_layer = Dropout(dropout_embedder)

    prev_text_l = drop_layer(prev_text_l)
    prev_source_l = drop_layer(prev_source_l)
    prev_target_l = drop_layer(prev_target_l)

    # prev_text_l = Concatenate(name="mark_concatenation")([prev_text_l, mark_il])

    # DIMENSIONALITY REDUCTION
    space_shape = int(original_space_shape / space_scale)
    if space_scale > 0:
        relu_embedder = Dense(units=int(space_shape),
                              activation='relu',
                              kernel_initializer='he_normal',
                              kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                              bias_regularizer=keras.regularizers.l2(regularizer_weight),
                              name='relu_reduction')

        prev_text_l = TimeDistributed(relu_embedder, name='TD_text_reduction')(prev_text_l)
        TD_prop = TimeDistributed(relu_embedder, name='TD_prop_reduction')
        prev_source_l = TD_prop(prev_source_l)
        prev_target_l = TD_prop(prev_target_l)

    # biLSTM
    if use_lstm:
        shape_lstm = int(int(np.shape(prev_source_l)[2])/2)
        prev_text_l = Bidirectional(LSTM(units=shape_lstm,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=True,
                                       unroll=False, # not possible to unroll if the time shape is not specified
                                       name='text_LSTM'),
                                  merge_mode='concat',
                                  name='text_biLSTM'
                                  )(prev_text_l)

        prev_source_l = Bidirectional(LSTM(units=shape_lstm,
                                       dropout=dropout_embedder,
                                       recurrent_dropout=dropout_embedder,
                                       kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                       recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                       bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                       return_sequences=True,
                                       unroll=False,  # not possible to unroll if the time shape is not specified
                                       name='source_LSTM'),
                                      merge_mode='concat',
                                      name='source_biLSTM'
                                      )(prev_source_l)

        prev_target_l = Bidirectional(LSTM(units=shape_lstm,
                                         dropout=dropout_embedder,
                                         recurrent_dropout=dropout_embedder,
                                         kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                                         recurrent_regularizer=keras.regularizers.l2(regularizer_weight),
                                         bias_regularizer=keras.regularizers.l2(regularizer_weight),
                                         return_sequences=True,
                                         unroll=False,  # not possible to unroll if the time shape is not specified
                                         name='target_LSTM'),
                                    merge_mode='concat',
                                  name='target_biLSTM'
                                    )(prev_target_l)

    # ATTENTION
    # simple self attention
    if "a_self" in merge:
        v_prev_text_l = prev_text_l
        v_prev_source_l = prev_source_l
        v_prev_target_l = prev_target_l

        # the importance model is shared by all the 3 inputs
        if merge == "a_self_shared":

            relu_attention = Dense(units=space_shape,
                                    activation='relu',
                                    kernel_initializer='he_normal',
                                    name='attention_mlp')

            importance_attention = Dense(units=1,
                                    activation=None,
                                    name='attention_importance')

            text_relu_attention = relu_attention
            source_relu_attention = relu_attention
            target_relu_attention = relu_attention
            text_importance_attention = importance_attention
            source_importance_attention = importance_attention
            target_importance_attention = importance_attention

        # each input develops a different importance model
        else:

            text_relu_attention = Dense(units=space_shape,
                                   activation='relu',
                                   kernel_initializer='he_normal',
                                   name='text_attention_mlp')

            text_importance_attention = Dense(units=1,
                                         activation=None,
                                         name='text_attention_importance')

            source_relu_attention = Dense(units=space_shape,
                                   activation='relu',
                                   kernel_initializer='he_normal',
                                   name='source_attention_mlp')

            source_importance_attention = Dense(units=1,
                                         activation=None,
                                         name='source_attention_importance')

            target_relu_attention = Dense(units=space_shape,
                                   activation='relu',
                                   kernel_initializer='he_normal',
                                   name='target_attention_mlp')

            target_importance_attention = Dense(units=1,
                                         activation=None,
                                         name='target_attention_importance')

        prev_text_l = TimeDistributed(text_relu_attention, name='TD_text_amlp')(prev_text_l)
        prev_text_l = TimeDistributed(text_importance_attention, name='TD_text_aimportance')(prev_text_l)
        TD_source = TimeDistributed(source_relu_attention, name='TD_source_amlp')
        TD_target = TimeDistributed(target_relu_attention, name='TD_target_amlp')
        prev_source_l = TD_source(prev_source_l)
        prev_target_l = TD_target(prev_target_l)
        TD_source = TimeDistributed(source_importance_attention, name='TD_source_aimportance')
        TD_target = TimeDistributed(target_importance_attention, name='TD_target_aimportance')
        prev_source_l = TD_source(prev_source_l)
        prev_target_l = TD_target(prev_target_l)

        prev_text_l = Flatten()(prev_text_l)
        prev_source_l = Flatten()(prev_source_l)
        prev_target_l = Flatten()(prev_target_l)

        text_a = Activation(activation=distribution,
                            name='text_attention')(prev_text_l)

        source_a = Activation(activation=distribution,
                            name='source_attention')(prev_source_l)

        target_a = Activation(activation=distribution,
                            name='target_attention')(prev_target_l)

        prev_text_l = RepeatVector(space_shape, name='text_repetition')(text_a)
        prev_text_l = Permute(dims=(2, 1), name='text_swap')(prev_text_l)
        prev_source_l = RepeatVector(space_shape, name='source_repetition')(source_a)
        prev_source_l = Permute(dims=(2, 1), name='source_swap')(prev_source_l)
        prev_target_l = RepeatVector(space_shape, name='target_repetition')(target_a)
        prev_target_l = Permute(dims=(2, 1), name='target_swap')(prev_target_l)

        prev_text_l = Multiply(name='text_amul')([v_prev_text_l, prev_text_l])
        prev_source_l = Multiply(name='source_amul')([v_prev_source_l, prev_source_l])
        prev_target_l = Multiply(name='target_amul')([v_prev_target_l, prev_target_l])

        text_embed2 = Lambda(create_sum_fn(1), name='text_asum')(prev_text_l)
        source_embed2 = Lambda(create_sum_fn(1), name='source_asum')(prev_source_l)
        target_embed2 = Lambda(create_sum_fn(1), name='target_asum')(prev_target_l)
    # parallel coarse grained co-attention
    # TODO: FIND A WAY TO DEAL WITH THIS DAMN PADDING!!!
    # CAN'T USE "non-padding finder" cause of the dimensionality reduction!
    elif merge == "a_coarse":
        v_prev_text_l = prev_text_l
        v_prev_source_l = prev_source_l
        v_prev_target_l = prev_target_l

        text_sum = Lambda(create_sum_fn(1), name="text_aavg_sum")(prev_text_l)
        text_avg = Lambda(create_elementwise_division_fn(), name='text_aavg_div')([text_sum, text_padding])
        source_sum = Lambda(create_sum_fn(1), name="source_aavg_sum")(prev_source_l)
        source_avg = Lambda(create_elementwise_division_fn(), name='source_aavg_div')([source_sum, source_padding])
        target_sum = Lambda(create_sum_fn(1), name="target_aavg_sum")(prev_target_l)
        target_avg = Lambda(create_elementwise_division_fn(), name='target_aavg_div')([target_sum, target_padding])

        text_query_p = RepeatVector(propos_length, name='text_aquery_p')(text_avg)
        source_query_p = RepeatVector(propos_length, name='source_aquery_p')(source_avg)
        target_query_p = RepeatVector(propos_length, name='target_aquery_p')(target_avg)
        source_query_t = RepeatVector(text_length, name='source_aquery_t')(source_avg)
        target_query_t = RepeatVector(text_length, name='target_aquery_t')(target_avg)

        if context:
            prev_source_l = Concatenate(name='source_aconcat')([prev_source_l, text_query_p, target_query_p])
            prev_target_l = Concatenate(name='target_aconcat')([prev_target_l, text_query_p, source_query_p])
            prev_text_l = Concatenate(name='text_aconcat')([prev_text_l, target_query_t, source_query_t])
        else:
            prev_source_l = Concatenate(name='source_aconcat')([prev_source_l, target_query_p])
            prev_target_l = Concatenate(name='target_aconcat')([prev_target_l, source_query_p])

        text_relu_attention = Dense(units=space_shape,
                               activation='relu',
                               kernel_initializer='he_normal',
                               name='text_attention_mlp')

        text_importance_attention = Dense(units=1,
                                     activation=None,
                                     name='text_attention_importance')

        source_relu_attention = Dense(units=space_shape,
                               activation='relu',
                               kernel_initializer='he_normal',
                               name='source_attention_mlp')

        source_importance_attention = Dense(units=1,
                                     activation=None,
                                     name='source_attention_importance')

        target_relu_attention = Dense(units=space_shape,
                               activation='relu',
                               kernel_initializer='he_normal',
                               name='target_attention_mlp')

        target_importance_attention = Dense(units=1,
                                     activation=None,
                                     name='target_attention_importance')

        prev_text_l = TimeDistributed(text_relu_attention, name='TD_text_amlp')(prev_text_l)
        prev_text_l = TimeDistributed(text_importance_attention, name='TD_text_aimportance')(prev_text_l)
        TD_source = TimeDistributed(source_relu_attention, name='TD_source_amlp')
        TD_target = TimeDistributed(target_relu_attention, name='TD_target_amlp')
        prev_source_l = TD_source(prev_source_l)
        prev_target_l = TD_target(prev_target_l)
        TD_source = TimeDistributed(source_importance_attention, name='TD_source_aimportance')
        TD_target = TimeDistributed(target_importance_attention, name='TD_target_aimportance')
        prev_source_l = TD_source(prev_source_l)
        prev_target_l = TD_target(prev_target_l)

        prev_text_l = Flatten()(prev_text_l)
        prev_source_l = Flatten()(prev_source_l)
        prev_target_l = Flatten()(prev_target_l)

        text_a = Activation(activation=distribution,
                            name='text_attention')(prev_text_l)

        source_a = Activation(activation=distribution,
                            name='source_attention')(prev_source_l)

        target_a = Activation(activation=distribution,
                            name='target_attention')(prev_target_l)

        prev_text_l = RepeatVector(space_shape, name='text_repetition')(text_a)
        prev_text_l = Permute(dims=(2, 1), name='text_swap')(prev_text_l)
        prev_source_l = RepeatVector(space_shape, name='source_repetition')(source_a)
        prev_source_l = Permute(dims=(2, 1), name='source_swap')(prev_source_l)
        prev_target_l = RepeatVector(space_shape, name='target_repetition')(target_a)
        prev_target_l = Permute(dims=(2, 1), name='target_swap')(prev_target_l)

        prev_text_l = Multiply(name='text_amul')([v_prev_text_l, prev_text_l])
        prev_source_l = Multiply(name='source_amul')([v_prev_source_l, prev_source_l])
        prev_target_l = Multiply(name='target_amul')([v_prev_target_l, prev_target_l])

        text_embed2 = Lambda(create_sum_fn(1), name='text_asum')(prev_text_l)
        source_embed2 = Lambda(create_sum_fn(1), name='source_asum')(prev_source_l)
        target_embed2 = Lambda(create_sum_fn(1), name='target_asum')(prev_target_l)
    # TODO: Don't know which parts of this code are working and which are not. Need to check properly everything!!!
    elif merge == "a_flat":
        v_prev_text_l = prev_text_l
        v_prev_source_l = prev_source_l
        v_prev_target_l = prev_target_l

        if context:
            raise NotImplemented("Fine-grained attention has not been implemented for use with context")
        else:
            concat_l = Concatenate(name='total_aconcat', axis=-2)([prev_source_l, prev_target_l])

            flatten_l = Flatten(name='aflatten')(concat_l)

            prev_source_l = Dense(name='source_attention_mlp',
                                            units=propos_length,
                                            activation='relu',
                                            kernel_initializer='he_normal',)(flatten_l)

            prev_target_l = Dense(name='target_attention_mlp',
                                            units=propos_length,
                                            activation='relu',
                                            kernel_initializer='he_normal',)(flatten_l)

            source_a = Activation(activation=distribution,
                                  name='source_attention')(prev_source_l)

            target_a = Activation(activation=distribution,
                                  name='target_attention')(prev_target_l)

            prev_source_l = RepeatVector(space_shape, name='source_repetition')(source_a)
            prev_source_l = Permute(dims=(2, 1), name='source_swap')(prev_source_l)
            prev_target_l = RepeatVector(space_shape, name='target_repetition')(target_a)
            prev_target_l = Permute(dims=(2, 1), name='target_swap')(prev_target_l)

            prev_source_l = Multiply(name='source_amul')([v_prev_source_l, prev_source_l])
            prev_target_l = Multiply(name='target_amul')([v_prev_target_l, prev_target_l])

            source_embed2 = Lambda(create_sum_fn(1), name='source_asum')(prev_source_l)
            target_embed2 = Lambda(create_sum_fn(1), name='target_asum')(prev_target_l)

    # TODO: FINISH TO IMPLEMENT THIS
    # DECOMPOSABLE FINE GRAINED CO ATTENTION
    elif merge == "a_fine":
        v_prev_text_l = prev_text_l
        v_prev_source_l = prev_source_l
        v_prev_target_l = prev_target_l

        if context:
            raise NotImplemented("Fine-grained attention has not been implemented for use with context")
        else:
            prev_source_l = TimeDistributed(Dense(name='source_attention_mlp',
                                  units=space_shape,
                                  activation='relu',
                                  kernel_initializer='he_normal', ), name='source_attention_mlp_TD')(prev_source_l)
            prev_source_l = TimeDistributed(Dense(name='source_attention_iv',
                                                  units=1,), name='source_attention_iv_TD')(prev_source_l)

            prev_target_l = TimeDistributed(Dense(name='target_attention_mlp',
                                  units=space_shape,
                                  activation='relu',
                                  kernel_initializer='he_normal', ), name='target_attention_mlp_TD')(prev_target_l)
            prev_target_l = TimeDistributed(Dense(name='target_attention_iv',
                                                  units=1,), name='target_attention_iv_TD')(prev_target_l)

            prev_source_l = Flatten(name='source_flatten_attention')(prev_source_l)
            prev_target_l = Flatten(name='target_flatten_attention')(prev_target_l)

            prev_source_l = RepeatVector(propos_length, "source_fine_repetition")(prev_source_l)


            prev_target_l = Dense(name='target_attention_mlp',
                                  units=propos_length,
                                  activation='relu',
                                  kernel_initializer='he_normal', )(flatten_l)

            source_a = Activation(activation=distribution,
                                  name='source_attention')(prev_source_l)

            target_a = Activation(activation=distribution,
                                  name='target_attention')(prev_target_l)

            prev_source_l = RepeatVector(space_shape, name='source_repetition')(source_a)
            prev_source_l = Permute(dims=(2, 1), name='source_swap')(prev_source_l)
            prev_target_l = RepeatVector(space_shape, name='target_repetition')(target_a)
            prev_target_l = Permute(dims=(2, 1), name='target_swap')(prev_target_l)

            prev_source_l = Multiply(name='source_amul')([v_prev_source_l, prev_source_l])
            prev_target_l = Multiply(name='target_amul')([v_prev_target_l, prev_target_l])

            source_embed2 = Lambda(create_sum_fn(1), name='source_asum')(prev_source_l)
            target_embed2 = Lambda(create_sum_fn(1), name='target_asum')(prev_target_l)


    if context and distance >= 0:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2, dist_il])
    elif distance >= 0:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2, dist_il])
    elif context:
        prev_l = Concatenate(name='embed_merge')([text_embed2, source_embed2, target_embed2])
    else:
        prev_l = Concatenate(name='embed_merge')([source_embed2, target_embed2])

    if bn_res:
        prev_l = BatchNormalization(name='merge_BN')(prev_l)

    prev_l = Dropout(dropout_resnet, name='merge_Dropout')(prev_l)

    final_size = int(original_space_shape/final_scale)
    res_size = int(original_space_shape/res_scale)

    prev_l = Dense(units=final_size,
                   activation='relu',
                   kernel_initializer='he_normal',
                   kernel_regularizer=keras.regularizers.l2(regularizer_weight),
                   bias_regularizer=keras.regularizers.l2(regularizer_weight),
                   name='merge_dense'
                   )(prev_l)

    prev_l = make_resnet(prev_l, regularizer_weight, resnet_layers,
                         res_size=res_size, dropout=dropout_resnet, bn=bn_res)

    if bn_final:
        prev_l = BatchNormalization(name='final_BN')(prev_l)

    prev_l = Dropout(dropout_final, name='final_dropout')(prev_l)

    rel_ol = Dense(units=outputs[1],
                   name='relation',
                   activation=classification,
                   )(prev_l)

    if link_as_sum is None:
        link_ol = Dense(units=outputs[0],
                        name='link',
                        activation='softmax',
                        )(prev_l)
    else:
        link_scores = []
        rel_scores = []
        # creates a layer that extracts the score of a single relation classification class
        for i in range(outputs[1]):
            rel_scores.append(Lambda(create_crop_fn(1, i, i + 1), name='rel' + str(i))(rel_ol))

        # for each link class, sums the relation score contributions
        for i in range(len(link_as_sum)):
            # terms to be summed together for one of the link classes
            link_contribute = []
            for j in range(len(link_as_sum[i])):
                value = link_as_sum[i][j]
                link_contribute.append(rel_scores[value])
            link_class = Add(name='link_' + str(i))(link_contribute)
            link_scores.append(link_class)

    """
    Custom code for cdcp
    rel_0 = Lambda(create_crop_fn(1, 0, 1), name='rel0')(rel_ol)
    rel_2 = Lambda(create_crop_fn(1, 2, 3), name='rel2')(rel_ol)
    rel_1 = Lambda(create_crop_fn(1, 1, 2), name='rel1')(rel_ol)
    rel_3 = Lambda(create_crop_fn(1, 3, 4), name='rel3')(rel_ol)
    rel_4 = Lambda(create_crop_fn(1, 4, 5), name='rel4')(rel_ol)

    pos_rel = Add(name='rel_pos')([rel_0, rel_2])
    neg_rel = Add(name='rel_neg')([rel_1, rel_3, rel_4])
    link_ol = Concatenate(name='link')([pos_rel, neg_rel])
    """

    source_ol = Dense(units=outputs[2],
                      name='source',
                      activation=classification,
                      )(prev_l)

    target_ol = Dense(units=outputs[3],
                      name='target',
                      activation=classification,
                      )(prev_l)

    # TODO: implement the use of attention visualization
    full_model = keras.Model(inputs=(text_il, sourceprop_il, targetprop_il, dist_il, mark_il),
                             # outputs=(link_ol, rel_ol, source_ol, target_ol, source_a, target_a, text_a),
                             outputs=(link_ol, rel_ol, source_ol, target_ol),
                             )

    return full_model


def create_crop_fn(dimension, start, end):
    """
    From https://github.com/keras-team/keras/issues/890#issuecomment-319671916
    Crops (or slices) a Tensor on a given dimension from start to end
    example : to crop tensor x[:, :, 5:10]
    call slice(2, 5, 10) as you want to crop on the second dimension
    :param dimension: dimension of the object. The crop will be performed on the last dimension
    :param start: starting index
    :param end: ending index (excluded)
    :return:
    """
    def func(x):
        if dimension == 0:
            return x[start: end]
        if dimension == 1:
            return x[:, start: end]
        if dimension == 2:
            return x[:, :, start: end]
        if dimension == 3:
            return x[:, :, :, start: end]
        if dimension == 4:
            return x[:, :, :, :, start: end]

    func.__name__ = "crop_" + str(dimension) + "_" + str(start) + "_" + str(end)
    return func


def create_sum_fn(axis):
    """
    Sum a tensor along an axis
    :param axis: axis along which to sum
    :return:
    """
    def func(x):
        return K.sum(x, axis=axis)

    func.__name__ = "sumalong_" + str(axis)
    return func


def create_average_fn(axis):
    """
    Average a tensor along an axis
    Source: https://stackoverflow.com/questions/53303724/how-to-average-only-non-zero-entries-in-tensor
    :param axis: axis along which to average
    :return: The average computed ignoring 0 values
    """
    def func(x):
        nonzero = K.any(K.not_equal(x, 0.000), axis=axis)
        n = K.sum(K.cast(nonzero, 'float32'), axis=axis, keepdims=True)
        x_mean = K.sum(x, axis=axis-1) / n
        return x_mean

    func.__name__ = "avgalong_" + str(axis)
    return func



def create_count_nonpadding_fn(axis, pad_dims):
    """
    Given a padded tensor, counts how many elements are not padded
    :param axis: The axis along which the padding elements are to be searched
    :param pad_dims: Dimensionality of a padding element e.g. (300,)
    :return: a tensor whose elements are the number of non-padding elements that were present in that position
    """
    def func(x):
        nonzero = K.any(K.not_equal(x, K.zeros(pad_dims, dtype='float32')), axis=axis)
        n = K.sum(K.cast(nonzero, 'float32'), axis=axis, keepdims=True)
        return n

    func.__name__ = "count_nonpadding_" + str(axis) + "_" + str(pad_dims)
    return func


def create_mutiply_negative_elements_fn():
    """
    Creates multiply the tensor for a set of very negative numbers
    :return: the tensor mutiplied for  -1e9
    """
    def func(x):
        n = x * (-1e9)
        return n

    func.__name__ = "mutiply_negative_elements_"
    return func


def create_padding_mask_fn():
    """
    Given a padded tensor, provides a mask with padded elements set to 1
    :return: a tensor whose elements are 1 in correspondence of the padding elements
    """
    def func(x, axis=-1):
        zeros = tf.equal(x, 0)
        # zeros = K.equal(x, K.zeros(x.shape[axis], dtype='float32'))
        zeros = K.cast(zeros, dtype='float32')
        return zeros

    func.__name__ = "create_padding_mask_"
    return func



def create_elementwise_division_fn():
    """
    Divide a tensor by the element of the second one
    :return:
    """
    def func(x):
        res = x[0]/x[1]
        return res

    func.__name__ = "elementwise_division"
    return func


if __name__ == '__main__':

    bow = np.array([[0]*DIM]*50)

    """

    model = build_net_5(bow=None,
                        text_length=552, propos_length=153,
                        regularizer_weight=0.001,
                        dropout_embedder=0.1,
                        dropout_resnet=0.1,
                        dropout_final=0.1,
                        embedding_size=int(20),
                        embedder_layers=4,
                        resnet_layers=(1, 2),
                        res_size=5,
                        final_size=int(20),
                        bn_embed=True,
                        bn_res=True,
                        bn_final=True,
                        single_LSTM=True,
                        pooling=10,
                        text_pooling=50,
                        pooling_type='avg')

    plot_model(model, to_file='model5.png', show_shapes=True)

    model = build_net_7(bow=None,
                        text_length=552, propos_length=153,
                        regularizer_weight=0.001,
                        dropout_embedder=0.1,
                        dropout_resnet=0.1,
                        dropout_final=0.1,
                        embedding_size=int(20),
                        embedder_layers=4,
                        resnet_layers=(1, 2),
                        res_size=5,
                        final_size=int(20),
                        bn_embed=True,
                        bn_res=True,
                        bn_final=True,
                        single_LSTM=True,
                        pooling=10,
                        text_pooling=50,
                        pooling_type='avg')

    plot_model(model, to_file='model7.png', show_shapes=True)

    model = build_net_6(bow=None,
                        text_length=552, propos_length=153,
                        regularizer_weight=0.001,
                        dropout_embedder=0.1,
                        dropout_resnet=0.1,
                        dropout_final=0.1,
                        embedding_size=int(20),
                        embedder_layers=4,
                        resnet_layers=(1, 2),
                        res_size=5,
                        final_size=int(20),
                        bn_embed=True,
                        bn_res=True,
                        bn_final=True,
                        pooling_type='avg')

    plot_model(model, to_file='model6.png', show_shapes=True)
    """


    model = build_net_9(bow=bow,
                        text_length=10,
                        propos_length=10,
                        res_size=5,
                        resnet_layers=(1, 2),
                        embedding_size=50,
                        embedder_layers=4,
                        final_size=20,
                        regularizer_weight=0.0001,
                        dropout_resnet=0.1,
                        dropout_embedder=0.1,
                        dropout_final=0.1,
                        bn_embed=True,
                        bn_res=True,
                        bn_final=True,
                        single_LSTM=True,
                        pooling=10,
                        text_pooling=50,
                        temporalBN=False,
                        same_DE_layers=False,
                        context=False,
                        distance=5,
                        link_as_sum=[[0, 2], [1, 3, 4, 5, 6, 7]],
                        outputs=(2, 8, 2, 2)
                        )


    """
    model = build_net_8(bow=bow,
                        text_length=552,
                        propos_length=153,
                        regularizer_weight=0.001,
                        dropout_embedder=0.1,
                        dropout_resnet=0.1,
                        dropout_final=0.1,
                        embedding_scale=int(10),
                        embedder_layers=2,
                        resnet_layers=(2, 2),
                        res_scale=int(20),
                        final_scale=int(10),
                        outputs=(2, 5, 5, 5),
                        bn_embed=False,
                        bn_res=False,
                        bn_final=False,
                        context=False,
                        distance=5,
                        temporalBN=False,
                        merge="a_coarse",
                        classification="sparsemax",
                        distribution="sparsemax",
                        space_scale=int(6),
                        use_lstm=True)
    """

    plot_model(model, to_file='9.png', show_shapes=True)

    print("YEP")

