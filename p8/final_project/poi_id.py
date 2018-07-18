#!/usr/bin/python
# python 3.6 and scikit-learn 0.19.1

import sys
import pickle
sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data

### Loading the dictionary containing the dataset
with open("final_project_dataset.pkl", "rb") as data_file:
    data_dict = pickle.load(data_file)

### Removing outlier(s)
my_dataset = data_dict
my_dataset.pop('TOTAL')

### Adding new feature... creative I know


finance = ['salary','deferral_payments','total_payments','loan_advances',
           'bonus','restricted_stock_deferred','deferred_income','total_stock_value',
           'expenses','exercised_stock_options','other','long_term_incentive',
           'restricted_stock','director_fees']

for person in my_dataset:
    my_dataset[person]['worth'] = sum(
            my_dataset[person][f]
            for f in finance
            if my_dataset[person][f] != 'NaN')


### Preparing data for feature selection
all_features_list = ['poi']
nonpoi_features = list(my_dataset['LAY KENNETH L'])
nonpoi_features.remove('email_address')
nonpoi_features.remove('poi')
nonpoi_features.remove('worth')
all_features_list.extend(nonpoi_features)
all_data = featureFormat(my_dataset, all_features_list, sort_keys = True)
all_labels, all_features = targetFeatureSplit(all_data)

### Scaling features for algorithms affected by it
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
scaler.fit_transform(all_features)

### Testing k best parameters with GridSearchCV
from sklearn.feature_selection import SelectKBest
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import GridSearchCV

kbest = SelectKBest()
nb = GaussianNB()
pipeline = Pipeline(steps = [('kbest', kbest), ('nb', nb)])

k_options = list(range(len(all_features_list)))[1:]
param_grid = {'kbest__k': k_options}
cv = StratifiedShuffleSplit(test_size = 0.3, random_state = 70)

gridsearch = GridSearchCV(pipeline, param_grid = param_grid, scoring = 'f1', cv = cv)
gridsearch.fit(all_features, all_labels)

### Incorporating k best features found via gridsearch
best_features = [nonpoi_features[i] for i in
                 gridsearch.best_estimator_.named_steps['kbest'].get_support(indices=True)]

features_list = ['poi']
features_list.extend(best_features)

### Extracting features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)

### Using best classifier to generate pkl file
clf = GaussianNB()

### Generating training/testing sets
sss = StratifiedShuffleSplit(test_size = 0.3, random_state = 47)

features_train = []
features_test = []
labels_train = []
labels_test = []
for train_idx, test_idx in sss.split(features, labels):
    for ii in train_idx:
        features_train.append(features[ii])
        labels_train.append(labels[ii])
    for jj in test_idx:
        features_test.append(features[jj])
        labels_test.append(labels[jj])

### Training the classifier
clf.fit(features_train, labels_train)

### Generating pkl files
dump_classifier_and_data(clf, my_dataset, features_list)
