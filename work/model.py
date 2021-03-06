import tensorflow as tf
import numpy as np


def lstm_cell(model, rnn_size):
    if model == 'rnn':
        cell_fun = tf.contrib.rnn.BasicRNNCell
    elif model == 'gru':
        cell_fun = tf.contrib.rnn.GRUCell
    elif model == 'lstm':
        cell_fun = tf.contrib.rnn.BasicLSTMCell

    cell = cell_fun(rnn_size, state_is_tuple=True)
    cell = tf.contrib.rnn.DropoutWrapper(cell, output_keep_prob=0.5)
    return cell


def rnn_model(model, input_data, output_data, vocab_size, rnn_size=128, num_layers=2, batch_size=64,
              learning_rate=0.01, is_training=True):
    """
    construct rnn seq2seq model.
    :param model: model class
    :param input_data: input data placeholder
    :param output_data: output data placeholder
    :param vocab_size:
    :param rnn_size:
    :param num_layers:
    :param batch_size:
    :param learning_rate:
    :return:
    """
    end_points = {}

    # 这里不知道为啥， 不能直接用这种方式进行创建多层lstm
    # cell = tf.contrib.rnn.MultiRNNCell([cell] * num_layers, state_is_tuple=True)
    cell = tf.contrib.rnn.MultiRNNCell([lstm_cell(model, rnn_size) for _ in range(num_layers)], state_is_tuple=True)

# 这里测试注意批次的状态的维度
    initial_state = cell.zero_state(batch_size, tf.float32)
    # if output_data is not None:
    #     initial_state = cell.zero_state(batch_size, tf.float32)
    # else:
    #     initial_state = cell.zero_state(1, tf.float32)

# process input data
#    with tf.device("/cpu:0"):
#        embedding = tf.get_variable('embedding', initializer=tf.random_uniform(
#            [vocab_size + 1, rnn_size], -1.0, 1.0))
#        inputs = tf.nn.embedding_lookup(embedding, input_data)

    # [batch_size, ?, rnn_size] = [64, ?, 128]
    # 本项目中， 直接将输入的input_data表述为这种形式就行了
    # print(input_data)
    ## TODO 在这里加名字重用
    # with tf.variable_scope("rnn", reuse=tf.AUTO_REUSE):
    outputs, last_state = tf.nn.dynamic_rnn(cell, input_data, initial_state=initial_state)
    output = tf.reshape(outputs, [-1, rnn_size])

    weights = tf.Variable(tf.truncated_normal([rnn_size, vocab_size]))
    bias = tf.Variable(tf.zeros(shape=[vocab_size]))
    logits = tf.nn.bias_add(tf.matmul(output, weights), bias=bias)
    # [?, vocab_size+1]

    if output_data is not None:
        # output_data must be one-hot encode
        labels = tf.one_hot(tf.reshape(output_data, [-1]), depth=vocab_size)
        # should be [?, vocab_size+1]

        loss = tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits)
        # loss shape should be [?, vocab_size+1]
        total_loss = tf.reduce_mean(loss)
        train_op = tf.train.AdamOptimizer(learning_rate).minimize(total_loss)

        end_points['initial_state'] = initial_state
        end_points['output'] = output
        end_points['train_op'] = train_op
        end_points['total_loss'] = total_loss
        end_points['loss'] = loss
        end_points['last_state'] = last_state
    else:
        prediction = tf.nn.softmax(logits)

        end_points['initial_state'] = initial_state
        end_points['last_state'] = last_state
        end_points['prediction'] = prediction

    return end_points
