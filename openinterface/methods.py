from simtk import unit
import numpy as np

def connectivity(item, receptor_selection, ligand_selection, contact_type='CAs', threshold=1.2*unit.nanometers):

    cmap, labels_receptor, labels_ligand = contact_map(item, receptor_selection, ligand_selection,
                                                      contact_type=contact_type, threshold=threshold)

    connectivity_receptor = cmap.sum(axis=2)
    connectivity_ligand = cmap.sum(axis=1)

    return connectivity_receptor, connectivity_ligand, labels_receptor, labels_ligand

def nearby_connectivity(item, receptor_selection, ligand_selection, contact_type='CAs', threshold=0.6*unit.nanometers):

    cmap, labels_receptor, labels_ligand = contact_map(item, receptor_selection, ligand_selection,
                                                      contact_type=contact_type, threshold=threshold)

    connectivity_receptor = cmap.sum(axis=2)
    connectivity_ligand = cmap.sum(axis=1)

    return connectivity_receptor, connectivity_ligand, labels_receptor, labels_ligand


def contact_map(item, receptor_selection, ligand_selection, contact_type='CAs', threshold=1.2*unit.nanometers):

    from molsysmt import get, select, contact_map, info

    group_indices_receptor = get(item, target='group', selection=receptor_selection,
                                 group_index=True)

    group_indices_ligand = get(item, target='group', selection=ligand_selection,
                                 group_index=True)

    CA_indices_receptor = select(item, selection='atom_name=="CA" and group_index==@group_indices_receptor')

    CA_indices_ligand = select(item, selection='atom_name=="CA" and group_index==@group_indices_ligand')

    cmap = contact_map(item, selection_1=CA_indices_receptor, selection_2=CA_indices_ligand,
                       threshold=threshold)

    labels_receptor = info(item, target='group', indices=group_indices_receptor,
                           output='short_string')

    labels_ligand = info(item, target='group', indices=group_indices_ligand,
                         output='short_string')

    return cmap, labels_receptor, labels_ligand

def buried_factors (item, receptor_selection, ligand_selection, target='group'):

    from molsysmt import extract, get, info

    tmp_complex = item
    indices_receptor_in_complex = get(tmp_complex, target=target, selection=receptor_selection, index=True)
    indices_ligand_in_complex = get(tmp_complex, target=target, selection=ligand_selection, index=True)

    tmp_receptor = extract(item, selection=receptor_selection)
    tmp_ligand = extract(item, selection=ligand_selection)

    sasa_complex = sasa(item, target=target)._value
    sasa_receptor = sasa(tmp_receptor, target=target)._value
    sasa_ligand = sasa(tmp_ligand, target=target)._value

    n_frames = sasa_receptor.shape[0]
    n_elements_receptor = sasa_receptor.shape[1]
    n_elements_ligand = sasa_ligand.shape[1]

    buried_factors_receptor = np.zeros([n_frames, n_elements_receptor], dtype='float')

    for ll in range(n_frames):
        for ii in range(n_elements_receptor):
            jj = indices_receptor_in_complex[ii]
            if sasa_receptor[ll,ii] > 0.0:
                buried_factors_receptor[ll,ii] = (sasa_receptor[ll, ii] - sasa_complex[ll, jj])/sasa_receptor[ll, ii]

    buried_factors_ligand = np.zeros([n_frames, n_elements_ligand], dtype='float')

    for ll in range(n_frames):
        for ii in range(n_elements_ligand):
            jj = indices_ligand_in_complex[ii]
            if sasa_ligand[ll,ii] > 0.0:
                buried_factors_ligand[ll, ii] = (sasa_ligand[ll, ii] - sasa_complex[ll, jj])/sasa_ligand[ll, ii]

    labels_receptor = info(item, target=target, selection=receptor_selection, output='short_string')
    labels_ligand = info(item, target=target, selection=ligand_selection, output='short_string')

    return buried_factors_receptor, buried_factors_ligand, labels_receptor, labels_ligand

def sasa(item, selection='all', frame_indices='all', target='group', syntaxis='MolSysMT'):

    from molsysmt import sasa as molsysmt_sasa

    return molsysmt_sasa(item, selection=selection, frame_indices=frame_indices, target=target,
                        syntaxis=syntaxis)

def sasa_buried (item, receptor_selection, ligand_selection):

    from molsysmt import extract, get, info

    tmp_complex = item
    tmp_receptor = extract(item, selection=receptor_selection)
    tmp_ligand = extract(item, selection=ligand_selection)

    sasa_complex = sasa(item, target='atom').sum(axis=1)
    sasa_receptor = sasa(tmp_receptor, target='atom').sum(axis=1)
    sasa_ligand = sasa(tmp_ligand, target='atom').sum(axis=1)

    return sasa_receptor+sasa_ligand-sasa_complex

def contacting_residues (item, receptor_selection, ligand_selection):

    from molsysmt import extract, get, info
    from molsysmt import distance
    from numpy import where, unique
    from simtk.unit import angstroms
    from molsysmt.physchem import get_radii

    atom_indices_receptor = get(item, target='atom', selection=receptor_selection,
                                index=True)

    atom_indices_ligand = get(item, target='atom', selection=ligand_selection,
                              index=True)

    distances = distance(item, selection_1=atom_indices_receptor, selection_2=atom_indices_ligand)

    frame_index, indices_in_receptor, indices_in_ligand = where(distances < 4.1 * angstroms)

    vdw_atoms1 = get_radii(item, selection=atom_indices_receptor[indices_in_receptor], target='atom', radius_type='vdw')
    vdw_atoms2 = get_radii(item, selection=atom_indices_ligand[indices_in_ligand], target='atom', radius_type='vdw')

    list_contacting_receptor = []
    list_contacting_ligand = []

    for ii, jj, vdw_ii, vdw_jj  in zip(indices_in_receptor, indices_in_ligand, vdw_atoms1, vdw_atoms2):
        if distances[0,ii,jj] < (vdw_ii+vdw_jj+0.5*angstroms):
            list_contacting_receptor.append(ii)
            list_contacting_ligand.append(jj)

    list_contacting_atoms_receptor = atom_indices_receptor[unique(list_contacting_receptor)]
    list_contacting_atoms_ligand = atom_indices_ligand[unique(list_contacting_ligand)]

    list_contacting_residues_receptor = get(item, selection=list_contacting_atoms_receptor,
                                            group_index=True)

    list_contacting_residues_ligand = get(item, selection=list_contacting_atoms_ligand,
                                          group_index=True)

    list_contacting_residues_receptor = unique(list_contacting_residues_receptor)
    list_contacting_residues_ligand = unique(list_contacting_residues_ligand)


    return list_contacting_residues_receptor, list_contacting_residues_ligand

