import json
import re


def get_classifier_list(classifiers):
    classifier_list = []

    for num, _ in enumerate(classifiers.keys()):
        classifier_list.append(f"Classifier{num+1}")

    classifier_list.append("LeadSpecies")

    return classifier_list


def get_age_classifier(classifiers):
    max_age = classifiers["age_classes"]["max_age"]
    interval = classifiers["age_classes"]["age_interval"]

    age_id = []
    ages = []

    for year in range(0, (max_age + 1), interval):
        age_id.append("AGEID" + str(year))
        ages.append(year)

    age_dict = dict(zip(age_id, ages))

    return age_dict


def get_inventory_species(classifiers):
    species = []

    for s in classifiers["Classifiers"]["species"]:
        species.append(s)

    return species


def get_yield_class_proportions(classifiers, species_name, yield_class):
    for i in classifiers["Classifiers"]["yield_class"][species_name]:
        for key, value in i.items():
            if key == yield_class:
                return value


def get_disturbance_type(classifiers):
    disturbance_type = {}
    for value, _ in enumerate(classifiers["Classifiers"]["distubance_type"]["id"]):
        disturbance_type[
            classifiers["Classifiers"]["distubance_type"]["id"][value]
        ] = classifiers["Classifiers"]["distubance_type"]["name"][value]

    return disturbance_type


def get_clearfell_baseline(classifiers):
    return classifiers["Classifiers"]["baseline"]["clearfell"]


def get_thinning_baseline(classifiers):
    return classifiers["Classifiers"]["baseline"]["thinning"]
