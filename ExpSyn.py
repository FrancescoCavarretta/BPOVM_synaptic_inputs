"""Expsyn synapse parameter fitting"""

# pylint: disable=R0914


import os
import logging
import bluepyopt as bpopt
import bluepyopt.ephys as ephys
from bluepyopt.ephys.serializer import DictMixin
logger = logging.getLogger(__name__)


from parameters import PyObjectParameter


from point_process import NrnPointProcess, PointProcessGroup






            
class ISI:
    def __init__(self):
        self.n = 0
        self.first = True
    
    def get(self):
        self.n += 1
        if self.n > 5:
            return None
        if self.first:
            self.first = False
            return 20.0
        return 5.0
    
    def reset(self):
        self.n = 0
        self.first = True
            


from spiketrain import NrnSpikeTrainGenerator
            
        

def main():
    """Main"""
    nrn_sim = ephys.simulators.NrnSimulator()

    morph = ephys.morphologies.NrnFileMorphology(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'simple.swc'))
    
    somatic_loc = ephys.locations.NrnSeclistLocation(
        'somatic',
        seclist_name='somatic')

    somacenter_loc = ephys.locations.NrnSeclistCompLocation(
        name='somacenter',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)

    pas_mech = ephys.mechanisms.NrnMODMechanism(
        name='pas',
        suffix='pas',
        locations=[somatic_loc])

    # stimulus parameters

    stim_start = 20
    number = 5
    interval = 5
    time_add = 20
    stim_duration = interval * number
    stim_end = stim_start + stim_duration
    total_duration = stim_end + time_add
    weight = 1.0
    
    stg = NrnSpikeTrainGenerator(ISI())
    stg.total_duration = total_duration    

    netstim = ephys.stimuli.NrnNetStimStimulus(total_duration=stim_end, number=number, interval=interval, start=stim_start, weight=weight, locations=[])

    netstim = stg

    syn_circuit = PointProcessGroup('MyExpSyn', somacenter_loc, netstim, 'gmax', tau=14.0)

    syn_circ_nsyn = PyObjectParameter(name='syn_circ_nsyn',
                                param_name='n',
                                value=0,
                                bounds=[0, 100],
                                py_objects=[syn_circuit])
    
    syn_circ_gmax = PyObjectParameter(name='syn_circ_gmax',
                                param_name='gmax',
                                value=0,
                                bounds=[0, 0.01],
                                py_objects=[syn_circuit])


    

    cm_param = ephys.parameters.NrnSectionParameter(
        name='cm',
        param_name='cm',
        value=1.0,
        locations=[somatic_loc],
        frozen=True)

    cell = ephys.models.CellModel(
        name='simple_cell',
        morph=morph,
        mechs=[pas_mech, syn_circuit],
        params=[cm_param, syn_circ_nsyn, syn_circ_gmax])

    rec = ephys.recordings.CompRecording(
        name='soma.v',
        location=somacenter_loc,
        variable='v')

    protocol = ephys.protocols.SweepProtocol(
        'netstim_protocol',
        [netstim],
        [rec])

    max_volt_feature = ephys.efeatures.eFELFeature(
        'maximum_voltage',
        efel_feature_name='maximum_voltage',
        recording_names={'': 'soma.v'},
        stim_start=stim_start,
        stim_end=stim_end,
        exp_mean=-40,
        exp_std=1.0)
    
    max_volt_objective = ephys.objectives.SingletonObjective(
        max_volt_feature.name,
        max_volt_feature)

    score_calc = ephys.objectivescalculators.ObjectivesCalculator(
        [max_volt_objective])

    cell_evaluator = ephys.evaluators.CellEvaluator(
        cell_model=cell,
        param_names=['syn_circ_nsyn', 'syn_circ_gmax'],
        fitness_protocols={protocol.name: protocol},
        fitness_calculator=score_calc,
        sim=nrn_sim)

    default_param_values = {'syn_circ_nsyn': 15, 'syn_circ_nsyn':0.001}

    print(cell_evaluator.evaluate_with_dicts(default_param_values))

    optimisation = bpopt.optimisations.DEAPOptimisation(
        evaluator=cell_evaluator,
        offspring_size=10)

    _, hall_of_fame, _, _ = optimisation.run(max_ngen=5)

    best_ind = hall_of_fame[0]

    print('Best individual: ', best_ind)
    print('Fitness values: ', best_ind.fitness.values)

    best_ind_dict = cell_evaluator.param_dict(best_ind)
    responses = protocol.run(
        cell_model=cell,
        param_values=best_ind_dict,
        sim=nrn_sim)

    time = responses['soma.v']['time']
    voltage = responses['soma.v']['voltage']

    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    plt.plot(time, voltage)
    plt.xlabel('Time (ms)')
    plt.ylabel('Voltage (ms)')
    plt.show()


if __name__ == '__main__':
    main()
