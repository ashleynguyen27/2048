
# coding: utf-8

# In[1]:

import os
import sys
import traceback
from dipy.tracking import utils
import nibabel as nib
import numpy as np
from nibabel import trackvis
from responsestuff.responsestuff.autoresponse import fskeys
import scipy
import json
import glob
from shutil import copy


# In[2]:


def construct_network(subjid):
	config_path = open("config.json")
	config_dict = dict(json.load(config_path))
	track_dir = config_dict["track_dir"]
	label_dir = config_dict["label_dir"]
	streamline_file = "{}/{}/prob-localtrack-clean.trk".format(track_dir, subjid)
	label_file = "{}/{}/aseg_to_fa_aff.nii.gz".format(label_dir, subjid)

	save_dir = config_dict["save_dir"]
	save_file = "{}/{}/network/network_multiplicities.json".format(save_dir, subjid)


	# In[3]:

	trk, hdr = trackvis.read(streamline_file)

	streamlines = [i[0] for i in trk] # "strips" streamlines (only extracts points)
	trk_save = [(i, None, None) for i in streamlines] # unstripped version to save if needed
	assert str(hdr['voxel_order']).lower() == "las" # NOT SURE?
	vs = hdr['voxel_size'] # NOT SURE?
	aff = np.diag([vs[0], vs[1], vs[2], 1]) # NOT SURE?
	aff[:, 3] = np.dot(aff, [.5, .5, .5, 1]) # NOT SURE?


	# In[4]:

	ctx_array = fskeys['ctx'] # labels that belong to the cerebral cortex
	deep_grey_array = fskeys['deep gray'] # labels that belong to grey matter

	aseg = nib.load(label_file).get_data()
	gray_region = (np.in1d(aseg, fskeys['ctx']) |
	               np.in1d(aseg, fskeys['deep gray']))
	gray_region.shape = aseg.shape # "unlinearize": convert linear to 3D shape
	aseg_grey = aseg * gray_region # mask all non-grey matter regions in this mapping


	# In[5]:

	labels, lt = utils.reduce_labels(aseg_grey)

	mat, mapping = utils.connectivity_matrix(streamlines, labels,
	                                             affine=aff,
	                                             return_mapping=True,
	                                             mapping_as_streamlines=True)


	# In[6]:

	stream_multiplicity_map = {}
	for val in mapping:
	    modified_key = lt[val[0]], lt[val[1]]
	    # print(modified_key, len(mapping[val]))
	    stream_multiplicity_map[str(modified_key)] = len(mapping[val])

	save_directory = "{}/{}/network".format(save_dir, subjid)
	if not os.path.exists(save_directory):
	    os.makedirs(save_directory)
	    
	f = open(save_file, 'w')
	json.dump(stream_multiplicity_map, f)
	f.close()

def copy_over_json(subjid):
	json_path = os.path.join("/projects/ps-henrylab/hcp/hcp_structural/tracking/", subjid, "network/network_multiplicities.json")
	target_path = os.path.join("/home/amitakul/scripts/networks", "{0}-network-multiplicities.json".format(subjid))
	copy(json_path, target_path)
if __name__ == "__main__":
	for path in glob.glob("/projects/ps-henrylab/hcp/hcp_structural/tracking/*"):
		subjid = path.split("/")[-1]
		if os.path.exists(os.path.join(path, "network/network_multiplicities.json")):
			print("already computed network for {0}".format(subjid))
			copy_over_json(subjid)
		elif os.path.isdir(path):
			print('constructing network for {0}'.format(subjid))
			try:
				construct_network(subjid)
			except Error as e:
				print("ERROR: could not construct network for {0} because {1}".format(subjid, e))
			copy_over_json(subjid)
		else:
			print("ignoring the following path: {0}".format(path))
