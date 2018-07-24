
# Identify Fraud from Enron Email

Jeremy Tran  
June 13, 2018

### Dataset and Questions

Machine learning uses computing and statistics to generate findings, which are only as good as the data used.  The Enron scandal was this huge messy affair, and unsurprisingly the data associated with it is also huge and messy, which makes it a suitable application for machine learning to see if certain questions can be answered.  Namely, in this project, the question is if persons of interest (POIs) can be identified from the financial and e-mail data.

The dataset as initially prepared contains information for 146 individuals, with up to 21 features for finances, e-mail use and status as a POI.  There are 18 POIs total to be identified.

As explained in the course material, one blatant outlier is the `TOTAL` "individual," so I removed that entry first.  


```python
#!/usr/bin/python

import sys
import pickle
import numpy as np
sys.path.append("../tools/")

import warnings
warnings.filterwarnings('ignore')

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data, test_classifier

with open("final_project_dataset.pkl", "rb") as data_file:
    data_dict = pickle.load(data_file)

my_dataset = data_dict
my_dataset.pop('TOTAL')

### Printing key characteristics of dataset
print('no of persons: ', len(data_dict))
print('no of POIs: ',
      len(['poi' for poi in data_dict if data_dict[poi]['poi'] == 1]))
print('no of NaN values: ',
      len([(person,feature)
           for person in data_dict
           for feature in data_dict[person]
           if data_dict[person][feature] == 'NaN']))
```

    no of persons:  145
    no of POIs:  18
    no of NaN values:  1352
    

    C:\Users\jt002\Anaconda3\lib\site-packages\sklearn\cross_validation.py:41: DeprecationWarning: This module was deprecated in version 0.18 in favor of the model_selection module into which all the refactored classes and functions are moved. Also note that the interface of the new CV iterators are different from that of this module. This module will be removed in 0.20.
      "This module will be removed in 0.20.", DeprecationWarning)
    

### Feature Selection

_**New Feature**_

As per assignment requirements, I had to create a new feature, and seeing as I'm not an expert in mining tons of text data, I opted simply... to create a new feature that would be the agglomeration of all financial info for each individual, and see if, after being appropriately scaled and undergoing pca, etc, it could replace the disparate myriad finanical details as features and, in conjunction, with email features, classify POIs.


```python
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

### Testing replacing all financial features with 'worth'
features_list = ['poi', 'worth', 'shared_receipt_with_poi', 'from_poi_to_this_person',
               'from_this_person_to_poi']
data = featureFormat(my_dataset, features_list, sort_keys = True)

from sklearn.model_selection import train_test_split
labels, features = targetFeatureSplit(data)
features_test, features_train, labels_test, labels_train = train_test_split(
    features, labels, test_size = 0.3, random_state = 42)

from sklearn.metrics import classification_report
from sklearn.naive_bayes import GaussianNB

target_names = ['non-POI','POI']
nb = GaussianNB()
nb.fit(features_train, labels_train)

print('"Worth" as a Feature')
print('Naive Bayes Accuracy: ', nb.score(features_test, labels_test), '\n')
print(classification_report(labels_test, nb.predict(features_test),
                            target_names = target_names))
```

    "Worth" as a Feature
    Naive Bayes Accuracy:  0.84 
    
                 precision    recall  f1-score   support
    
        non-POI       0.88      0.94      0.91        88
            POI       0.17      0.08      0.11        12
    
    avg / total       0.80      0.84      0.82       100
    
    


My preliminary testing showed that this aggregate variable did not vastly improve predictions when added alongside existing financial features to classifiers.  This was perhaps expected, as it is simply a duplicate of the existing information and perhaps augments certain selected financial features.  However, when used in lieu of all financial features, and coupled with only e-mail information, this combined 'worth' value did not fare well in predicting any POIs at all...

That certain financial features were more predictive than net worth alone reflected that simple wealth or large amounts of assets were not peculiar to POIs... though they did tend to have higher net asset values.

_**Univariate feature selection**_

I decided to use a univariate feature selection method, SelectKBest, since I'm not very creative.  In this method, an ANOVA f-score is calculated for each feature against the classification labels, and thus the importance of each feature can be guesstimated.  In a way, I felt like this was cheating since I was essentially using the entire dataset to find the important features, and then later making predictions using subsets of that dataset based on those features... 


