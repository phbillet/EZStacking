import io
import functools
import pandas as pd
import numpy as np
import nbformat as nbf
import ipywidgets as widgets
from IPython.display import display
from ipyfilechooser import FileChooser

def analyze(problem_type, stacking, data_size, with_keras, with_xgb, yb, seaborn, file, target_col,\
            user_drop_cols, threshold_NaN, threshold_cat, threshold_Z):

    pd_pk_import, pd_pk_from, pd_level_0, pd_document, pd_tree = set_config(with_keras, with_xgb, problem_type,\
                                                                   stacking, yb, seaborn, data_size)
    
    nb = nbf.v4.new_notebook()
    nb['cells'] = []
    
    text = "# EDA & modelization"
    nb['cells'].append(nbf.v4.new_markdown_cell(text))

    nb = load_package(nb, pd_pk_import, pd_pk_from)
       
    for index, row in pd_document.iterrows():
#        print("row =", row)
        if row[1] != 'None':
           if row[0] == ' ': 
              text = row[1]            
           else:
              text = str(row[0]) + ' ' + str(row[1])
           nb['cells'].append(nbf.v4.new_markdown_cell(text))
        if row[2] != 'None':
           code = eval(row[2])
           nb['cells'].append(nbf.v4.new_code_cell(code))

    return nb

