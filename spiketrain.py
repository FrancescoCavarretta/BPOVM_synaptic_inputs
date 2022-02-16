import PyAST.neuron as astnrn
import bluepyopt.ephys.stimuli as stimuli

"""
  BPO -- adapted version of the online spike train generator
"""
class NrnSpikeTrainGenerator(astnrn.NrnSpikeTrainGenerator, stimuli.Stimulus):
  def __init__(self, isi_gen, total_duration, locations=[]):
    self.isi_gen = isi_gen # isi random generator
    self._netcons = {} # netcons activated at each spike time by calling _spike_ev
    self.locations = locations
    self.total_duration = total_duration


  def instantiate(self, sim=None, icell=None):
    self._netcons.clear() # clear the netcons and spike generator

    self.reset() # reset generation
    
    # typical instantiation in BPO
    for location in self.locations:
      for syn in location.instantiate(sim=sim, icell=icell):
        self.add_destination(syn) # create the netcons


  def destroy(self, sim=None):
    self._netcons.clear()


  
