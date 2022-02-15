"""Expsyn synapse parameter fitting"""

# pylint: disable=R0914


import os
import logging
import bluepyopt as bpopt
import bluepyopt.ephys as ephys
from bluepyopt.ephys.serializer import DictMixin
logger = logging.getLogger(__name__)

class PyParameter(bpopt.parameters.Parameter, DictMixin):

    """Parameter of a section"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name',
                         'value_scaler', 'locations', )

    def __init__(
            self,
            name,
            value=None,
            frozen=False,
            bounds=None,
            locations=None,
            param_name=None):
        """Constructor
        Args:
            name (str): name of the Parameter
            value (float): Value for the parameter, required if Frozen=True
            frozen (bool): Whether the parameter can be varied, or its values
            is permently set
            bounds (indexable): two elements; the lower and upper bounds
                (Optional)
            locations: an iterator of the point process locations you want to
                       set the parameters of
            param_name (str): name of parameter used within the point process
        """

        super(PyParameter, self).__init__(
            name,
            value=value,
            frozen=frozen,
            bounds=bounds)

        self.locations = locations
        self.param_name = param_name


    def instantiate(self, sim=None, icell=None):
        """Instantiate"""
        if self.value is None:
            raise Exception(
                'PySectionParameter: impossible to instantiate parameter "%s"'
                ' without value' %
                self.name)

        for location in self.locations:
            setattr(location, self.param_name, self.value  )
            location.instantiate(sim=sim, icell=icell)
            logger.debug(
                'Set %s to %s for point process',
                self.param_name,
                self.value)
            

    def __str__(self):
        """String representation"""
        return '%s: %s = %s' % (self.name,
                                self.param_name,
                                self.value if self.frozen else self.bounds)
    
    def destroy(self, sim=None):
        for location in self.locations:
            location.destroy(sim=sim)


""" create a synaptic circuit, as nsyn synapses """
class SynapticCircuit:
    def __init__(self, location):
        if type(location) == list:
            self.location = location
        else:
            self.location = [location]

        # create nsyn synapses
        self.expsyn_mech = []
        self.expsyn_loc = []
        self.expsyn_tau_param = []
        self.nsyn = 0
        
        # stimulus parameters 
        self.stim_start = 20
        self.number = 5
        self.interval = 5
        self.time_add = 20
        self.stim_duration = self.interval * self.number
        self.stim_end = self.stim_start + self.stim_duration
        self.total_duration = self.stim_end + self.time_add
        self.weight = 5e-4
        
        self.netstim = ephys.stimuli.NrnNetStimStimulus(total_duration=self.stim_end,
            number=self.number,
            interval=self.interval,
            start=self.stim_start,
            weight=self.weight,
            locations=self.expsyn_loc)


        
    def instantiate(self, sim=None, icell=None):
        nsyn = int(round(self.nsyn))
    
        self.expsyn_mech = [None] * nsyn
        self.expsyn_loc = [None] * nsyn
        self.expsyn_tau_param = [None] * nsyn
        
        for isyn in range(nsyn):
            self.expsyn_mech[isyn] = ephys.mechanisms.NrnMODPointProcessMechanism(name='expsyn' + '_' + str(isyn), suffix='ExpSyn', locations=self.location) 
            self.expsyn_mech[isyn].instantiate(sim=sim, icell=icell)

            self.expsyn_loc[isyn] = ephys.locations.NrnPointProcessLocation('expsyn_loc' + '_' + str(isyn), pprocess_mech=self.expsyn_mech[isyn]) 
            self.expsyn_loc[isyn].instantiate(sim=sim, icell=icell)

            self.expsyn_tau_param[isyn] = ephys.parameters.NrnPointProcessParameter(name='expsyn_tau' + '_' + str(isyn), param_name='tau', value=14.0, locations=[self.expsyn_loc[isyn]]) 
            self.expsyn_tau_param[isyn].instantiate(sim=sim, icell=icell)

        self.netstim.locations = self.expsyn_loc
        self.netstim.instantiate(sim=sim, icell=icell)
        

    def destroy(self, sim=None):
        nsyn = int(round(self.nsyn))
    
        for isyn in range(nsyn):
            self.expsyn_mech[isyn].destroy(sim=sim)
            #self.expsyn_loc[isyn].destroy(sim=sim)
            self.expsyn_tau_param[isyn].destroy(sim=sim)
        self.netstim.destroy(sim=sim)
        self.nsyn = 0
        self.expsyn_mech = []
        self.expsyn_loc = []
        self.expsyn_tau_param = []





            

            



            
        

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



    syn_circuit = SynapticCircuit(somacenter_loc)

    syn_circ_nsyn = PyParameter(name='syn_circ_nsyn',
                                param_name='nsyn',
                                value=0,
                                bounds=[0, 100],
                                locations=[syn_circuit])


    

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
        params=[cm_param, syn_circ_nsyn])

    rec = ephys.recordings.CompRecording(
        name='soma.v',
        location=somacenter_loc,
        variable='v')

    protocol = ephys.protocols.SweepProtocol(
        'netstim_protocol',
        [syn_circuit.netstim],
        [rec])

    max_volt_feature = ephys.efeatures.eFELFeature(
        'maximum_voltage',
        efel_feature_name='maximum_voltage',
        recording_names={'': 'soma.v'},
        stim_start=syn_circuit.stim_start,
        stim_end=syn_circuit.stim_end,
        exp_mean=-30,
        exp_std=1.0)
    
    max_volt_objective = ephys.objectives.SingletonObjective(
        max_volt_feature.name,
        max_volt_feature)

    score_calc = ephys.objectivescalculators.ObjectivesCalculator(
        [max_volt_objective])

    cell_evaluator = ephys.evaluators.CellEvaluator(
        cell_model=cell,
        param_names=['syn_circ_nsyn'],
        fitness_protocols={protocol.name: protocol},
        fitness_calculator=score_calc,
        sim=nrn_sim)

    default_param_values = {'syn_circ_nsyn': 15}

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