def set_config(with_keras, with_xgb, problem_type, stacking, yb, seaborn, data_size):
    xls = pd.ExcelFile('EZStacking_config.xlsx')
    meta_package = pd.read_excel(xls, 'meta_package')
    package_source = pd.read_excel(xls, 'package_source')
    package = pd.read_excel(xls, 'package')
    document = pd.read_excel(xls, 'document')
    
    meta_package.loc[meta_package['meta_package_index'] == 'STACK', ['meta_package_valid']] = stacking
    meta_package.loc[meta_package['meta_package_index'] == 'KER', ['meta_package_valid']] = with_keras
    meta_package.loc[meta_package['meta_package_index'] == 'XGB', ['meta_package_valid']] = with_xgb
    meta_package.loc[meta_package['meta_package_index'] == 'YB', ['meta_package_valid']] = yb
    meta_package.loc[meta_package['meta_package_index'] == 'SNS', ['meta_package_valid']] = seaborn
                     
    problem = problem_type
    size = data_size
    
    package_source_type = 'full'

    pd_pk_import = package_source[(package_source.package_source_type   == package_source_type) \
                                 ].merge(meta_package[(meta_package.meta_package_valid == True) & \
                                         ((meta_package.meta_package_data_size == 'both') | \
                                         (meta_package.meta_package_data_size == data_size))], \
                                         left_on  = 'meta_package_index', \
                                         right_on = 'meta_package_index', \
                                         how = 'inner') \
                                 [['package_source_index', 'package_source_name', \
                                   'package_source_short_name', 'package_source_code']]

    package_source_type = 'partial'

    pd_pk_srce_from = package_source[(package_source.package_source_type == package_source_type)\
                                    ].merge(meta_package[(meta_package.meta_package_valid == True) & \
                                             ((meta_package.meta_package_data_size == 'both') | \
                                             (meta_package.meta_package_data_size == data_size))], \
                                            left_on  = 'meta_package_index', \
                                            right_on = 'meta_package_index', \
                                            how = 'inner') \
                                    [['package_source_index', 'package_source_name', \
                                      'package_source_short_name', 'package_source_code']] 
    
 
    
    pd_pk_from = package[((package.package_problem == 'None') | (package.package_problem == problem)) \
                        ].merge(pd_pk_srce_from, \
                                left_on='package_source_index', \
                                right_on='package_source_index',\
                                how='inner') \
                    [['package_source_index', 'package_source_name', 'package_name']].drop_duplicates()
    

    pd_level_0 = package[(package.package_type == 'estimator') & \
                         (package.package_problem == problem) & \
                         (package.meta_package_index != 'STACK') \
                        ].merge(pd_pk_from, \
                                left_on='package_source_index', \
                                right_on='package_source_index',\
                                how='inner') \
                         .merge(meta_package[(meta_package.meta_package_valid == True) & \
                                             ((meta_package.meta_package_data_size == 'both') | \
                                             (meta_package.meta_package_data_size == data_size))], \
                                left_on  = 'meta_package_index', \
                                right_on = 'meta_package_index', \
                                how = 'inner') \
                         .merge(meta_package[meta_package.meta_package_valid == True], \
                                left_on  = 'meta_package_index', \
                                right_on = 'meta_package_index', \
                                how = 'inner') \
                        [[ 'package_index', 'package_code']].drop_duplicates()
    
    pd_tree = package[(package.package_type == 'estimator') & \
                      (package.package_problem == problem) & \
                      (package.meta_package_index != 'STACK') \
                     ].merge(pd_pk_from, \
                             left_on='package_source_index', \
                             right_on='package_source_index',\
                             how='inner') \
                      .merge(meta_package[(meta_package.meta_package_valid == True) & \
                                          ((meta_package.meta_package_data_size == 'both') | \
                                          (meta_package.meta_package_data_size == data_size))], \
                             left_on  = 'meta_package_index', \
                             right_on = 'meta_package_index', \
                             how = 'inner') \
                      .merge(meta_package[(meta_package.meta_package_valid == True) & \
                                          (meta_package.meta_package_tree == True)], \
                             left_on  = 'meta_package_index', \
                             right_on = 'meta_package_index', \
                             how = 'inner') \
                      [[ 'package_index', 'package_code']].drop_duplicates()
    
    pd_document = document[((document.document_problem == 'both') | (document.document_problem == problem)) & \
                           ((document.document_stacking == 'both') | \
                           (document.document_stacking == \
                            meta_package[meta_package.meta_package_index == 'STACK']\
                            ['meta_package_valid'].tolist()[0]\
                           )) & \
                           ((document.document_keras == 'both') | \
                           (document.document_keras == \
                            meta_package[meta_package.meta_package_index == 'KER']\
                            ['meta_package_valid'].tolist()[0]\
                           )) & \
                           ((document.document_xgb == 'both') | \
                           (document.document_xgb == \
                            meta_package[meta_package.meta_package_index == 'XGB']\
                            ['meta_package_valid'].tolist()[0]\
                           )) \
                          ].merge(meta_package[meta_package.meta_package_valid == True], \
                                               left_on  = 'meta_package_index', \
                                               right_on = 'meta_package_index', \
                                               how = 'inner') \
                          [['sort_key', 'title', 'text', 'code']].sort_values('sort_key') \
                          [['title', 'text', 'code']].drop_duplicates()
    
    return pd_pk_import, pd_pk_from, pd_level_0, pd_document, pd_tree

def load_package(nb, pd_pk_import, pd_pk_from):
    text = "## Loading main packages "
    nb['cells'].append(nbf.v4.new_markdown_cell(text))
    
    string = '' 
    for index, row in pd_pk_import.iterrows(): 
        if row[2] == '*':
           string = string + "from " + str(row[1]) + " import " +  str(row[2]) + "\n"
        elif row[2] != 'None': 
           string = string + "import " + str(row[1]) + " as " + str(row[2]) + "\n" 
        else:
           string = string + "import " + str(row[1]) + "\n"
        if row[3] != 'None':
           string = string + str(row[3]) + "\n"
        
    for index, row in pd_pk_from.iterrows():
        string = string + "from " + str(row[1]) + " import " +  str(row[2]) + "\n"
        
    code = string
    nb['cells'].append(nbf.v4.new_code_cell(code))
    
    return nb

