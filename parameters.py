import logging

import bluepyopt as bpo
from bluepyopt.ephys.serializer import DictMixin

logger = logging.getLogger(__name__)


""""""

"""
Abstract Parameter class for Python object parameters
Args:
    name (str): name of the Parameter
    value (float): Value for the parameter, required if Frozen=True
    frozen (bool): Whether the parameter can be varied, or its values is permently set
    bounds (indexable): two elements; the lower and upper bounds (Optional)
    param_name (str): name used within Python/NEURON
"""
class PyParameter(bpo.parameters.Parameter):
    """Contructor"""
    def __init__(self, name, value=None, frozen=False, bounds=None, param_name=None):
        super(PyParameter, self).__init__(name, value=value, frozen=frozen, bounds=bounds)
        self.param_name = param_name
        
    """Instantiate the parameter in the simulator"""
    def instantiate(self, sim=None, icell=None):
        pass
      
    """Remove parameter from the simulator"""
    def destroy(self, sim=None):
        pass


"""Contructor
Args:
    name (str): name of the Parameter
    value (float): Value for the parameter, required if Frozen=True
    frozen (bool): Whether the parameter can be varied, or its values is permently set
    bounds (indexable): two elements; the lower and upper bounds (Optional)
    param_name (str): name used within Python/NEURON
    Python objects on which to instantiate the parameter
"""
class PyObjectParameter(PyParameter, DictMixin):

    """Parameter of a section"""
    SERIALIZED_FIELDS = ('name', 'value', 'frozen', 'bounds', 'param_name', 'circuits')

    def __init__(self, name, value=None, frozen=False, bounds=None, param_name=None, py_objects=None):

        super(PyObjectParameter, self).__init__(name, value=value, frozen=frozen, bounds=bounds, param_name=param_name)

        self.py_objects = py_objects
        

    def instantiate(self, sim=None, icell=None):
        """Instantiate"""
        if self.value is None:
          raise Exception('PyObjectParameter: impossible to instantiate parameter "%s" without value' % self.name)

        # instantiate the objects
        for _py_object in self.py_objects:
          setattr(_py_object, self.param_name, self.value)
          if callable(getattr(_py_object, 'instantiate', None)):
            try:
              _py_object.instantiate(sim=sim, icell=icell)
            except TypeError:
              raise Exception('PyObjectParameter: impossible to call instantiate for the class %s' % _py_object)
            
          logger.debug('Set %s in %s to %s', self.param_name, _py_object, self.value)


    def destroy(self, sim=None):
        # destroy the objects
        for _py_object in self.py_objects:
          if callable(getattr(_py_object, 'destroy', None)):
            try:
              _py_object.destroy(sim=sim)
            except TypeError:
              raise Exception('PyObjectParameter: impossible to call destroy for the class %s' % _py_object)

      
    def __str__(self):
        """String representation"""
        return '%s: %s %s = %s' % (self.name, [str(_py_object) for _py_object in self.py_objects], self.param_name, self.value if self.frozen else self.bounds)

