#This is the code by Gilles, which should work. We had this running for subject 304.
#Changes: 1. zstats add to list (merge) linked to to_target
#         2. modality iterable
#         3. iterate across all subjects
#         4. V8  - deals with lateralized/lateralized_correct/classic design.
#         5. V9 - add contrast Cong > Incong to Lateralize/Correct
         
from gilles_workflows import create_fsl_ants_registration_workflow
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
from nipype.interfaces import ants


subject_ids = [1, 2]

#modality = ['tactile', 'visual']
modality = ['visual']
contrast = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

identity = pe.Node(util.IdentityInterface(fields=['subject_id']), name='identity')
identity.iterables = [('subject_id', subject_ids)]



#identitynode

templates = {'anatomy': '/home/gdholla1/data/simon_amsterdam/clean/S{subject_id}/T1w.nii',
            'functional_mean' : '/home/gdholla1/data/simon_amsterdam/preprocessing_results/mean/_subject_id_{subject_id}/_fwhm_0.0/run1_dtype_mcf_mask_gms_mean.nii.gz',}


templates_transformation = {'level2_copes':'/home/gdholla1/data/simon_amsterdam/modelfit_{modality}/level2_copes/_subject_id_{subject_id}/_shift_-2.0/cope1_contrast{contrast}.nii.gz',
            'level2_tdof':'/home/gdholla1/data/simon_amsterdam/modelfit_{modality}/level2_tdof/_subject_id_{subject_id}/_shift_-2.0/tdof_t1_contrast{contrast}.nii.gz',
            'level2_varcops':'/home/gdholla1/data/simon_amsterdam/modelfit_{modality}/level2_varcopes/_subject_id_{subject_id}/_shift_-2.0/varcope1_contrast{contrast}.nii.gz',
            'zstats':'/home/gdholla1/data/simon_amsterdam/modelfit_{modality}/zstats/_subject_id_{subject_id}/_shift_-2.0/zstat1_contrast{contrast}.nii.gz'}

workflow = create_fsl_ants_registration_workflow(name='registration_simon_amsterdam')
workflow.base_dir = '/home/gdholla1/workflow_folders/'

selector = pe.Node(nio.SelectFiles(templates), name='selector')
workflow.connect(identity, 'subject_id', selector, 'subject_id')

selector_transformation = pe.Node(nio.SelectFiles(templates_transformation), name='selector_transformation')
selector_transformation.iterables = [('modality', modality), ('contrast', contrast)]
workflow.connect(identity, 'subject_id', selector_transformation, 'subject_id')

merger = pe.Node(util.Merge(4), name='merger')

workflow.connect(selector_transformation, 'level2_copes', merger, 'in1')
workflow.connect(selector_transformation, 'level2_tdof', merger, 'in2')
workflow.connect(selector_transformation, 'level2_varcops', merger, 'in3')
workflow.connect(selector_transformation, 'zstats', merger, 'in4')

bet = pe.Node(fsl.BET(), name='bet')

workflow.connect(selector, 'anatomy', bet, 'in_file')

workflow.connect(bet, 'out_file', workflow.get_node('inputspec'), 'anatomical_mp2rage')
workflow.connect(bet, 'out_file', workflow.get_node('inputspec'), 'anatomical_t1_weighted')
workflow.connect(selector, 'functional_mean', workflow.get_node('inputspec'), 'mean_epi')
workflow.connect(merger, 'out' , workflow.get_node('inputspec'), 'to_target')

zstats_to_struct = pe.Node(ants.ApplyTransforms(), name='zstats_to_struct')
workflow.connect(selector_transformation, 'zstats', zstats_to_struct, 'input_image')
workflow.connect(selector, 'anatomy', zstats_to_struct, 'reference_image')
workflow.connect(workflow.get_node('outputspec'), 'epi2anat_transform', zstats_to_struct, 'transforms')

ds = pe.Node(nio.DataSink(), name='datasink')
ds.inputs.base_directory = '/home/gdholla1/data/simon_amsterdam/registration'

workflow.connect(workflow.get_node('outputspec'), 'warped_image', ds, 'struct_in_target')
workflow.connect(workflow.get_node('outputspec'), 'epi_in_anat_space', ds, 'epi_in_struct')
workflow.connect(workflow.get_node('outputspec'), 'composite_transform', ds, 'anat2mni_transform')
workflow.connect(workflow.get_node('outputspec'), 'inverse_composite_transform', ds, 'mni2anat_transform')
workflow.connect(workflow.get_node('outputspec'), 'epi2anat_transform', ds, 'epi2anat_transform')
workflow.connect(zstats_to_struct, 'output_image', ds, 'zstats_in_struct')
workflow.connect(workflow.get_node('outputspec'), 'transformed_target_space', ds, 'stats_in_mni_space')

workflow.inputs.inputspec.target='/usr/share/fsl/5.0/data/standard/MNI152_T1_1mm_brain.nii.gz'

workflow.run()
#workflow.run(plugin='MultiProc', plugin_args={'n_procs':6})

