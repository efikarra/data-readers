'''
Created on 5 Apr 2017

@author: efi
'''
from keras.preprocessing.sequence import pad_sequences
from keras.utils import np_utils
import numpy as np


class Preprocessor():
    def __init__(self, vocab, pad_value=0., seq_length=None):
        self.vocab = vocab
        self.seq_length = seq_length
        self.pad_value = pad_value

    def _pad_sequences(self, sequences):
        padded_seqs = pad_sequences(sequences, maxlen=self.seq_length, dtype='int32', padding='pre', truncating='pre',
                                    value=self.pad_value)
        self.seq_length = padded_seqs.shape[1]
        return padded_seqs.tolist()

    def transform_data(self, sequences, xs=None):
        pass


class BaselinePreprocessor(Preprocessor):
    def __init__(self, vocab, pad_value=0., seq_length=None):
        Preprocessor.__init__(self, vocab, pad_value, seq_length)

    def transform_data(self, sequences, xs=None):
        x_data = []
        y_data = []
        index = 0
        for seq in sequences:
            x_seq = []
            y_seq = []
            for i in range(0, len(seq) - 1, 1):
                features = []
                targets = []
                features += np_utils.to_categorical([self.vocab[seq[i]]], len(self.vocab))[0, :].tolist()
                targets += np_utils.to_categorical([self.vocab[seq[i + 1]]], len(self.vocab))[0, :].tolist()
                if xs:
                    features += xs[index][i]
                x_seq.append(features)
                y_seq.append(targets)
            x_data.append(x_seq)
            y_data.append(y_seq)
            index += 1
        features_dim = len(self.vocab)
        if xs:
            features_dim += len(self.vocab)
        padded_x_data = self._pad_sequences(x_data)
        padded_y_data = self._pad_sequences(y_data)
        padded_y_data = np.reshape(padded_y_data, (len(padded_y_data), self.seq_length, len(self.vocab)))
        padded_x_data = np.reshape(padded_x_data, (len(padded_x_data), self.seq_length, features_dim))
        return padded_x_data, padded_y_data


class FullModelPreprocessor(Preprocessor):
    def __init__(self, vocab, pad_value=0., seq_length=None):
        Preprocessor.__init__(self, vocab, pad_value, seq_length)

    def transform_data(self, sequences, xs):
        # sequences=sequences[:]
        x_data = []
        Context_Data = []
        y_data = []
        for xi in xs:
            x_seq = []
            for i in range(0, len(xi) - 1, 1):
                x_seq.append(xi[i])
            Context_Data.append(x_seq)

        for j, seq in enumerate(sequences):
            x_seq = []
            y_seq = []
            for i in range(0, len(seq) - 1, 1):
                x_seq.append(np_utils.to_categorical([self.vocab[seq[i]]], len(self.vocab))[0, :].tolist())
                y_seq.append(np_utils.to_categorical([self.vocab[seq[i + 1]]], len(self.vocab))[0, :].tolist())
            x_data.append(x_seq)
            y_data.append(y_seq)
        features_dim = len(self.vocab)
        padded_x_data = self._pad_sequences(x_data)
        padded_context_data = self._pad_sequences(Context_Data)
        padded_y_data = self._pad_sequences(y_data)
        padded_y_data=np.reshape(padded_y_data,(len(padded_y_data),self.seq_length,len(self.vocab)))
        padded_context_data=np.reshape(padded_context_data, (len(padded_context_data), self.seq_length, features_dim))
        padded_x_data=np.reshape(padded_x_data, (len(padded_x_data), self.seq_length, features_dim))
        return padded_x_data, padded_y_data, padded_context_data
