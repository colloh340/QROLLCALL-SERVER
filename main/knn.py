import pandas as pd
from sklearn.datasets import load_iris

iris=load_iris()
iris.feature_names
iris.target_names

df=pd.DataFrame(iris.data, columns=iris.feature_names)
df.head()

df['target']=iris.target
df.head()
df[df.target==1].head()
df[df.target==2].head()

df0=df[:50]
df1=df[50:100]
df2=df[100:]
import matplotlib.pyplot as plt

#matplotlib inline

plt.xlabel('Sepal Lenth')
plt.ylabel('Sepal Width')
plt.scatter(df0['sepal length (cm)'],df0['sepal width (cm)'], color="green", marker='X')
plt.scatter(df1['sepal length (cm)'],df1['sepal width (cm)'], color="blue", marker='*')
plt.scatter(df2['sepal length (cm)'],df2['sepal width (cm)'], color="red", marker='+')

plt.xlabel('Petal Length')
plt.ylabel('Petal Width')
plt.scatter(df0['petal length (cm)'],df0['petal width (cm)'], color="green", marker='X')
plt.scatter(df1['petal length (cm)'],df1['petal width (cm)'], color="blue", marker='*')
plt.scatter(df2['petal length (cm)'],df2['petal width (cm)'], color="red", marker='+')

from sklearn.model_selection import train_test_split
x=df.drop(['target'], axis='columns')
y=df.target
x.head()


x_train, x_test, y_train, y_test= train_test_split(x,y, test_size=0.2, random_state=1)
len(x_train)
len(x_test)
from sklearn.neighbors import KNeighborsClassifier
knn=KNeighborsClassifier(n_neighbors=3)
knn.fit(x_train,y_train)

knn.score(x_test,y_test)
from sklearn.metrics import confusion_matrix
y_pred=knn.predict(x_test)
cm=confusion_matrix(y_test, y_pred)
cm


# matplotlib inline
import matplotlib.pyplot as plt
import seaborn as sn
plt.figure(figsize=(7,5))
sn.heatmap(cm,annot=True)
plt.xlabel('Predicted')
plt.ylabel('Truth')

from sklearn.metrics import classification_report
print(classification_report(y_test,y_pred))