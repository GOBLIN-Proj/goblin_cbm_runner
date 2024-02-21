from cbm_runner.cbm_validation_manager import CBM_ValidationManager

def main():
    val = CBM_ValidationManager()

    print(val.get_linked_events(0))
    print(val.get_site_event_stats_by_timestep(0))
    print(val.get_age_classes(0))
    print(val.get_sit_events(0))
    print(val.get_baseline_forest())

if __name__ == "__main__":
    main()