```python
### Preparing data for feature selection
all_features_list = ['poi']
nonpoi_features = list(my_dataset['LAY KENNETH L'])
nonpoi_features.remove('email_address')
nonpoi_features.remove('poi')
nonpoi_features.remove('worth')
all_features_list.extend(nonpoi_features)
all_data = featureFormat(my_dataset, all_features_list, sort_keys = True)
all_labels, all_features = targetFeatureSplit(all_data)

### Using SelectKBest to determine features importances
from sklearn.feature_selection import SelectKBest

kbest = SelectKBest(k = 'all')
kbest.fit(all_features, all_labels)
best_order = np.argsort(kbest.scores_)[::-1]

print("Features and ANOVA Scores\n")
for i in range(len(best_order)):
    print(nonpoi_features[best_order[i]], ": ", kbest.scores_[best_order[i]])

```

    Features and ANOVA Scores
    
    exercised_stock_options :  25.09754152873549
    total_stock_value :  24.4676540475264
    bonus :  21.06000170753657
    salary :  18.575703268041785
    deferred_income :  11.5955476597306
    long_term_incentive :  10.072454529369441
    restricted_stock :  9.346700791051488
    total_payments :  8.866721537107772
    shared_receipt_with_poi :  8.74648553212908
    loan_advances :  7.242730396536018
    expenses :  6.23420114050674
    from_poi_to_this_person :  5.344941523147337
    other :  4.204970858301416
    from_this_person_to_poi :  2.426508127242878
    director_fees :  2.107655943276091
    to_messages :  1.69882434858085
    deferral_payments :  0.2170589303395084
    from_messages :  0.16416449823428736
    restricted_stock_deferred :  0.06498431172371151
    

From examining the scores, I found that certain financial features showed huge variances between POIs and non-POIs, with the rest of the features, including both financial and e-mail information, being less important.

I decided to use `GridSearchCV` to test all the possible number of k best features as run through a classifier (randomly chosen to be Naive Bayes), using f1 as the performance score.

