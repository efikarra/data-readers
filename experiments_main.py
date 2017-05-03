"""
Main method for performing experiments
"""
from experiments_methods import *
import datasets
from model import gauss_prior, ArrayInitializer
from keras.regularizers import l2
from keras.initializers import Constant
from sklearn.model_selection import ShuffleSplit
from collections import namedtuple
import pickle
import itertools


def add_results(vall_losses, train_losses, epochs, results, name):
    vall_losses[name].append(results.val_loss)
    train_losses[name].append(results.train_loss)
    epochs[name].append(results.epoch)


def run_k_fold(seqs,n_splits,dataset_name):
    split_wrt_time=False
    max_seq_length = utils.compute_seq_max_length(seqs) - 1
    model_names = ["multinomial", "markov", "ytoy1", "ytoy2","ytoy_xtoy", "ytoz", "ytoz_ytoy", "ytoz_xtoz",
                   "ytoz_ytoy_xtoz", "ytoz_ytoy_xtoy"]
    vall_losses = {k: [] for k in model_names}
    train_losses = {k: [] for k in model_names}
    epochs = {k: [] for k in model_names}

    sf = ShuffleSplit(n_splits=n_splits, random_state=0, train_size=0.8, test_size=0.2)
    splits=1
    for i,(train_idxs,val_idxs) in enumerate(sf.split(seqs)):
        with open(dataset_name+'-split%d'%i+'.pickle', 'wb') as handle:
            pickle.dump((train_idxs,val_idxs), handle, protocol=pickle.HIGHEST_PROTOCOL)
        print "fold %d" % i
        train_seqs = [seqs[i] for i in train_idxs]
        print ""
        val_seqs = [seqs[i] for i in val_idxs]

        n_epochs = 2
        small_n_epochs=2
        rnn_type = "simpleRNN"
        z_dim=10
        batch_size=100
        k = 10e-7

        xs_train = datasets.build_xs(train_seqs, vocab, freq=False)
        xs_val = datasets.build_xs(val_seqs, vocab, freq=False)
        train_freqs, gamma = utils.transition_matrix(train_seqs, len(vocab), k=k, freq=True, end_state=False)
        print "vocabulary size:", len(vocab)
        print "train sequences:", len(train_seqs)
        print "val sequences:", len(val_seqs)
        print
        print "multinomial"
        model, results = run_multinomial(train_seqs, val_seqs, len(vocab), wrt_time=split_wrt_time,k=k)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "markov"
        model, results = run_markov(train_seqs, val_seqs, len(vocab), wrt_time=split_wrt_time, k=k)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        # build train/val sets for rnns
        x_train, y_train, train_xs, x_val, y_val, val_xs = prepare_model_input(train_seqs, val_seqs, xs_train,
                                                                               xs_val, vocab,
                                                                               max_seq_length=max_seq_length)

        print
        print "ytoy1"
        var = 0.01
        init_weights = utils.sample_weights(np.log(train_freqs), np.sqrt(var))
        model, results = run_model_no_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                 wrt_time=split_wrt_time, early_stopping=False,
                                                 model_checkpoint=False,n_epochs=small_n_epochs,
                                                 batch_size=batch_size, y_to_y_regularizer=gauss_prior(np.log(train_freqs),var),
                                                 y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                 verbose=2, model_name="ytoy1", y_bias=False,
                                                 connect_x=False, connect_y=True)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoy2"
        model, results = run_model_no_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                 wrt_time=split_wrt_time, early_stopping=False, n_epochs=n_epochs,
                                                 batch_size=batch_size,model_checkpoint=True,
                                                 y_to_y_regularizer=None,
                                                 y_to_y_w_initializer=None,
                                                 verbose=2, model_name="ytoy2", y_bias=False,
                                                 connect_x=False, connect_y=True)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoy_xtoy"
        var = 1.0
        init_weights = utils.sample_weights(np.log(train_freqs), np.sqrt(var))
        model, results = run_model_no_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                 model_checkpoint=True,orig_seqs_lengths=None, wrt_time=split_wrt_time,
                                                 y_to_y_regularizer=gauss_prior(np.log(train_freqs),var),
                                                 y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                 early_stopping=False, n_epochs=small_n_epochs, batch_size=batch_size,
                                                 verbose=2, model_name="ytoy_xtoy", connect_x=True, y_bias=False,
                                                 connect_y=True, diag_b=True,read_file=None)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoz"
        model, results = run_model_with_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                   toy_regularizer=None,
                                                   orig_seqs_lengths=None, wrt_time=False, read_file=None,
                                                   rnn_type=rnn_type, early_stopping=False,model_checkpoint=True,
                                                   n_epochs=n_epochs, batch_size=batch_size, verbose=2, z_dim=z_dim,
                                                   model_name="ytoz", y_to_z=True, y_to_y=False,
                                                   x_to_y=False, x_to_z=False, z_to_y_drop=0.1)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoz_ytoy"
        model, results = run_model_with_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                   orig_seqs_lengths=None, wrt_time=False, y_to_y_trainable=True,
                                                   y_to_y_regularizer=gauss_prior(np.log(train_freqs),var),
                                                   model_checkpoint=True,
                                                   y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                   read_file=None, rnn_type=rnn_type, early_stopping=False,
                                                   n_epochs=n_epochs, batch_size=batch_size, verbose=2, z_dim=z_dim,
                                                   model_name="ytoz_ytoy", y_to_z=True, y_to_y=True,
                                                   x_to_y=False, x_to_z=False, z_to_y_drop=0.1)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print "ytoz_xtoz"
        model, results = run_model_with_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                   orig_seqs_lengths=None, wrt_time=False, y_to_y_trainable=True,
                                                   y_to_y_regularizer=gauss_prior(np.log(train_freqs),var), read_file=None,
                                                   rnn_type=rnn_type,model_checkpoint=True,
                                                   y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                   early_stopping=False,
                                                   n_epochs=n_epochs, batch_size=batch_size, verbose=0, z_dim=z_dim,
                                                   model_name="ytoz_xtoz", y_to_z=True, y_to_y=False,
                                                   x_to_y=False, x_to_z=True, z_to_y_drop=0.1)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoz_ytoy_xtoz"
        model, results = run_model_with_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                   orig_seqs_lengths=None, wrt_time=False, y_to_y_trainable=True,
                                                   y_to_y_regularizer=gauss_prior(np.log(train_freqs),var), read_file=None,
                                                   rnn_type=rnn_type,model_checkpoint=True,
                                                   y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                   early_stopping=False,
                                                   n_epochs=n_epochs, batch_size=batch_size, verbose=0, z_dim=z_dim,
                                                   model_name="ytoz_ytoy_xtoz", y_to_z=True, y_to_y=True,
                                                   x_to_y=False, x_to_z=True, z_to_y_drop=0.1)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

        print
        print "ytoz_ytoy_xtoy"
        model, results = run_model_with_recurrence(x_train, y_train, train_xs, x_val, y_val, val_xs, vocab,
                                                   orig_seqs_lengths=None, wrt_time=False, y_to_y_trainable=True,
                                                   y_to_y_regularizer=gauss_prior(np.log(train_freqs),var), read_file=None,
                                                   rnn_type=rnn_type,model_checkpoint=True,
                                                   y_to_y_w_initializer=ArrayInitializer(init_weights),
                                                   early_stopping=False,
                                                   n_epochs=n_epochs, batch_size=batch_size, verbose=2, z_dim=z_dim,
                                                   model_name="ytoz_ytoy_xtoy", y_to_z=True, y_to_y=True,
                                                   x_to_y=True, x_to_z=False, z_to_y_drop=0.1)
        add_results(vall_losses, train_losses, epochs, results, model.model_name)

    print "vall_losses: ", vall_losses
    print "train_losses: ", train_losses
    print "epochs: ", epochs
    for name in model_names:
        print
        print "model: %s" % name
        print "val: %f" % np.mean(vall_losses[name])
        print "train: %f" % np.mean(train_losses[name])
        if None not in epochs[name]:
            print "train: %f" % np.mean(epochs[name])


if __name__ == "__main__":
    # load flickr data
    print "Experimenting with Flickr:"
    seqs, vocab = datasets.load_flickr_data()
    print "total seqs,vocab: ", len(seqs), len(vocab)
    seqs = datasets.remove_short_seqs(seqs, min_seq_length=2)
    print "total seqs,vocab: ", len(seqs), len(vocab)
    run_k_fold(seqs,n_splits=3,dataset_name="flickr")
    print "Experimenting with Flickr ended."

    print "Experimenting with MSNBC:"
    seqs, vocab = datasets.load_msnbc_data()
    print "total vocab: ", len(vocab)
    import random
    # run experiments with MSNBC real and simulated data
    seqs = datasets.remove_short_seqs(seqs, min_seq_length=2)
    seqs = [seqs[i] for i in random.sample(xrange(len(seqs)), 10000)]
    run_k_fold(seqs,n_splits=3,dataset_name="msnbc")
    print "Experimenting with MSNBC ended."
