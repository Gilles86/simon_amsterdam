from nipype.interfaces import fsl
from nipype.interfaces import io as nio
from nipype.interfaces import ants
from nipype.interfaces import utility as util

import nipype.pipeline.engine as pe

workflow = pe.Workflow(name='transform_mni_masks', base_dir='/home/gdholla1/workflow_folders/')

templates = {'epi2anat':'/home/gdholla1/data/simon_amsterdam/registration/epi2anat_transform/_subject_id_{subject_id}/affine.txt',
             'mni2anat':'/home/gdholla1/data/simon_amsterdam/registration/mni2anat_transform/_subject_id_{subject_id}/transformInverseComposite.h5',
             'mask':'/home/gdholla1/data/simon/masks_mni/{mask_str}.nii.gz',
             'mean':'/home/gdholla1/data/simon_amsterdam/preprocessing_results/mean/_subject_id_{subject_id}/_fwhm_0.0/run1_dtype_mcf_mask_gms_mean.nii.gz'}

selector = pe.MapNode(nio.SelectFiles(templates), iterfield=['mask_str'], name='selector')

subject_ids = [1, 2]

selector.iterables = [('subject_id', subject_ids)]

selector.inputs.mask_str = ['V1', 'V2', 'V3', 'V4', 'V5', 'S1', 'S2', 'V','S']
#selector.inputs.mask_str = ['Neubert_1mm_44d_L', 'Neubert_1mm_44d_R', 'Neubert_1mm_44v_L', 'Neubert_1mm_44v_R','Neubert_1mm_45A_L', 'Neubert_1mm_45A_R', 'Neubert_1mm_Left_M1', 'Neubert_1mm_Right_M1', 'V1_L', 'V1_R',]
selector.inputs.mask_str = [u'thalamus_primary_motor', u'thalamus_sensory', u'thalamus_occipital', u'thalamus_pre-frontal', u'thalamus_pre-motor', u'thalamus_posterior_parietal', u'thalamus_temporal', 'thalamus_all']

#selector.inputs.mask_str = ['subthalamic_nucleus_l', 'subthalamic_nucleus_r']

transform_merger = pe.MapNode(util.Merge(2), iterfield=['in1', 'in2'], name='transform_merger')

workflow.connect(selector, 'mni2anat', transform_merger, 'in1')
workflow.connect(selector, 'epi2anat', transform_merger, 'in2')


flirt = pe.MapNode(fsl.ApplyXfm(), iterfield=['in_file'], name='flirt')
flirt.inputs.reference = '/usr/share/fsl/data/standard/MNI152_T1_1mm.nii.gz'
flirt.inputs.in_matrix_file = '/usr/share/fsl/5.0/etc/flirtsch/ident.mat'

workflow.connect(selector, 'mask', flirt, 'in_file')


applier = pe.MapNode(ants.ApplyTransforms(), iterfield=['input_image', 'reference_image', 'transforms'], name='applier')
applier.inputs.invert_transform_flags = [False, True]
applier.inputs.interpolation = 'NearestNeighbor'

workflow.connect(transform_merger, 'out', applier, 'transforms')
workflow.connect(flirt, 'out_file', applier, 'input_image')
workflow.connect(selector, 'mean', applier, 'reference_image')

ds = pe.Node(nio.DataSink(base_directory='/home/gdholla1/data/simon_amsterdam'), name='datasink')
ds.inputs.regexp_substitutions = [('/_applier[0-9]+/', '/')]


workflow.connect(applier, 'output_image', ds, 'masks_epi_space')

workflow.run()
