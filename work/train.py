import os
import numpy as np
import tensorflow as tf
from data import get_training_data
from model import rnn_model

tf.app.flags.DEFINE_integer('vocab_size', 3, 'vocab size.')
tf.app.flags.DEFINE_integer('batch_size', 50, 'batch size.')
tf.app.flags.DEFINE_integer('time_steps', 100, 'time size.')
tf.app.flags.DEFINE_integer('pulse_size', 5, 'pulse size.')
tf.app.flags.DEFINE_float('learning_rate', 0.01, 'learning rate.')
tf.app.flags.DEFINE_string('model_dir', os.path.abspath('./model'), 'model save path.')
tf.app.flags.DEFINE_string('file_path', os.path.abspath('./data/poems.txt'), 'file name of poems.')
tf.app.flags.DEFINE_string('model_prefix', 'signal', 'model save prefix.')
tf.app.flags.DEFINE_integer('epochs', 10, 'train how many epochs.')

FLAGS = tf.app.flags.FLAGS


# def get_rawdata():
#     signals = produce_signals()
#     x_batches, y_batches = generate_batch(FLAGS.batch_size * FLAGS.time_steps, signals)
#
#     length = len(x_batches) // 2
#     train_x_batches = x_batches[: length]
#     train_y_batches = y_batches[: length]
#     test_x_batches = x_batches[length:]
#     test_y_batches = y_batches[length:]
#
#     return train_x_batches, train_y_batches, test_x_batches, test_y_batches


def run_training(x_batches, y_batches):
    if not os.path.exists(FLAGS.model_dir):
        os.makedirs(FLAGS.model_dir)

    # poems_vector, word_to_int, vocabularies = process_poems(FLAGS.file_path)
    # batches_inputs, batches_outputs = generate_batch(FLAGS.batch_size, poems_vector, word_to_int)

    # signals = produce_signals()
    # x_batches, y_batches = generate_batch(FLAGS.batch_size * FLAGS.time_steps, signals)
    # x_batches = tf.reshape(x_batches_,[-1, FLAGS.time_steps, FLAGS.pulse_size])  # reshape input_data

    # input_data = tf.placeholder(tf.int32, [FLAGS.batch_size, None, FLAGS.pulse_size])
    # output_targets = tf.placeholder(tf.int32, [FLAGS.batch_size, None, 1])
    input_data = tf.placeholder(tf.float32, [None, FLAGS.time_steps, FLAGS.pulse_size])
    output_targets = tf.placeholder(tf.int32, [None, FLAGS.time_steps, 1])

    end_points = rnn_model(model='lstm', input_data=input_data, output_data=output_targets, vocab_size=FLAGS.vocab_size,
            rnn_size=128, num_layers=2, batch_size=FLAGS.batch_size, learning_rate=FLAGS.learning_rate)

    saver = tf.train.Saver(tf.global_variables())
    init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())

# add by sun
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

    with tf.Session(config=config) as sess:
        # sess = tf_debug.LocalCLIDebugWrapperSession(sess=sess)
        # sess.add_tensor_filter("has_inf_or_nan", tf_debug.has_inf_or_nan)
        sess.run(init_op)

        start_epoch = 0
        checkpoint = tf.train.latest_checkpoint(FLAGS.model_dir)
        if checkpoint:
            saver.restore(sess, checkpoint)
            print("## restore from the checkpoint {0}".format(checkpoint))
            start_epoch += int(checkpoint.split('-')[-1])
        print('## start training...')
        try:
            for epoch in range(start_epoch, FLAGS.epochs):
                n = 0
                n_chunk = len(x_batches)  # how many batch
                for batch in range(n_chunk):
                    # process input data
                    input_batch = np.reshape(x_batches[n], [-1, FLAGS.time_steps, FLAGS.pulse_size])  # reshape input_data
                    output_batch = np.reshape(y_batches[n], [-1, FLAGS.time_steps, 1])  # reshape input_data 这里的第3维度为 1

                    loss, _, _ = sess.run([
                        end_points['total_loss'],
                        end_points['last_state'],
                        end_points['train_op']
                    ], feed_dict={input_data: input_batch, output_targets: output_batch})
                    n += 1
                    print('Epoch: %d, batch: %d, training loss: %.6f' % (epoch, batch, loss))
                if epoch % 6 == 0:
                    saver.save(sess, os.path.join(FLAGS.model_dir, FLAGS.model_prefix), global_step=epoch)
        except KeyboardInterrupt:
            print('## Interrupt manually, try saving checkpoint for now...')
            saver.save(sess, os.path.join(FLAGS.model_dir, FLAGS.model_prefix), global_step=epoch)
            print('## Last epoch were saved, next time will start from epoch {}.'.format(epoch))


# def run_testing(test_x_batches, test_y_batches):
#     input_data = tf.placeholder(tf.float32, [None, FLAGS.time_steps, FLAGS.pulse_size])
#     # output_targets = tf.placeholder(tf.int32, [None, FLAGS.time_steps, 1])
#
#     end_points = rnn_model(model='lstm', input_data=input_data, output_data=None, vocab_size=FLAGS.vocab_size,
#             rnn_size=128, num_layers=2, batch_size=FLAGS.batch_size, learning_rate=FLAGS.learning_rate)
#
#     saver = tf.train.Saver(tf.global_variables())
#     init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
#
#     config = tf.ConfigProto()
#     config.gpu_options.allow_growth = True
#
#     with tf.Session(config=config) as sess:
#         sess.run(init_op)
#         checkpoint = tf.train.latest_checkpoint(FLAGS.model_dir)
#         saver.restore(sess, checkpoint)
#
#         n = 0
#         n_chunk = len(test_x_batches)
#         for batch in range(n_chunk):
#             test_input_batch = np.reshape(test_x_batches[n], [-1, FLAGS.time_steps, FLAGS.pulse_size])  # reshape input_data
#             test_output_batch = np.reshape(test_y_batches[n], [-1, FLAGS.time_steps, 1])  # reshape input_data 这里的第3维度为 1
#             [predict, last_state] = sess.run([end_points['prediction'], end_points['last_state']],
#                     feed_dict={input_data: test_input_batch})
#
#             correct_prediction = tf.equal(tf.argmax(predict, 1), tf.argmax(test_output_batch, 1))
#             accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
#             print("test batch id : ", n, "  test accuracy : ", sess.run(accuracy))
#             n += 1


def main(_):
    train_x_batches, train_y_batches = get_training_data(FLAGS.batch_size * FLAGS.time_steps)
    run_training(train_x_batches, train_y_batches)


if __name__ == '__main__':
    tf.app.run()
