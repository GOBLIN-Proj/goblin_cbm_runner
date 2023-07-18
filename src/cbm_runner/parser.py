import json
import re

def get_classifier_list(classifiers):

    classifier_list = []
    
    for key in classifiers["classifier_id"]:
        classifier_list.append(f"Classifier{key}")

    classifier_list.append("LeadSpecies")

    return classifier_list


def get_age_classifier(classifiers):

    ages = []

    for n in classifiers["age_classifier"]["description"]:

        num = re.findall(r"\d+", n)

        if num:
            ages.append(int(num[0]))

    age_dict = dict(zip(classifiers["age_classifier"]["name"], ages))

    return age_dict


def get_inventory_species(classifiers):

    species = []

    for s in classifiers["inventory"]["species"]:
        species.append(list(s.keys())[0])

    return species


def get_inventory_type(classifiers, species_name):

    inventory_type = []

    for i, species in enumerate(get_inventory_species(classifiers)):
        if species == species_name:
            for typ in classifiers["inventory"]["species"][i][species]["type"]:
                inventory_type.append(typ)

    return inventory_type


def get_inventory_soil(classifiers, species_name):

    inventory_soil = []

    for i, species in enumerate(get_inventory_species(classifiers)):
        if species == species_name:
            for soil in classifiers["inventory"]["species"][i][species]["soil"]:
                inventory_soil.append(soil)

    return inventory_soil


def get_inventory_yield_class(classifiers, species_name):

    inventory_yield_class = []

    for i, species in enumerate(get_inventory_species(classifiers)):
        if species == species_name:
            for yc in classifiers["inventory"]["species"][i][species]["yield_class"]:
                inventory_yield_class.append(yc)

    return inventory_yield_class

def get_yield_class_proportions(classifiers, species_name, yield_class):

    for i in classifiers["yield_class"][species_name]:
        for key, value in i.items():
            if key == yield_class:
                return value


def get_disturbance_type(classifiers):

    disturbance_type = {}
    for value, _ in enumerate(classifiers["distubance_type"]["id"]):
        disturbance_type[classifiers["distubance_type"]["id"][value]] = classifiers["distubance_type"]["name"][value]

    return disturbance_type

def get_historical_disturbance(classifiers, forest, species):
    return classifiers["historical_disturbance"][forest][species]


def get_yield_class(classifiers, species):
    return classifiers["yield_class"][species]


def get_clearfell_baseline(classifiers):
    return classifiers["baseline"]["clearfell"]


def get_thinning_baseline(classifiers):
    return classifiers["baseline"]["thinning"]