def keras_nn_class(stacking):
    code_stack = "def K_Class(X=X, y=y): \n" + \
                 "    keras.backend.clear_session() \n" + \
                 "#   neural network architecture: start \n" + \
                 "    model = Sequential() \n" + \
                 "    model.add(Dense(len(X.columns.tolist()) + len(df[target_col].unique()) + 2, \n" + \
                 "              input_dim=len(X.columns.tolist()), activation='relu')) \n" + \
                 "    model.add(Dense(len(df[target_col].unique()), activation='softmax')) \n" + \
                 "#   neural network architecture: end   \n" + \
                 "    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])\n" + \
                 "    return model\n" + \
                 "#   Keras training parameters: epoch and batch_size \n" + \
                 "K_C = KerasClassifier(build_fn=K_Class, epochs=200, batch_size=5, verbose=0) \n" + \
                 "K_C._estimator_type = 'classifier' "
    code_simpl = "keras.backend.clear_session() \n" + \
                 "#   neural network architecture: start \n" + \
                 "model = Sequential() \n" + \
                 "model.add(Dense(len(X.columns.tolist()) + len(df[target_col].unique()) + 2, \n" + \
                 "          input_dim=len(X.columns.tolist()), activation='relu')) \n" + \
                 "model.add(BatchNormalization()) \n" + \
                 "model.add(Dense(len(df[target_col].unique()), activation='softmax')) \n" + \
                 "#   neural network architecture: end   \n" + \
                 "model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])"
    if stacking:
       code = code_stack
    else:
       code = code_simpl 
    return code

def keras_nn_regre(stacking):
    code_stack = "def K_Regre(X=X, y=y): \n" + \
                 "    keras.backend.clear_session()\n" + \
                 "#   neural network architecture: start  \n" + \
                 "    model = Sequential() \n" + \
                 "    model.add(Dense(len(X.columns.tolist()) + 1 + 2, input_dim=len(X.columns.tolist()), \n" + \
                 "              activation='relu')) \n" + \
                 "#   model.add(Dense(len(X.columns.tolist()) + 1 + 2, activation='relu')) \n" + \
                 "    model.add(Dense(1)) \n" + \
                 "    model.compile(loss='mean_squared_error', optimizer='adam') \n" + \
                 "#   neural network architecture: end   \n" + \
                 "    return model  \n" + \
                 "#   Keras training parameters: epoch and batch_size \n" + \
                 "K_R = KerasRegressor(build_fn=K_Regre, epochs=200, batch_size=5, verbose=0) \n" + \
                 "K_R._estimator_type = 'regressor'"
    code_simpl = "keras.backend.clear_session()\n" + \
                 "#   neural network architecture: start  \n" + \
                 "model = Sequential() \n" + \
                 "model.add(Dense(len(X.columns.tolist()) + 1 + 2, input_dim=len(X.columns.tolist()), \n" + \
                 "          activation='relu')) \n" + \
                 "model.add(BatchNormalization()) \n" + \
                 "#   model.add(Dense(len(X.columns.tolist()) + 1 + 2, activation='relu')) \n" + \
                 "model.add(Dense(1)) \n" + \
                 "model.compile(loss='mean_squared_error', optimizer='adam')"
    if stacking:
       code = code_stack
    else:
       code = code_simpl 
    return code
    
def level_0(pd_level_0):
       string = "level_0 = [ \n"
       for index, row in pd_level_0.iterrows():
           string = string +  "          ( '" + str(row[0]) + "' , "  + str(row[1]) +  " ), \n"  
       string = string + "          ]"  
       return string

def list_model(pd_level_0):
       string = ""
       for index, row in pd_level_0.iterrows():
           if (row[1] != 'K_C') & (row[1] != 'K_R'): 
              string = string + "# " + str(row[1]) + "\n"  
       return string    

def generate(problem_type, stacking, data_size, with_keras, with_xgb, yb, seaborn, file, target_col,\
             threshold_NaN, threshold_cat, threshold_Z, output):
    user_drop_cols=[]
    nb = analyze(problem_type, stacking, data_size, with_keras, with_xgb, yb, seaborn, file, target_col,\
                  user_drop_cols, threshold_NaN, threshold_cat, threshold_Z)
    fname = output + '.ipynb'
    with open(fname, 'w') as f:
         nbf.write(nb, f)
            
