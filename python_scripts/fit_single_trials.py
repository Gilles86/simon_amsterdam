import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
from nipype.workflows.fmri.fsl.estimate import create_modelfit_workflow, create_fixed_effects_flow
from gilles_workflows import create_fdr_threshold_workflow
import numpy as np

def get_session_info(subject_id, run, shift=0):
    import pandas
    import numpy as np
    from nipype.interfaces.base import Bunch
    
    df = pandas.read_pickle('/home/gdholla1/data/simon_amsterdam/behavior/all_data.pandas')

    df = df[(df.subject_id == subject_id) & (df.run == run)]
    df['onset'] += shift

    onsets = [[e] for e in df.onset.tolist()]


    info = Bunch(conditions=['trial %d' % i for i in np.arange(1, len(onsets) + 1)],
              onsets=onsets,
              durations=[[1]] * len(onsets))
    
    return info



meta_workflow = pe.Workflow(name='fit_puck_single_trials', base_dir='/home/gdholla1/workflow_folders/')


modelfit_workflow = create_modelfit_workflow(name='modelfit_puck_single_trials')

modelfit_workflow.base_dir = '/home/gdholla1/workflow_folders/'
modelfit_workflow.inputs.inputspec.bases = {'dgamma': {'derivs': False}}
modelfit_workflow.inputs.inputspec.film_threshold = 1000
modelfit_workflow.inputs.inputspec.interscan_interval = 2.5
modelfit_workflow.inputs.inputspec.model_serial_correlations = True

contrasts = [('trial %d' % i, 'T', ['trial %d' % i],  [1.0]) for i in np.arange(1, 55)]

modelfit_workflow.inputs.inputspec.contrasts =  contrasts


identity = pe.Node(util.IdentityInterface(fields=['subject_id', 'run']),
                                  name='identity')

identity.iterables = [('subject_id', [2])]
identity.inputs.run = [1,2,3,4, 5,6,7,8]

templates = {'epi':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/highpassed_files/_subject_id_{subject_id}/_fwhm_0.0/_addmean*/run{run}_dtype_mcf_mask_*.nii.gz',
            'mask':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/mask/_subject_id_{subject_id}/_fwhm_0.0/_dilatemask0/run1_dtype_mcf_bet_thresh_dil.nii.gz',
            'realignment_parameters':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/motion_parameters/_subject_id_1/_fwhm_0.0/_realign*/run{run}*.par'}

selector = pe.MapNode(nio.SelectFiles(templates), iterfield=['run'], name='selector')


session_info_getter = pe.MapNode(util.Function(function=get_session_info,
                                     input_names=['subject_id', 'run', 'shift'],
                                     output_names=['session_info']),
                       iterfield=['run'],
                       name='session_info_getter')
session_info_getter.iterables = [('shift', [-2.0, 0.0])]


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
specifymodel.inputs.time_repetition = 2.5
specifymodel.inputs.high_pass_filter_cutoff = 128. / (2.5 * 2.)


meta_workflow.connect([
                  (selector, modelfit_workflow,
                   [('epi', 'inputspec.functional_data')]),
                  (session_info_getter, specifymodel,
                   [('session_info', 'subject_info'),]),
                  (selector, specifymodel,
                  [('epi', 'functional_runs'),]),
                  (selector, specifymodel,
                  [('realignment_parameters', 'realignment_parameters'),]),
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
ds.inputs.base_directory = '/home/gdholla1/data/simon_amsterdam/modelfit_single_trials'
ds.inputs.regexp_substitutions = [('/_flameo([0-9]+)/([a-z0-9_]+).nii.gz', '/\\2_contrast\\1.nii.gz'),
        ('/_masker([0-9]+)/zstat1_masked.nii.gz', '/thresholded_zstat_contrast\\1.nii.gz'),]

meta_workflow.connect(modelfit_workflow, 'outputspec.zfiles', ds, 'single_trial_z_stats')
meta_workflow.connect(modelfit_workflow, 'outputspec.copes', ds, 'single_trial_copes')
meta_workflow.connect(modelfit_workflow, 'outputspec.parameter_estimates', ds, 'single_trial_parameter_estimates')

#meta_workflow.run()
meta_workflow.run(plugin='MultiProc', plugin_args={'n_procs':4})

