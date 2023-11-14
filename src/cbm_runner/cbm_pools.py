

class Pools:
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
        return self.above_ground_biomass_pools

    def get_below_ground_biomass_pools(self):
        return self.below_ground_biomass_pools
    
    def get_deadwood_pools(self):
        return self.deadwood
    
    def get_litter_pools(self):
        return self.litter
    
    def get_soil_organic_matter_pools(self):
        return self.soil_organic_matter

    def get_annual_process_fluxes(self):
        return self.annual_process_fluxes