# GUI
caption_fc = widgets.Label(value='Select your input file:')
fc = FileChooser('./')
file = widgets.VBox([caption_fc, fc])

caption_problem_type = widgets.Label(value='Select your problem type:')
problem_type = widgets.RadioButtons(
                options=['classification', 'regression'],
                description='Problem type:',
                disabled=False
                )
problem = widgets.VBox([caption_problem_type, problem_type])

caption_data_size = widgets.Label(value='Select your data size:')
data_size = widgets.RadioButtons(
                options=['small', 'large'],
                description='Data size:',
                disabled=False
                )
data = widgets.VBox([caption_data_size, data_size])

caption_option = widgets.Label(value='Select your options:')
model_caption_option = widgets.Label(value='Models:')
stacking = widgets.Checkbox(
                value=False,
                description='Stacking',
                disabled=False,
                indent=False
                )

keras = widgets.Checkbox(
                value=False,
                description='Keras',
                disabled=False,
                indent=False
                )

xgboost = widgets.Checkbox(
                value=False,
                description='XGBoost',
                disabled=False,
                indent=False
                )
model_option = widgets.VBox([model_caption_option, stacking, keras, xgboost])

visualizer_caption_option = widgets.Label(value='Visualizers:')
yb = widgets.Checkbox(
                value=True,
                description='Yellow bricks',
                disabled=False,
                indent=False
                )

seaborn = widgets.Checkbox(
                value=False,
                description='Seaborn',
                disabled=False,
                indent=False
                )
visualizer_option = widgets.VBox([visualizer_caption_option, yb, seaborn])

option = widgets.VBox([caption_option, widgets.HBox([model_option, visualizer_option])])

caption_target = widgets.Label(value='Enter target name:')
target_cl = widgets.Text(
                value='column name',
                placeholder='Type something',
                description='Target:',
                disabled=False   
                )
target = widgets.VBox([caption_target, target_cl]) 

caption_threshold = widgets.Label(value='Fix your thresholds:')
threshold_NaN = widgets.FloatSlider(
                value=0.5,
                min=0,
                max=1,
                step=0.03,
                description='Th. NaN:',
                disabled=False,
                continuous_update=False,
                orientation='horizontal',
                readout=True,
                readout_format='.1f',
                )

threshold_cat = widgets.IntText(
                value=5,
                description='Th. Cat:',
                disabled=False
                )

threshold_Z = widgets.FloatSlider(
                value=3.0,
                min=0,
                max=10,
                step=0.1,
                description='Th. Z:',
                disabled=False,
                continuous_update=False,
                orientation='horizontal',
                readout=True,
                readout_format='.1f',
                )
threshold = widgets.VBox([caption_threshold,threshold_cat, threshold_NaN, threshold_Z])

caption_output_file = widgets.Label(value='Enter output file name:')
output = widgets.Text(
                value='output file',
                placeholder='Type something',
                description='Output:',
                disabled=False   
                )

run = widgets.Button(
                description='Generate',
                disabled=False,
                button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                tooltip='Run',
                icon=''
                )
generator = widgets.VBox([caption_output_file, output, run])

def on_button_clicked(b, problem_type, stacking, data_size, keras, xgboost, fc, yb,\
                      seaborn, target, threshold_NaN, threshold_cat, threshold_Z, output):

    generate(problem_type.value, stacking.value, data_size.value, keras.value, xgboost.value, yb.value,\
             seaborn.value, fc.selected, target_cl.value, threshold_NaN.value, threshold_cat.value,\
             threshold_Z.value, output.value)

run.on_click(functools.partial(on_button_clicked, problem_type=problem_type, stacking=stacking,\
                               data_size=data_size,keras=keras, xgboost=xgboost, yb=yb,\
                               seaborn=seaborn,  fc=fc, target=target, threshold_NaN=threshold_NaN,\
                               threshold_cat=threshold_cat, threshold_Z=threshold_Z, output=output))

EZS_gui = widgets.VBox([file, target, problem, data, option, threshold, generator])