import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
from nipype.workflows.fmri.fsl.estimate import create_modelfit_workflow, create_fixed_effects_flow
from gilles_workflows import create_fdr_threshold_workflow

def get_session_info(subject_id, run, shift=0):
    import pandas
    import numpy as np
    from nipype.interfaces.base import Bunch
    
    df = pandas.read_pickle('/home/gdholla1/data/simon_amsterdam/behavior/all_data.pandas')

    df = df[(df.subject_id == subject_id) & (df.run == run)]
    df['onset'] += shift

    onsets_left_congruent = df[(df.stimulus_location == 'left') & (df.congruency == 'congruent')].onset.tolist()
    onsets_left_incongruent = df[(df.stimulus_location == 'left') & (df.congruency == 'incongruent')].onset.tolist()

    onsets_right_congruent = df[(df.stimulus_location == 'right') & (df.congruency == 'congruent')].onset.tolist()
    onsets_right_incongruent = df[(df.stimulus_location == 'right') & (df.congruency == 'incongruent')].onset.tolist()

    onsets_slow = df[df.slow == 'slow'].onset.tolist()
    onsets_error = df[df.correct == False].onset.tolist()

    info = Bunch(conditions=['left_congruent',
                          'left_incongruent',
                          'right_congruent',
                            'right_incongruent',
                            'slow',
                            'error'],
              onsets=[onsets_left_congruent,
                      onsets_left_incongruent,
                      onsets_right_congruent,
                      onsets_right_incongruent,
                      onsets_slow,
                      onsets_error],
              durations=[[1]] * 6)
    
    return info



meta_workflow = pe.Workflow(name='fit_puck_visual', base_dir='/home/gdholla1/workflow_folders/')


modelfit_workflow = create_modelfit_workflow(name='modelfit_puck_visual')

modelfit_workflow.base_dir = '/home/gdholla1/workflow_folders/'
modelfit_workflow.inputs.inputspec.bases = {'dgamma': {'derivs': True}}
modelfit_workflow.inputs.inputspec.contrasts = [('task', 'T', ['task'], [1.0])]
modelfit_workflow.inputs.inputspec.film_threshold = 1000
modelfit_workflow.inputs.inputspec.interscan_interval = 2.5
modelfit_workflow.inputs.inputspec.model_serial_correlations = True

modelfit_workflow.inputs.inputspec.contrasts = [('incongruent > congruent', 'T', 
                                                 ['left_incongruent', 'right_incongruent', 'left_congruent', 'right_congruent'], 
                                                 [1.0, 1.0, -1.0, -1.0]),
                                                ('congruent > incongruent', 'T',
                                                 ['left_congruent', 'right_congruent', 'left_incongruent', 'right_incongruent'], 
                                                 [1.0, 1.0, -1.80, -1.0]),
                                                 ('face > house', 'T',
                                                 ['left_congruent', 'right_incongruent', 'left_incongruent', 'right_congruent'], 
                                                 [1.0, 1.0, -1.0, -1.0]), 
                                                 ('house > face', 'T',
                                                 ['left_incongruent', 'right_congruent', 'left_congruent', 'right_incongruent'], 
                                                 [1.0, 1.0, -1.0, -1.0]),                                                 
                                                 ('congruent left (face) > congruent right (house)', 'T',
                                                 ['left_congruent', 'right_congruent'],
                                                 [1.0, -1.0]),
                                                 ('incongruent left (house) > incongruent right (face)', 'T',
                                                 ['left_incongruent', 'right_incongruent'],
                                                 [1.0, -1.0]),
                                                 ('congruent left (face) > incongruent right (face)', 'T',
                                                 ['left_incongruent', 'right_incongruent'],
                                                 [1.0, -1.0]),
                                                 ('congruent right (house) > incongruent left (house)', 'T',
                                                 ['right_incongruent', 'left_incongruent'],
                                                 [1.0, -1.0]),
                                                 ('error > baseline', 'T',
                                                 ['error'],
                                                 [1.0]),
                                                 ('slow > baseline', 'T',
                                                 ['slow'],
                                                 [1.0])                                               ]


identity = pe.Node(util.IdentityInterface(fields=['subject_id', 'run']),
                                  name='identity')

identity.iterables = [('subject_id', [1])]
identity.inputs.run = [1,2,3, 4]

