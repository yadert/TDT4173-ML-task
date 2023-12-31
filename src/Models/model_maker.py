from utilities import *
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import matplotlib.pylab as plt
from sklearn.base import clone
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict, KFold

class model():
    def __init__(self):
        pass
    
    def fit(self):
        self.model.fit(self.X_train, self.y_train["pv_measurement"])
        
    def pred(self):
        max_value = self.y_train["pv_measurement"].max()
        self.prediction = self.model.predict(self.X_test)
        self.pred_estimated = self.model.predict(self.X_valid)
        self.prediction = self.prediction.clip(min = 0, max = max_value)
        self.predictions = self.floor_pred([self.prediction], [self.X_test])
    
    def feature_importence_plot(self):
        self.model.feature_importances_
        plt.figure(figsize=(20,10))
        plt.barh(self.X_train.columns, self.model.feature_importances_)
    
    def corr_plot(self):
        # Calculate correlation coefficient
        corr, _ = pearsonr(self.y_valid["pv_measurement"], self.pred_estimated)
        print(f"Pearson correlation: {corr:.2f}")
        
        # Calculate the linear fit
        coefficients = np.polyfit(self.y_valid["pv_measurement"], self.pred_estimated, 1)
        polynomial = np.poly1d(coefficients)
        linear_fit = polynomial(self.y_valid["pv_measurement"])
        
        # Create scatter plot
        plt.figure(figsize=(10, 6))
        plt.scatter(self.y_valid["pv_measurement"], self.pred_estimated, label='Data points')
        plt.plot(self.y_valid["pv_measurement"], linear_fit, color='red', label=f'Linear fit: y = {coefficients[0]:.2f}x + {coefficients[1]:.2f}')
        
        plt.xlabel('Actual values (y_valid)')
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
        print("Cross-validation scores:", scores)
        print("Mean cross-validation score:", self.cross_val_score_mean)
        
    
    def cross_val_stack(self, X_train, y_train):
            # Setup cross-validation scheme
            kf = KFold(n_splits=5, shuffle=True, random_state=1)
    
            # Prepare to collect predictions, actual values, and DataFrames
            predictions = []
            actuals = []
            maes = []
            training_dfs = []  # List to collect training DataFrames
    
            # Iterate over each split
            for train_index, test_index in kf.split(X_train):
                # Split the data
                X_train_fold, X_test_fold = X_train.iloc[train_index], X_train.iloc[test_index]
                y_train_fold, y_test_fold = y_train.iloc[train_index], y_train.iloc[test_index]
    
                # Save the training DataFrame for this fold
                training_dfs.append(X_test_fold)
    
                # Fit the model
                self.model.fit(X_train_fold, y_train_fold["pv_measurement"])
    
                # Predict on the test fold
                fold_predictions = self.model.predict(X_test_fold)
    
                fold_predictions = fold_predictions.clip(min=0, max=self.y_train["pv_measurement"].max())
    
                # Calculate and store MAE for the fold
                fold_mae = mean_absolute_error(y_test_fold["pv_measurement"], fold_predictions)
                maes.append(fold_mae)
    
                # Store predictions and actual values
                predictions.append(fold_predictions)
                actuals.append(y_test_fold["pv_measurement"].values)
    
            self.cross_val_mae_mean = np.mean(maes)
            # Concatenate to have full array of cross-validated predictions and actuals
            self.cross_val_predictions = np.concatenate(predictions)
            self.cross_val_actuals = np.concatenate(actuals)
            self.cross_val_floored = np.concatenate(self.floor_pred(predictions, training_dfs))
            return self.cross_val_floored, self.cross_val_actuals, self.cross_val_mae_mean
        
        def floor_pred(self, y_pred, X_valid):
            floored_predictions = []
            for i in range(len(y_pred)):
                threshold = 0  # set your threshold here
                predictions_fold = y_pred[i]
                valid_df_fold = X_valid[i]
    
                # Make sure the indices align, this assumes `sun_elevation:d` is a column in the DataFrame
                mask = valid_df_fold["sun_elevation:d"] < threshold
    
                # Check that mask and the predictions have the same length
                if len(mask) != len(predictions_fold):
                    raise ValueError(f"Length mismatch between mask and predictions in fold {i}: {len(mask)} vs {len(predictions_fold)}")
    
                # Apply the mask
                predictions_fold = np.where(mask, 0, predictions_fold)
    
                # Append the floored predictions to the list
                floored_predictions.append(predictions_fold)
    
            # At the end, concatenate all the floored prediction arrays
            return floored_predictions
