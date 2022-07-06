'''
Strategy based on machine learning models.
'''
# TODO refactor, move content to modules.predictor
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
from modules.predictor import Predictor
from utils.config import Files

predictor = Predictor(Files.DATA_IND_OSC)		# Files.DATA_BINANCE_OHLC_5M_TREE
# TODO temp
df = predictor.df
X_dataset = predictor.X_dataset
Y_dataset = predictor.Y_dataset

#scaler = MinMaxScaler()
#X_dataset = scaler.fit_transform(X_dataset)
#pca = PCA(n_components=10)
#principalComponents = pca.fit_transform(X_dataset)
#X_dataset = pd.DataFrame(data=principalComponents)

# X_train, X_test, Y_train, Y_test = train_test_split(X_dataset, Y_dataset, test_size=0.001)
X_train = X_dataset.iloc[:int(X_dataset.shape[0] * 0.6)]
X_test = X_dataset.iloc[int(X_dataset.shape[0] * 0.6):]
Y_train = Y_dataset.iloc[:int(Y_dataset.shape[0] * 0.6)]
Y_test = Y_dataset.iloc[int(Y_dataset.shape[0] * 0.6):]

#clf = AdaBoostClassifier()
clf = MLPClassifier(hidden_layer_sizes=(500, 200, 100, 20), max_iter=5000, tol=0.00001, n_iter_no_change=50, verbose=True)
# clf = RandomForestClassifier(n_estimators=1000, max_depth=100)
# clf = DecisionTreeClassifier()#max_depth=300)
#clf = MLPRegressor()
clf = clf.fit(X_train, Y_train)
scores = cross_val_score(clf, X_train, Y_train, cv=2)
pred_overfit = clf.predict(X_train)
pred = clf.predict(X_test)

print(df.columns)
# print(export_text(clf, feature_names=df.columns.values.tolist()[1:-1], show_weights=True))
print(scores)
print('Accuracy validation: ' + str(scores.mean()))
print('Accuracy overfit: ', accuracy_score(Y_train, pred_overfit))
print('Accuracy: ', accuracy_score(Y_test, pred))
print(classification_report(Y_test, pred))
