from utilities import *
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import matplotlib.pylab as plt
from sklearn.base import clone

class model():
    def __init__(self):
        pass
    
    def fit(self):
        self.model.fit(self.X_train, self.y_train["pv_measurement"])
    
    def prepare_data(self, X_observed, X_estimated, y, X_selected_features, cross_validate):
        
        
        X_observed_clean = clean_df(X_observed, X_selected_features)
        X_estimated_clean = clean_df(X_estimated, X_selected_features)
        X_estimated_clean_mean = mean_df(X_estimated_clean)
        X_observed_clean_mean = mean_df(X_observed_clean)
        
        X_train = pd.concat([X_observed_clean_mean, X_estimated_clean_mean])
        X_train = date_forecast_to_time(X_train)
        X_train, y = resize_training_data(X_train,y)
        if cross_validate == True:
            cross_validate(X_train, y_train)
        self.X_columns = X_train.columns
        self.train_test_data_split(X_train, y)
        #self.scale_data()
        
        if cross_validate:
            self.cross_validate(X_train, y)
            
        self.X_columns = X_train.columns
        self.train_test_data_split(X_train, y)
        
    def train_test_data_split(self, X, y):
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size = 0.1, shuffle = True, random_state = 42)
        
    def scale_data(self):
        self.X_train = scale_df(self.X_train, True)
        self.X_test = scale_df(self.X_test, False)
        
    def pred(self, X_test = None):
        max_value = self.y_train["pv_measurement"].max()
        if X_test is None:
            X_test = self.X_test
            self.pred_estimated = self.model.predict(X_test)
            self.pred_estimated = self.pred_estimated.clip(min = 0, max = max_value)
            
        else:
            X_test = mean_df(X_test[self.X_selected_features])
            X_test = date_forecast_to_time(X_test).drop(columns = ['date_forecast'])
            #X_test = scale_df(X_test, False)
            self.prediction = self.model.predict(X_test)
            self.prediction = self.prediction.clip(min = 0, max = max_value)
            
    def mae(self):
        return mean_absolute_error(self.y_test["pv_measurement"], self.pred_estimated)
    
    def feature_importence_plot(self):
        list_of_feature_and_importance = {}
        list_of_feature = []
        self.model.feature_importances_
        plt.figure(figsize=(20,10))
        plt.barh(self.X_columns, self.model.feature_importances_)
        for feature, importance in zip(self.X_columns, self.model.feature_importances_):
            print(f"{feature}: {importance}")
            if (importance >= 0.002):
                list_of_feature_and_importance[feature] = importance
                list_of_feature.append(feature)
        print(list_of_feature_and_importance)
        print(list_of_feature)
                
    def corr_plot(self):
        # Calculate correlation coefficient
        corr, _ = pearsonr(self.y_test["pv_measurement"], self.pred_estimated)
        print(f"Pearson correlation: {corr:.2f}")
        
        # Calculate the linear fit
        coefficients = np.polyfit(self.y_test["pv_measurement"], self.pred_estimated, 1)
        polynomial = np.poly1d(coefficients)
        linear_fit = polynomial(self.y_test["pv_measurement"])
        
        # Create scatter plot
        plt.figure(figsize=(10, 6))
        plt.scatter(self.y_test["pv_measurement"], self.pred_estimated, label='Data points')
        plt.plot(self.y_test["pv_measurement"], linear_fit, color='red', label=f'Linear fit: y = {coefficients[0]:.2f}x + {coefficients[1]:.2f}')
        
        plt.xlabel('Actual values (y_test)')
        plt.ylabel('Predicted values (y_pred)')
        plt.title('Correlation between Actual and Predicted Values with Linear Fit')
        plt.legend()
        plt.grid(True)
        plt.show()
        
    def cross_validate(self, X_train, y_train):
        # Cross-validation
        scores = cross_val_score(self.model, X_train, y_train["pv_measurement"], cv=5, scoring='neg_mean_absolute_error', n_jobs = -1)
        scores = -scores  # Making scores positive for easier interpretation
        self.cross_val_score_mean = scores.mean()
        self.cross_val_score = scores

