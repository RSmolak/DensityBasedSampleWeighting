from sklearn.datasets import make_classification
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.base import clone
from sklearn.metrics import accuracy_score, precision_score, balanced_accuracy_score, recall_score
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import LabelEncoder

from ADASYN import CustomNNADASYNClassifier
from OS import CustomNNRandomOversamplingClassifier
from SMOTE import CustomNNSMOTEClassifier

from model import MyNNModel, CustomNNClassifier

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_data(file_name):
    df = pd.read_csv(file_name, comment='@', header=None)

    features = df.iloc[:, :-1].values
    labels = df.iloc[:, -1].values

    print(np.unique(labels))
    le = LabelEncoder()
    numerical_labels = le.fit_transform(labels)

    return features, numerical_labels



# Learning hyperparameters
num_epoch = 100
batch_size = 100
learning_rate = 0.005

# Create datasets
generated_datasets = []
imbalanced_ratios = [0.55, 0.6, 0.7, 0.8, 0.9, 0.95]
for ratio in imbalanced_ratios:
    X, y = make_classification(n_samples=1000, n_features=15, n_informative=15, n_redundant=0, weights=[ratio,1-ratio])
    generated_datasets.append((X,y))


density_weighting_classifier = CustomNNClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method='density_weighting'
)

count_weighting_classifier = CustomNNClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method='count_weighting'
)
no_weighting_classifier = CustomNNClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method=None
)
adasyn_classifier = CustomNNADASYNClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method=None
)
ros_classifier = CustomNNRandomOversamplingClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method=None
)
smote_classifier = CustomNNSMOTEClassifier(
    model_class=MyNNModel,
    output_size=1,
    learning_rate=learning_rate,
    batch_size=batch_size,
    num_epoch=num_epoch,
    imbalanced_opt_method=None
)

datafiles = [
    'datasets/glass1.dat',
    'datasets/glass-0-1-2-3_vs_4-5-6.dat',
    'datasets/page-blocks0.dat',
    'datasets/vehicle0.dat',
    'datasets/vehicle2.dat',
    'datasets/wisconsin.dat',
    #'datasets/yeast1.dat',
    #'datasets/yeast3.dat',
]

DATASETS = []
DATASETS.extend([load_data(datafile) for datafile in datafiles])
#DATASETS.extend(generated_datasets)

CLASSIFIERS = [
    no_weighting_classifier,
    count_weighting_classifier,
    density_weighting_classifier,
    adasyn_classifier,
    ros_classifier,
    smote_classifier,
]


rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=42)
scores_acc = np.zeros(shape = (len(DATASETS), len(CLASSIFIERS), rskf.get_n_splits()))
scores_bal_acc = np.zeros(shape = (len(DATASETS), len(CLASSIFIERS), rskf.get_n_splits()))
scores_rec = np.zeros(shape = (len(DATASETS), len(CLASSIFIERS), rskf.get_n_splits()))
scores_prec = np.zeros(shape = (len(DATASETS), len(CLASSIFIERS), rskf.get_n_splits()))

accuracies_to_plot = {}
bal_accuracies_to_plot = {}
precision_to_plot = {}
recall_to_plot = {}


for classifier_idx, clf_prot in enumerate(CLASSIFIERS):
    print(classifier_idx)
    accuracies_to_plot = []
    bal_accuracies_to_plot = []
    precision_to_plot = []
    recall_to_plot = []

    for dataset_idx, (X,y) in enumerate(DATASETS):
        print("dataset:", dataset_idx)
        print()
        accuracies_to_plot.append([])
        bal_accuracies_to_plot.append([])
        precision_to_plot.append([])
        recall_to_plot.append([])

        for fold_idx, (train, test) in enumerate(rskf.split(X, y)):
            clf = clone(clf_prot)
            clf.fit(X[train], y[train])
            y_pred = clf.predict(X[test])

            accuracies_to_plot[dataset_idx].append(clf.get_stat('accuracy'))
            bal_accuracies_to_plot[dataset_idx].append(clf.get_stat('bal_accuracy'))
            precision_to_plot[dataset_idx].append(clf.get_stat('precision'))
            recall_to_plot[dataset_idx].append(clf.get_stat('recall'))

            score_acc = accuracy_score(y[test], y_pred)
            scores_acc[dataset_idx, classifier_idx, fold_idx] = score_acc
            score_bal_acc = balanced_accuracy_score(y[test], y_pred)
            scores_bal_acc[dataset_idx, classifier_idx, fold_idx] = score_acc
            score_rec = recall_score(y[test], y_pred)
            scores_rec[dataset_idx, classifier_idx, fold_idx] = score_acc
            score_prec = precision_score(y[test], y_pred, zero_division=1)
            scores_prec[dataset_idx, classifier_idx, fold_idx] = score_acc

    fig, axs = plt.subplots(3, 2, figsize=(6, 9))

    for i, ax in enumerate(axs.flatten()):
        if i < len(DATASETS):
            acc_arr = np.array(accuracies_to_plot[i])
            means_arr = np.mean(acc_arr, axis=0)

            bal_acc_arr = np.array(bal_accuracies_to_plot[i])
            means_bal_arr = np.mean(bal_acc_arr, axis=0)

            prec_arr = np.array(precision_to_plot[i])
            means_prec = np.mean(prec_arr, axis=0)

            rec_arr = np.array(recall_to_plot[i])
            means_rec = np.mean(rec_arr, axis=0)

            ax.plot(range(1, num_epoch + 1), means_arr, label = 'accuracy')
            ax.plot(range(1, num_epoch + 1), means_bal_arr, label = 'bal_accuracy')
            ax.plot(range(1, num_epoch + 1), means_prec, label = 'precision')
            ax.plot(range(1, num_epoch + 1), means_rec, label = 'recall')

            ax.set(xlabel='Epoki', ylabel='Średnia wartość metryki')
            ax.legend()
            ax.set_title(f'Dataset {i+1}')
            ax.set_ylim([0.0, 1.0])

    plt.tight_layout()
    plt.suptitle(f'Classifier {classifier_idx + 1}', fontsize=16)
    plt.savefig(f'Classifier_{classifier_idx + 1}.png')
#
# print('ACC:\n', scores_acc)
# print('BAL_ACC:\n', scores_bal_acc)
# print('REC:\n', scores_rec)
# print('PREC:\n', scores_prec)
# np.save("scores_acc", scores_acc)
# np.save("scores_bal_acc", scores_bal_acc)
# np.save("scores_rec", scores_rec)
# np.save("scores_prec", scores_prec)
