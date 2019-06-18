from lazy import lazy
from mongoengine import *

class Participant(Document):
    label = StringField()
    station_name = StringField()
    region = StringField()
    state = StringField()
    dispatch_type = StringField()
    category = StringField()
    classification = StringField()
    fuel_source_primary = StringField()
    fuel_source_descriptor = StringField()
    technology_type_primary = StringField()
    technology_type_descriptor = StringField()
    physical_unit_no = StringField()
    unit_size_MW = FloatField()
    aggregation = StringField()
    DUID = StringField()
    reg_cap_MW = FloatField()
    max_cap_MW = FloatField()
    max_ROC_per_min = FloatField()


# Note for future explorers:
# There are some DUIDS that are in the bid files, that do NOT appear in this list.
# I got this list from the excel file "NEM Registration and Exemption List.xlsx"
# I scraped the DUIDS from the "Generators and Scheduled Loads" tab.

class ParticipantService(object):
    @lazy
    def participant_metadata(self):
        search = Participant.objects()
        participants = {}
        for p in search:
            participants[p.DUID] = {
                'state':p.state,
                'fuel_source_primary':p.fuel_source_primary,
                'fuel_source_descriptor':p.fuel_source_descriptor,
                'technology_type_primary':p.technology_type_primary,
                'technology_type_descriptor':p.technology_type_descriptor,
                'unit_size_MW':p.unit_size_MW,
                'reg_cap_MW':p.reg_cap_MW,
                'max_ROC_per_min':p.max_ROC_per_min,
                'label':p.label,
                'station_name':p.station_name,
            }
        return participants
    
    def get_participant_list(self, state="ALL"):
        participants = []
        if state != "ALL":
            participants = [p for p in self.participant_metadata if self.participant_metadata[p]['state'] == state ]
        else:
            participants = [p for p in self.participant_metadata]
        return participants