templates = {'epi':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/highpassed_files/_subject_id_{subject_id}/_fwhm_5.0/_addmean*/run{run}_dtype_mcf_mask_smooth_mask_gms_tempfilt_maths.nii.gz',
            'mask':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/mask/_subject_id_{subject_id}/_fwhm_5.0/_dilatemask0/run1_dtype_mcf_bet_thresh_dil.nii.gz'}

selector = pe.MapNode(nio.SelectFiles(templates), iterfield=['run'], name='selector')

def get_session_info(subject_id, run, shift=0):
    import pandas
    import numpy as np
    from nipype.interfaces.base import Bunch
    
    df = pandas.read_pickle('/home/gdholla1/data/simon_amsterdam/behavior/all_data.pandas')

    df = df[(df.subject_id == subject_id) & (df.run == run)]
    df['onset'] += shift

    onsets_left_congruent = df[(df.stimulus_location == 'left') & (df.congruency == 'congruent')].onset.tolist()
    onsets_left_incongruent = df[(df.stimulus_location == 'left') & (df.congruency == 'incongruent')].onset.tolist()

    onsets_right_congruent = df[(df.stimulus_location == 'right') & (df.congruency == 'congruent')].onset.tolist()
    onsets_right_incongruent = df[(df.stimulus_location == 'right') & (df.congruency == 'incongruent')].onset.tolist()

    onsets_slow = df[df.slow == 'slow'].onset.tolist()
    onsets_error = df[df.correct == False].onset.tolist()

    info = Bunch(conditions=['left_congruent',
                          'left_incongruent',
                          'right_congruent',
                            'right_incongruent',
                            'slow',
                            'error'],
              onsets=[onsets_left_congruent,
                      onsets_left_incongruent,
                      onsets_right_congruent,
                      onsets_right_incongruent,
                      onsets_slow,
                      onsets_error],
              durations=[[1]] * 6)
    
    return info


session_info_getter = pe.MapNode(util.Function(function=get_session_info,
                                     input_names=['subject_id', 'run', 'shift'],
                                     output_names=['session_info']),
                       iterfield=['run'],
                       name='session_info_getter')
session_info_getter.iterables = [('shift', [-2.0])]


meta_workflow.connect([(identity, selector,
                   [('subject_id', 'subject_id'),
                    ('run', 'run')])])

meta_workflow.connect([(identity, session_info_getter,
                   [('subject_id', 'subject_id'),
                    ('run', 'run')])])

from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import fsl

specifymodel = pe.Node(SpecifyModel(), name='specifymodel')
specifymodel.inputs.input_units = 'secs'
specifymodel.inputs.time_repetition = 2
specifymodel.inputs.high_pass_filter_cutoff = 128. / (2. * 2.)


meta_workflow.connect([
                  (selector, modelfit_workflow,
                   [('epi', 'inputspec.functional_data')]),
                  (session_info_getter, specifymodel,
                   [('session_info', 'subject_info'),]),
                  (selector, specifymodel,
                  [('epi', 'functional_runs'),]),
                  (specifymodel, modelfit_workflow,
                   [('session_info', 'inputspec.session_info'),])
                  ])

fixedfx = create_fixed_effects_flow()
def get_first(list_in):
    return list_in[0]

meta_workflow.connect(selector, ('mask', get_first), fixedfx, 'flameo.mask_file')

def num_copes(files):
    return len(files)

def transpose_copes(copes):    
    import numpy as np
    return np.array(copes).T.tolist()

meta_workflow.connect([(modelfit_workflow, fixedfx,
                   [(('outputspec.copes', transpose_copes), 'inputspec.copes'),
                    (('outputspec.varcopes', transpose_copes), 'inputspec.varcopes'),
                    ('outputspec.dof_file', 'inputspec.dof_files'),
                    (('outputspec.copes', num_copes), 'l2model.num_copes')])])


ztopval = pe.MapNode(interface=fsl.ImageMaths(op_string='-ztop',
                                              suffix='_pval'),
                     nested=True,
                     iterfield=['in_file'],
                     name='ztop',)

fdr_workflow = create_fdr_threshold_workflow()

meta_workflow.connect([
                  (fixedfx, ztopval,
                   [('outputspec.zstats', 'in_file'),]),
                  (fixedfx, fdr_workflow,
                   [('outputspec.zstats', 'inputspec.z_stats'),]),
                  (ztopval, fdr_workflow,
                   [('out_file', 'inputspec.p_values'),]),
                  (selector, fdr_workflow,
                   [(('mask', get_first), 'inputspec.mask'),]),
                  ])

ds = pe.Node(nio.DataSink(), name='datasink')
ds.inputs.base_directory = '/home/gdholla1/data/simon_amsterdam/modelfit_visual'
ds.inputs.regexp_substitutions = [('/_flameo([0-9]+)/([a-z0-9_]+).nii.gz', '/\\2_contrast\\1.nii.gz'),
        ('/_masker([0-9]+)/zstat1_masked.nii.gz', '/thresholded_zstat_contrast\\1.nii.gz'),]

meta_workflow.connect(fixedfx, 'outputspec.zstats', ds, 'zstats')
meta_workflow.connect(fixedfx, 'outputspec.copes', ds, 'level2_copes')
meta_workflow.connect(fixedfx, 'outputspec.varcopes', ds, 'level2_varcopes')
meta_workflow.connect(fixedfx, 'flameo.tdof', ds, 'level2_tdof')
meta_workflow.connect(fdr_workflow, 'outputspec.thresholded_z_stats', ds, 'thresholded_z_stats')

meta_workflow.run()
#meta_workflow.run(plugin='MultiProc', plugin_args={'n_procs':4})

