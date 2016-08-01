from nipype.workflows.fmri.fsl import create_featreg_preproc
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.algorithms.misc import TSNR

workflow = create_featreg_preproc('preprocess_simon_amsterdam') #The default name is "featpreproc".
workflow.base_dir = '/home/gdholla1/workflow_folders'

templates = {'functional_runs':'/home/gdholla1/data/simon_amsterdam/clean/S{subject_id}/run*.nii'}

subject_ids = [2]

selector = pe.Node(nio.SelectFiles(templates), name='selector')
selector.iterables = [('subject_id', subject_ids)]

workflow.connect(selector, 'functional_runs', workflow.get_node('inputspec'), 'func' )

#workflow.inputs.inputspec.fwhm = 5
workflow.get_node('inputspec').iterables = [('fwhm', [0.0, 5.0])]
workflow.inputs.inputspec.highpass = True

ds = pe.Node(nio.DataSink(), name='datasink')
ds.inputs.base_directory = '/home/gdholla1/data/simon_amsterdam//preprocessing_results/'

workflow.connect(workflow.get_node('outputspec'), 'mean', ds, 'mean')
workflow.connect(workflow.get_node('outputspec'), 'highpassed_files', ds, 'highpassed_files')
workflow.connect(workflow.get_node('outputspec'), 'mask', ds, 'mask')
workflow.connect(workflow.get_node('outputspec'), 'motion_parameters', ds, 'motion_parameters')
workflow.connect(workflow.get_node('outputspec'), 'motion_plots', ds, 'motion_plots')

tsnr_node = pe.MapNode(TSNR(), iterfield=['in_file'], name='tsnr')
workflow.connect(workflow.get_node('outputspec'), 'realigned_files', tsnr_node, 'in_file')
workflow.connect(tsnr_node,  'tsnr_file', ds, 'tsnr')


workflow.write_graph()
#workflow.run()
workflow.run(plugin='MultiProc', plugin_args={'n_procs':2})
