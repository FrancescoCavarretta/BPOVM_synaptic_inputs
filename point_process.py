import bluepyopt.ephys as ephys
from bluepyopt.ephys.serializer import DictMixin

""" our own definition of point process
  which encapsulate the NEURON mechanism
"""
class NrnPointProcess:
    def __init__(self, name, suffix, location):
        self.mechanism = ephys.mechanisms.NrnMODPointProcessMechanism(name='mech_{name}', suffix=suffix, locations=location) 
        self.location = ephys.locations.NrnPointProcessLocation('loc_{name}' + name, pprocess_mech=self.mechanism)


    def instantiate(self, sim=None, icell=None):
        self.mechanism.instantiate(sim=sim, icell=icell)

        
    def destroy(self, sim=None):
        self.mechanism.destroy(sim=sim)
        
        
""" create a circuit with n Point Processes and various parameters """
class PointProcessGroup:
    def __init__(self, suffix, locations, source, *args, **kwargs):
        if type(locations) == list:
            self.locations = locations
        else:
            self.locations = [locations]

        self.suffix = suffix            # NEURON mech suffix
        self.fixed_param_value = kwargs # fixed param value

        # free params list
        self.free_param_name = args
        
        # create the free params as attributes
        for _free_param_name in self.free_param_name:
            setattr(self, _free_param_name, 0.)
            
        self.param_obj = {}  # model params NEURON/BPO object
        self.n = 0           # number of point process
        self.pprocess = []   # point process list
        self.source = source # stimulus source

    
    def _mk_parameter(self, name, value, pprocess, sim=None, icell=None, frozen=True):
        self.param_obj[name] = ephys.parameters.NrnPointProcessParameter(name="param_{self.suffix}_{name}", param_name=name, value=value, frozen=frozen, locations=pprocess)
        self.param_obj[name].instantiate(sim=sim, icell=icell)

        
    def instantiate(self, sim=None, icell=None):    
        self.pprocess = [None] * int(round(self.n))
        
        for i in range(len(self.pprocess)):
            self.pprocess[i] = NrnPointProcess("{self.suffix}_{str(i)}", self.suffix, self.locations)
            self.pprocess[i].instantiate(sim=sim, icell=icell)
            

        self.source.locations = [pp.location for pp in self.pprocess]
        self.source.instantiate(sim=sim, icell=icell)
        
        # set fixed parameters
        for name, value in self.fixed_param_value.items():
            self._mk_parameter(name, value, [pp.location for pp in self.pprocess], sim=sim, icell=icell)

        # set free parameters
        for name in self.free_param_name:
            self._mk_parameter(name, getattr(self, name), [pp.location for pp in self.pprocess], sim=sim, icell=icell)
            
                
    def destroy(self, sim=None):
        for i in range(len(self.pprocess)):
            self.pprocess[i].destroy(sim=sim)
            
        self.source.destroy(sim=sim)
        self.n = 0
        self.pprocess = []
        self.param_obj.clear()