(idea for this code courtesy of user4646875 https://stackoverflow.com/questions/44999289/print-feature-names-for-selectkbest-where-k-value-is-inside-param-grid-of-gridse)


```python
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import GridSearchCV

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

### Printing best parameters of select k best
print('best f1 score: ', gridsearch.best_score_)
print('best k parameter:', gridsearch.best_params_)
print('best k=5 features: ', best_features)
```

    best f1 score:  0.39580808080808083
    best k parameter: {'kbest__k': 5}
    best k=5 features:  ['salary', 'bonus', 'deferred_income', 'total_stock_value', 'exercised_stock_options']
    

And... it turned out the best estimator came from using only the 5 best features, whose anova scores were also all above 10 in the above examination.

_**Feature Scaling**_

Since I was going to be testing a bunch of algorithms, some of which may depend on scaling of feature values (e.g. SVM), I decided to apply MinMaxScaler to all of the features.  Since scaling technically modified my dataset, I probably should've concatenated the features and labels after scaling, saved them as `my_dataset`, and _then_ split them again into labels and features for the subsequent steps...or maybe not.


```python
### Extracting features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)

### Scaling features for certain algorithms
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
features = scaler.fit_transform(features)

```

### Picking and Tuning Algorithims

_**Prelimnary**_

For picking algorithms initially, using the built-in in score function of each classifier to test accuracy was probably a sufficient performance measure.  But since we are also concerned with precision and recall in this project (and by extension, the f1 score as the averaged mean of precision and recall), I found a function in `sklearn.metrics` that computes all of the above and thus imported it for use for evaluating algorithms.

Actually, to begin training the algorithms I needed to use a cross-validation method, which is tied to training and testing.  Since only 18 out of 144 labels are POIs, a stratified splitting strategy made sense.


```python
### Generating testing and training data
from sklearn.model_selection import StratifiedShuffleSplit

sss = StratifiedShuffleSplit(test_size = 0.3, random_state = 47)

features_train = []
features_test  = []
labels_train   = []
labels_test    = []
for train_idx, test_idx in sss.split(features, labels):
    for ii in train_idx:
        features_train.append(features[ii])
        labels_train.append(labels[ii])
    for jj in test_idx:
        features_test.append(features[jj])
        labels_test.append(labels[jj])

```

_**Naive Bayes**_

Not much to play around with here, and performance seemed reasonable.


```python
nbc = GaussianNB()
nbc.fit(features_train, labels_train)

print('Naive Bayes Accuracy: ', nbc.score(features_test, labels_test), '\n')
print(classification_report(labels_test, nbc.predict(features_test),
                            target_names = target_names))

```

    Naive Bayes Accuracy:  0.9 
    
                 precision    recall  f1-score   support
    
        non-POI       0.93      0.96      0.94       370
            POI       0.61      0.44      0.51        50
    
    avg / total       0.89      0.90      0.89       420
    
    


_**Tuning SVM Parameters with GridSearchCV**_

Tuning algorithm parameters is important as typically there is a tradeoff between variance and bias.  High bias algorithms may fail to predict the underlying pattern, while high variance models may be responding more to noise than actual relations in the data.

I used GridSearchCV to test various parameters with SVM, and the best-performing ones seemed... highly unorthrodox, I guess?  Default values for C and gamma are 1 and 1/(sample size), respectively.  The accuracy score also seemed highly suspect, possibly reflecting overfitting...


```python
from sklearn.svm import SVC

params = {'C':[0.1, 1, 10, 100],
          'gamma':[1e-3, 1e-2, 1e-1, 1e1]}
gsc = GridSearchCV(SVC(), params, cv=5)
gsc.fit(features_train, labels_train)

print('Best Parameters: ', gsc.best_params_)
print('SVM Accuracy: ', gsc.score(features_test, labels_test), '\n')
print(classification_report(labels_test, gsc.predict(features_test),
                            target_names = target_names))


```

    Best Parameters:  {'C': 100, 'gamma': 10.0}
    SVM Accuracy:  0.9666666666666667 
    
                 precision    recall  f1-score   support
    
        non-POI       0.96      1.00      0.98       370
            POI       1.00      0.72      0.84        50
    
    avg / total       0.97      0.97      0.96       420
    
    

_**PCA and Adaboost**_

I thought maybe an ensemble method would model the data better since.. more is typically better.. or in this case, maybe more overfitting?


```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.decomposition import PCA

dt = DecisionTreeClassifier()
adaboost = AdaBoostClassifier(base_estimator = dt)
pca = PCA(n_components=5)
adc = Pipeline(steps = [('pca',pca), ('adaboost', adaboost)])

adc.fit(features_train, labels_train)

print('Adaboost Accuracy: ', adc.score(features_test, labels_test), '\n')
print(classification_report(labels_test, adc.predict(features_test),
                            target_names = target_names))
```

    Adaboost Accuracy:  1.0 
    
                 precision    recall  f1-score   support
    
        non-POI       1.00      1.00      1.00       370
            POI       1.00      1.00      1.00        50
    
    avg / total       1.00      1.00      1.00       420
    
    

### Validation and Evaluation

_**Evaluation**_

In this project, we are interested in recall and precision, and secondarily, the f1 score, which for our purposes is the averaged recall and precision scores.

- recall: true positive/(true positive + false negative), or probability that relevant items are classified
- precision: true positive/(true positive + false positive), or probability that items classified are relevant
- f1 score: (recall + precision)/2

We are probably more focused on recall, as it reflects the probability of identifying POIs even at the risk of misidentifying 'non-interesting' persons (that's what you get for hanging with this crowd!), while precision reflects the probability that those identified are truly of interest.

_**Validation**_

Validation is testing the validity of a model's predictions, usually on a test data set.  A classic mistake is using the entire dataset for both training and testing, which would result in a model that could make seemingly very good predictions but which are actually a result of overfitting.  Thus, separating data into testing and training sets is essential, but the model could still overfit on whatever was apportioned as the test set, thus necessitating a validation test for initial evaluation and a test set for final evaluation.

Cross-validation supposedly alleviates this problem, and as mentioned above I decided to use stratified splits for cross-validation.  

Using the tester provided by the assignment, boring Naive Bayes fared the best.


```python
test_classifier(nbc, my_dataset, features_list)
```

    GaussianNB(priors=None)
    	Accuracy: 0.85464	Precision: 0.48876	Recall: 0.38050	F1: 0.42789	F2: 0.39814
    	Total predictions: 14000	True positives:  761	False positives:  796	False negatives: 1239	True negatives: 11204
    
    
