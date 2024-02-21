"""
Geo CBM Validation Manager
==========================
This class is responsible for retrieving the validation data from the validation directory.
"""
from cbm_validation.validation import ValidationData
from geo_cbm_runner.validation_data import get_local_dir

class GeoCBM_ValidationManager:
    """
    This class is responsible for retrieving the validation data generated when running scenarios.

    To generate validation data, the GeoRunner attribute must be set to ```gen_validation``` True and the valdiation path must be set.

    Attributes:
        path (str): The path to the local directory.

    Methods:
        clear_validation_folder: Clears the validation folder.
        get_linked_events: Retrieves linked events data from a CSV file.
        get_site_event_stats_by_timestep: Retrieves site event stats by timestep data from a CSV file.
        get_age_classes: Retrieves age classes data from a CSV file.
        get_sit_events: Retrieves site events data from a CSV file.
        get_baseline_forest: Retrieves the baseline forest data from a CSV file.
        get_data_area: Retrieves area data from a CSV file.
        get_data_flux: Retrieves flux data from a CSV file.
        get_data_params: Retrieves parameters data from a CSV file.
        get_data_pools: Retrieves pools data from a CSV file.
        get_data_state: Retrieves state data from a CSV file.
    """

    def __init__(self):
        self.path = get_local_dir()


    def clear_validation_folder(self):
        """
        Clears the validation folder.
        """
        ValidationData.clear_validation_folder(self.path)

    
    def get_linked_events(self, scenario):
        """
        Retrieves linked events data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the linked events data, or an 
            error message if the file is not found.
        """
        return ValidationData.get_linked_events(self.path, scenario)
    

    def get_site_event_stats_by_timestep(self, scenario):
        """
        Retrieves site event stats by timestep data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the site event stats by timestep data, or an
            error message if the file is not found.
        """
        return ValidationData.get_site_event_stats_by_timestep(self.path, scenario)
    
    def get_age_classes(self, scenario):
        """
        Retrieves age classes data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the age classes data, or an
            error message if the file is not found.

        """
        return ValidationData.get_age_classes(self.path, scenario)
    

    def get_sit_events(self, scenario):
        """
        Retrieves site events data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the site events data, or an
            error message if the file is not found.
        """
        return ValidationData.get_sit_events(self.path, scenario)
    

    def get_baseline_forest(self):
        """
        Retrieves the baseline forest data from a CSV file.

        Returns:
            A pandas DataFrame containing the baseline forest data, or an
            error message if the file is not found.
        """
        return ValidationData.get_baseline_forest(self.path)
    
    def get_data_area(self, scenario):
        """
        Retrieves area data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the data area data, or an
            error message if the file is not found.
        """
        return ValidationData.get_data_area(self.path, scenario)

    def get_data_flux(self, scenario):
        """
        Retrieves flux data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the flux data, or an
            error message if the file is not found.
        """
        return ValidationData.get_data_flux(self.path, scenario)
    

    def get_data_params(self, scenario):
        """
        Retrieves parameters data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the parameters data, or an
            error message if the file is not found.
        """
        return ValidationData.get_data_params(self.path, scenario)
    

    def get_data_pools(self, scenario):
        """
        Retrieves pools data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the pools data, or an
            error message if the file is not found.
        """
        return ValidationData.get_data_pools(self.path, scenario)
    

    def get_data_state(self, scenario):
        """
        Retrieves state data from a CSV file.

        Args:
            sc: The scenario identifier.

        Returns:
            A pandas DataFrame containing the state data, or an
            error message if the file is not found.
        """
        return ValidationData.get_data_state(self.path, scenario)
