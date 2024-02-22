"""
Parser
======
The parser module contains functions for parsing the classifiers dictionary.
"""

def get_classifier_list(classifiers):
    """
    Get a list of classifiers.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        list: A list of classifiers.
    """
    classifier_list = []

    for num, _ in enumerate(classifiers.keys()):
        classifier_list.append(f"Classifier{num+1}")

    classifier_list.append("LeadSpecies")

    return classifier_list


def get_age_classifier(classifiers):
    """
    Get the age classifier.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        dict: A dictionary representing the age classifier.
    """
    max_age = classifiers["age_classes"]["max_age"]
    interval = classifiers["age_classes"]["age_interval"]

    age_id = []
    ages = []

    for year, value in enumerate(range(0, (max_age + 1), interval)):
        age_id.append("AGEID" + str(year))
        if year == 0:
            ages.append(0)
        else:
            ages.append(interval)

    age_dict = dict(zip(age_id, ages))

    return age_dict


def get_inventory_species(classifiers):
    """
    Get the inventory species.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        list: A list of inventory species.
    """
    species = []

    for s in classifiers["Classifiers"]["species"]:
        species.append(s)

    return species


def get_yield_class_proportions(classifiers, species_name, yield_class):
    """
    Get the yield class proportions for a given species and yield class.

    Args:
        classifiers (dict): A dictionary containing classifiers.
        species_name (str): The name of the species.
        yield_class (str): The yield class.

    Returns:
        float: The yield class proportions.
    """
    for i in classifiers["Classifiers"]["yield_class"][species_name]:
        for key, value in i.items():
            if key == yield_class:
                return value


def get_disturbance_type(classifiers):
    """
    Get the disturbance types.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        dict: A dictionary representing the disturbance types.
    """
    disturbance_type = {}
    for value, _ in enumerate(classifiers["Classifiers"]["distubance_type"]["id"]):
        disturbance_type[
            classifiers["Classifiers"]["distubance_type"]["id"][value]
        ] = classifiers["Classifiers"]["distubance_type"]["name"][value]

    return disturbance_type


def get_clearfell_baseline(classifiers):
    """
    Get the clearfell baseline.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        str: The clearfell baseline.
    """
    return classifiers["Classifiers"]["harvest"]["clearfell"]


def get_thinning_baseline(classifiers):
    """
    Get the thinning baseline.

    Args:
        classifiers (dict): A dictionary containing classifiers.

    Returns:
        str: The thinning baseline.
    """
    return classifiers["Classifiers"]["harvest"]["thinning"]
