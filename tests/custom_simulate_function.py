
import os
import pandas as pd
from libcbm.input.sit import sit_cbm_factory
from libcbm.input.sit.sit import SIT
from libcbm.model.cbm import cbm_simulator
from libcbm.model.cbm.cbm_model import CBM
from libcbm.model.cbm.cbm_variables import CBMVariables
from libcbm.model.cbm import cbm_variables
from libcbm.model.cbm.cbm_output import CBMOutput
from libcbm import resources

def spinup(sit: SIT) -> CBMVariables:
    with sit_cbm_factory.initialize_cbm(sit) as cbm:

        cbm_vars = cbm_variables.initialize_simulation_variables(
            classifiers,
            inventory,
            cbm.pool_codes,
            cbm.flux_indicator_codes,
            inventory.backend_type,
        )

        spinup_vars = cbm_variables.initialize_spinup_variables(
            cbm_vars,
            inventory.backend_type,
            spinup_params=None, # if you are setting non-default mean annual temperature this may be important
            include_flux=False,
        )

        cbm.spinup(spinup_vars)

        if "mean_annual_temp" in spinup_vars.parameters.columns:
            # since the mean_annual_temp appears in the spinup parameters, carry
            # it forward to the simulation period so that we have consistent
            # columns in the outputs
            cbm_vars.parameters.add_column(
                spinup_vars.parameters["mean_annual_temp"],
                cbm_vars.parameters.n_cols,
            )
        cbm_vars = cbm.init(cbm_vars)

        return cbm_vars

def step(time_step: int, sit: SIT, cbm_vars: CBMVariables) -> CBMVariables:
    with sit_cbm_factory.initialize_cbm(sit) as cbm:
        rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
        # apply rule based disturbances to the cbm_vars for this timestep
        cbm_vars = rule_based_processor.pre_dynamics_func(time_step, cbm_vars)
        # advance the C dynamics
        cbm_vars = cbm.step(cbm_vars)
        return cbm_vars


                       
spinup_config_path = os.path.abspath("sit_config_spinup.json")
step_config_path = os.path.abspath("sit_config_step.json")

# Produce 2 sit objects based on potentially separate SIT inputs/configs.
# It is important that these inputs are compatible, otherwise the results
# may not make sense, and or the model may crash.

# In this context "compatible" means both inputs share the same sit_classifiers 
# input, and sit_disturbance_types input

spinup_sit = sit_cbm_factory.load_sit(
    spinup_config_path, db_path=resources.get_cbm_defaults_path()
)
step_sit = sit_cbm_factory.load_sit(
    step_config_path, db_path=resources.get_cbm_defaults_path()
)

classifiers, inventory = sit_cbm_factory.initialize_inventory(spinup_sit)
cbm_output = CBMOutput(
    classifier_map=spinup_sit.classifier_value_names
)

cbm_vars = spinup(spinup_sit)
# append the t=0 (post-spinup results)
cbm_output.append_simulation_result(0, cbm_vars)

for t in range(1, 23):
    # the t cbm_vars replace the t-1 cbm_vars
    cbm_vars = step(t, step_sit, cbm_vars)
    cbm_output.append_simulation_result(t, cbm_vars)

pi = cbm_output.classifiers.to_pandas().merge(cbm_output.pools.to_pandas())
pi.to_csv("classifiers_pools.csv", index=False)


