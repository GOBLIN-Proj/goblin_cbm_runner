

class Pools:
    """
    Class representing the pools in a CBM model.

    This class encapsulates various types of pools relevant in the context of Carbon Budget Modeling (CBM),
    such as biomass pools, deadwood, litter, and soil organic matter. It also manages annual process fluxes.

    Methods:
        get_above_ground_biomass_pools(): Retrieves above ground biomass pools.
        get_below_ground_biomass_pools(): Retrieves below ground biomass pools.
        get_deadwood_pools(): Retrieves deadwood pools.
        get_litter_pools(): Retrieves litter pools.
        get_soil_organic_matter_pools(): Retrieves soil organic matter pools.
        get_annual_process_fluxes(): Retrieves annual process fluxes.

    Attributes:
        above_ground_biomass_pools (list): List of above ground biomass pools.
        below_ground_biomass_pools (list): List of below ground biomass pools.
        deadwood (list): List of deadwood pools.
        litter (list): List of litter pools.
        soil_organic_matter (list): List of soil organic matter pools.
        annual_process_fluxes (list): List of annual process fluxes.
    """
    def __init__(self):
        self.above_ground_biomass_pools = [
            "SoftwoodMerch",
            "SoftwoodFoliage",
            "SoftwoodOther",
            "HardwoodMerch",
            "HardwoodFoliage",
            "HardwoodOther"
        ]

        self.below_ground_biomass_pools = [
            "SoftwoodCoarseRoots",
            "SoftwoodFineRoots",
            "HardwoodCoarseRoots",
            "HardwoodFineRoots"
        ]

        self.deadwood = [
            "BelowGroundFastSoil",
            "MediumSoil",
            "SoftwoodStemSnag",
            "SoftwoodBranchSnag",
            "HardwoodStemSnag",
            "HardwoodBranchSnag",
        ]

        self.litter = [
            "AboveGroundVeryFastSoil",
            "AboveGroundFastSoil",
            "AboveGroundSlowSoil"
        ]

        self.soil_organic_matter = [
            "BelowGroundVeryFastSoil",
            "BelowGroundSlowSoil"
        ]

        self.annual_process_fluxes = [
            'DecayDOMCO2Emission',
            'DeltaBiomass_AG',
            'DeltaBiomass_BG',
            'TurnoverMerchLitterInput',
            'TurnoverFolLitterInput',
            'TurnoverOthLitterInput',
            'TurnoverCoarseLitterInput',
            'TurnoverFineLitterInput',
            'DecayVFastAGToAir',
            'DecayVFastBGToAir',
            'DecayFastAGToAir',
            'DecayFastBGToAir',
            'DecayMediumToAir',
            'DecaySlowAGToAir',
            'DecaySlowBGToAir',
            'DecaySWStemSnagToAir',
            'DecaySWBranchSnagToAir',
            'DecayHWStemSnagToAir',
            'DecayHWBranchSnagToAir']

    def get_above_ground_biomass_pools(self):
        """
        Returns the above ground biomass pools.

        Returns:
            list: List of above ground biomass pools.
        """
        return self.above_ground_biomass_pools

    def get_below_ground_biomass_pools(self):
        """
        Returns the below ground biomass pools.

        Returns:
            list: List of below ground biomass pools.
        """
        return self.below_ground_biomass_pools
    
    def get_deadwood_pools(self):
        """
        Returns the deadwood pools.

        Returns:
            list: List of deadwood pools.
        """
        return self.deadwood
    
    def get_litter_pools(self):
        """
        Returns the litter pools.

        Returns:
            list: List of litter pools.
        """
        return self.litter
    
    def get_soil_organic_matter_pools(self):
        """
        Returns the soil organic matter pools.

        Returns:
            list: List of soil organic matter pools.
        """
        return self.soil_organic_matter

    def get_annual_process_fluxes(self):
        """
        Returns the annual process fluxes.

        Returns:
            list: List of annual process fluxes.
        """
        return self.annual_process_fluxes