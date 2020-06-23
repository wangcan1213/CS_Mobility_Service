#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 18:03:46 2020

@author: doorleyr
"""

from mobility_service_model import MobilityModel
from activity_scheduler import ActivityScheduler
from mode_choice_nhts import NhtsModeLogit, NhtsModeRF
from two_stage_logit_hlc import TwoStageLogitHLC
from cs_handler import CS_Handler
import json


# =============================================================================
# Define New Modes
# =============================================================================
new_mode_specs=json.load(open('cities/Detroit/clean/new_mode_specs.json'))

pt_dissimilarity = 0.7
walk_dissimilarity = 0.3
prop_pt_similarity=1-(pt_dissimilarity/(pt_dissimilarity+walk_dissimilarity))


nests_spec=[{'name': 'pt_like', 
             'alts':['PT','bikeshare', 'shuttle'], 
             'lambda':pt_dissimilarity},
             {'name': 'walk_like',
             'alts': ['walk', 'bikeshare'],
             'lambda':walk_dissimilarity}
            ]

mode_choice_model=NhtsModeLogit(table_name='corktown', city_folder='Detroit')

params_for_share_bike = {}
existing_params = mode_choice_model.logit_model['params']
for g_attr in mode_choice_model.logit_generic_attrs:
    params_for_share_bike['{} for bikeshare'.format(g_attr)] = \
        existing_params['{} for PT'.format(g_attr)] * prop_pt_similarity + \
        existing_params['{} for walk'.format(g_attr)] * (1-prop_pt_similarity)
params_for_share_bike['ASC for bikeshare'] = existing_params['ASC for PT'] * prop_pt_similarity + \
        existing_params['ASC for walk'] * (1-prop_pt_similarity)


# =============================================================================
# Create model
# =============================================================================
this_model=MobilityModel('corktown', 'Detroit')

this_model.assign_activity_scheduler(ActivityScheduler(model=this_model))

mode_choice_model=NhtsModeLogit(table_name='corktown', city_folder='Detroit')
this_model.assign_mode_choice_model(mode_choice_model)

this_model.assign_home_location_choice_model(
        TwoStageLogitHLC(table_name='corktown', city_folder='Detroit', 
                         geogrid=this_model.geogrid, 
                         base_vacant_houses=this_model.pop.base_vacant))


# =============================================================================
# Add the mobility interventions
# =============================================================================
this_model.set_prop_electric_cars(0.5, co2_emissions_kg_met_ic= 0.000272,
                                  co2_emissions_kg_met_ev=0.00011)
this_model.set_new_modes(new_mode_specs, nests_spec=nests_spec)
mode_choice_model.set_logit_model_params(params_for_share_bike)


# =============================================================================
# Add to handler and start simulation
# =============================================================================

handler=CS_Handler(this_model)
handler.listen_city_IO()