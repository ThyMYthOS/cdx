#!/usr/bin/env python
##
# \addtogroup python_examples
# @{
# \addtogroup python_examples_example_01 example_01
# @{
#
# \file example-01.py
# \date April 13, 2017
# \author Frank Schubert
#
#   CDX Library
#
#
# The example can be run with:
#   python ./example-01.py
#   cdx-convert-continuous-to-discrete -e -b 0.1e-6 -a 0.1e-6 -s 1000e6 -i example-01.cdx -o example-01.cdd
#   cdx-display -i example-01.cdx
#
# If you would like to run this script with a CDX library version in your home directory, set e.g.
#
#   PYTHONPATH=~/workspace/cdx/trunk/python python ./example-01.py
#
# before calls to this script.

import matplotlib.pyplot as plt
import cmath
import numpy as np
import cdx.WriteContinuousDelayFile

# parameters:
cir_rate_Hz = 100.0

# satellite positions:
sat_pos_start_m = np.array([ [ 24000, -24000, 24000 ],
                             [ -24000, 24000, 12000 ] ])

nof_satellites = sat_pos_start_m.shape[0]

# satellite velocities matrix:
sat_vel_m_s = np.array([ [ 0, 0, 0],
                         [ 0, 0, 0] ])

# receiver start position:
rec_pos_start_m = np.array([ 0, 0, 0])
# receiver velocity vector:
receiver_velocity_m_s = np.array([ 5, 0, 0])

# reflector positions:
refl_pos_m = np.array([ [ 100, 10, -10 ],
                        [ -100, 10, -10 ]  ])

nof_scatterers = refl_pos_m.shape[0]

length_s = 5.0
nof_times = length_s * cir_rate_Hz
# all time instants:
times_s = np.linspace(0.0, length_s, nof_times)

print 'Simulation length: {} s, CIR rate: {} Hz, nof_satellites: {}, number of time instants to compute: {}'.format(length_s, cir_rate_Hz, nof_satellites, nof_times)

# setup CDX output file:
file_name = 'example-01.cdx'

# define the propagation parameters:
transmitter_frequency_Hz = 1.51e9
c0_m_s = 3e8
cir_rate_Hz = cir_rate_Hz
link_names = []
component_types = {}

for k in range(nof_satellites):
    link_name = 'satellite{}'.format(k)
    link_names.append(link_name)
    component_types[link_name] = {}
    component_types[link_name][0] = 'LOS'
    component_types[link_name][256] = 'scatterer'

cdx_file = cdx.WriteContinuousDelayFile.WriteContinuousDelayFile(file_name, c0_m_s,
                                                                 cir_rate_Hz, transmitter_frequency_Hz,
                                                                 link_names, component_types)

wave_length_m = c0_m_s / transmitter_frequency_Hz

for k, time in enumerate(times_s):
    # compute current receiver position:
    rec_pos_m = rec_pos_start_m + time * receiver_velocity_m_s

    # for all satellites:
    cirs = {}
    ref_delays = {}
    for n in range(nof_satellites):
        link_name = 'satellite{}'.format(n)

        # compute the actual satellite position...
        sat_pos_m = sat_pos_start_m[n, :] + time * sat_vel_m_s[n, :]
#         print 'sat_pos_start_m[n, :]', sat_pos_start_m[n, :], ', sat_pos_m: ', sat_pos_m, ', rec_pos_m: ', rec_pos_m, ', sat_pos_m - rec_pos_m', (sat_pos_m - rec_pos_m), 'np.linalg.norm(sat_pos_m - rec_pos_m)', np.linalg.norm(sat_pos_m - rec_pos_m)
        # ...and the distance from receiver to satellite:
        distance_satellite_receiver_m = np.linalg.norm(sat_pos_m - rec_pos_m)
        flight_time_satellite_receiver_s = distance_satellite_receiver_m / c0_m_s

        # compute the reference delay in s:
        ref_delays[link_name] = flight_time_satellite_receiver_s

        # prepare the CIR output: 1 + nof_scatterers: LOS + scatterers:
        cirs[link_name] = np.empty((1 + nof_scatterers,), dtype=cdx.WriteContinuousDelayFile.cir_dtype)

        # write LOS signal:
        cirs[link_name][0]['type'] = 0 # LOS type as set above
        cirs[link_name][0]['id'] = 0 # LOS type as set above
        cirs[link_name][0]['delay'] = 0.0

        receiver_to_satellite_vec = sat_pos_m - rec_pos_m
        receiver_to_satellite_unit_vec = receiver_to_satellite_vec / np.linalg.norm(receiver_to_satellite_vec)
        distance_change_receiver_to_satellite_m = np.dot(receiver_velocity_m_s, receiver_to_satellite_unit_vec) * 1.0 / cir_rate_Hz

        # LOS amplitude does not contain phase shift due to satellite movement:
        los_amplitude = 1.0
        #print 'receiver_to_satellite_unit_vec: ', receiver_to_satellite_unit_vec
        cirs[link_name][0]['real'] = los_amplitude.real
        cirs[link_name][0]['imag'] = los_amplitude.imag

        # for all scatterers:
        for l in range(nof_scatterers):
            receiver_to_scatterer_vec = refl_pos_m[l, :] - rec_pos_m
            distance_receiver_scatterer_m = np.linalg.norm(receiver_to_scatterer_vec)

            excess_distance_m = distance_receiver_scatterer_m - np.dot(receiver_to_satellite_unit_vec, receiver_to_scatterer_vec)
            excess_delay_s = excess_distance_m / c0_m_s

            idx = l + 1 # idx = 0 is LOS component
            cirs[link_name][idx]['type'] = 256 # scatterer type as set above
            cirs[link_name][idx]['id'] = 0
            cirs[link_name][idx]['delay'] = excess_delay_s
            scatterer_amplitude = 0.5 * cmath.exp(-1j * 2.0 * cmath.pi / wave_length_m * (distance_receiver_scatterer_m))
            cirs[link_name][idx]['real'] = scatterer_amplitude.real
            cirs[link_name][idx]['imag'] = scatterer_amplitude.imag

    # write CIRs for all satellites:
    cdx_file.append_cir(cirs, ref_delays)

print 'all done.'

## @} #
## @} #
