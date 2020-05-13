from collections import defaultdict
from typing import List, Dict, Tuple
import networkx as nx
from django.db.models import Sum
from pandemic.controller import cards
from pandemic.controller.cards import _check_card_type, dump_location_cards
from pandemic.controller.utils import get_location_id
from pandemic.errors import ResearchCenterAlreadyPresent, ResearchCenterLimit, NoResearchCenterPresent, NoDiseaseToCure, \
    LocationCardsAreMissing, LocationCardsNotMatching, DiseaseAlreadyCured
from pandemic.models.cards_location import CardLocation, CardPosition
from pandemic.models.disease import DiseaseStatusEnum, DiseaseStatus
from pandemic.models.maplocation import MapLocation, LocationType, LocationLinkTypes
from pandemic.models import MapState, Disease


def get_starting_location(playroom):
    return playroom.map.starting_location


def initialize_map_states(playroom):
    MapState.objects.filter(playroom=playroom).delete()
    all_locations = MapLocation.objects.filter(map=playroom.map)
    all_map_states = []
    for location in all_locations:
        all_map_states.append(MapState(playroom=playroom, location=location))
    MapState.objects.bulk_create(all_map_states)


def initialize_research_centers(playroom):
    location_init = get_starting_location(playroom)
    build_research_center(playroom, location_init.name)


def initialize_infections(playroom):
    infection_cards = cards.draw_infections(playroom, 9)

    infect_locations(playroom, [c.name for c in infection_cards[0:3]], number_of_disease=3)
    infect_locations(playroom, [c.name for c in infection_cards[3:6]], number_of_disease=2)
    infect_locations(playroom, [c.name for c in infection_cards[6: 9]], number_of_disease=1)


def initialize_disease_status(playroom):
    disease_status = []
    for disease_type in DiseaseStatusEnum:
        disease_status.append(DiseaseStatus(disease_type=disease_type, playroom=playroom))
    DiseaseStatus.objects.bulk_create(disease_status)


def heal_disease(playroom, location_name, disease_type, heal_all=False):
    try:
        disease = Disease.objects.get(map_state__playroom=playroom,
                                      map_state__location__name=location_name,
                                      disease_type=disease_type)
    except Disease.DoesNotExist:
        raise NoDiseaseToCure
    if disease.disease_count <= 0:
        raise NoDiseaseToCure

    heal_all = heal_all if heal_all else DiseaseStatus.objects.filter(playroom=playroom,
                                                                      disease_type=disease_type,
                                                                      disease_status=DiseaseStatusEnum.cured.value).count() > 0
    if heal_all:
        disease.disease_count = 0
    else:
        disease.disease_count -= 1

    disease.save()
    return disease


def cure_disease(playroom, player, card_names) -> DiseaseStatus:
    if len(card_names) != 5:
        raise LocationCardsAreMissing
    cards = CardLocation.objects.filter(playroom=playroom, position=CardPosition.hand.value,
                                        player=player, card__name=card_names).prefetch_related('card__location')
    if len(cards) != len(card_names):
        raise LocationCardsAreMissing
    disease_type = cards[0].card.location.location_type
    if not _check_card_type(cards, disease_type):
        raise LocationCardsNotMatching
    disease_status = _cured_disease(playroom, disease_type)
    dump_location_cards(cards)
    return disease_status


def _cured_disease(playroom, disease_type):
    try:
        disease_status = DiseaseStatus.objects.get(playroom=playroom, disease_type=disease_type,
                                                   disease_status=DiseaseStatusEnum.ongoing.value)
    except DiseaseStatus.DoesNotExist:
        raise DiseaseAlreadyCured
    disease_status.disease_status = DiseaseStatusEnum.cured.value
    disease_status.save()
    return disease_status


def eradicate_disease(playroom) -> List[Disease]:
    cured_diseases = DiseaseStatus.objects.filter(playroom=playroom,
                                                  disease_status=DiseaseStatusEnum.cured.value)
    absent_diseases_types = Disease.objects.filter(map_state__playroom=playroom).annotate(
        total_disease_count=Sum('disease_count')).filter(total_disease_count=0).values_list('disease_type', flat=True)

    eradicated = []
    for cured_disease in cured_diseases:
        if cured_disease.disease_type in absent_diseases_types:
            cured_disease.disease_status = DiseaseStatusEnum.eradicated.value
            cured_disease.save()
            eradicated.append(cured_disease)
    return eradicated


def infect_locations(playroom, location_names: List[str], number_of_disease=1) -> List[Disease]:
    infected_disease = []
    locations = MapLocation.objects.filter(name__in=location_names, map=playroom.map)
    for location in locations:
        map_state, _ = MapState.objects.get_or_create(location=location, playroom=playroom)
        disease_type = map_state.location.location_type
        disease, _ = Disease.objects.get_or_create(map_state=map_state, disease_type=disease_type)
        disease.disease_count += number_of_disease
        infected_disease.append(disease)
        disease.save()
    return infected_disease


def get_free_research_centers(playroom):
    return 6 - MapState.objects.filter(playroom=playroom, research_center=True).count()


def build_research_center(playroom, location_name):
    map_state = MapState.objects.get(playroom=playroom, location__name=location_name)
    if map_state.research_center:
        raise ResearchCenterAlreadyPresent
    if get_free_research_centers(playroom) < 1:
        raise ResearchCenterLimit
    map_state.research_center = True
    map_state.save()


def destroy_research_center(playroom, location_name):
    map_state = MapState.objects.get(playroom=playroom, location__name=location_name)
    if map_state.research_center:
        raise NoResearchCenterPresent
    map_state.research_center = False
    map_state.save()


def get_disease_count(playroom) -> Dict[str, Dict[int, int]]:
    disease_count = defaultdict(lambda: defaultdict(lambda: 0))
    diseases = Disease.objects.filter(map_state__playroom=playroom).prefetch_related('map_state__location')
    for disease in diseases:
        disease_count[get_location_id(disease.map_state.location)][disease.disease_type] = disease.disease_count
    return disease_count


def get_research_center(playroom) -> Dict[str, bool]:
    dict_location_to_research_centers = defaultdict(lambda: False)
    all_locations_with_research_centers = MapLocation.objects.filter(location_map_state__playroom=playroom,
                                                                     location_map_state__research_center=True)
    for loc in all_locations_with_research_centers:
        dict_location_to_research_centers[get_location_id(loc)] = True
    return dict_location_to_research_centers


def get_disease_status(playroom) -> Dict[str, int]:
    disease_status = defaultdict(lambda: DiseaseStatusEnum.ongoing.value)
    diseases = DiseaseStatus.objects.filter(playroom=playroom)
    for disease in diseases:
        disease_status[disease.disease_type] = disease.disease_status
    return disease_status


def get_location_graph(playroom):
    location_networkx = nx.DiGraph()
    neighbors_links = get_all_neighbor_links(playroom)
    research_links = get_all_research_center_links(playroom)
    location_networkx.add_edges_from(neighbors_links, edge_type=LocationLinkTypes.neighbor.value)
    location_networkx.add_edges_from(research_links, edge_type=LocationLinkTypes.research_center.value)
    return location_networkx


def get_location_types(playroom) -> Dict:
    all_locations = MapLocation.objects.filter(map__playroom=playroom).values_list("name", "location_type")
    return {t[0]: t[1] for t in all_locations}


def get_all_neighbor_links(playroom):
    all_locations = MapLocation.objects.filter(map=playroom.map).prefetch_related('neighbors')
    all_links = [(get_location_id(loc), get_location_id(neighbor))
                 for loc in all_locations for neighbor in loc.neighbors.all()]
    return all_links


def get_all_research_center_links(playroom) -> List[Tuple[str, str]]:
    edges = []
    all_locations_with_research_center = MapLocation.objects.filter(location_map_state__playroom=playroom,
                                                                    location_map_state__research_center=True)
    for i in range(0, len(all_locations_with_research_center)):
        location_in = get_location_id(all_locations_with_research_center[i])
        for j in range(i, len(all_locations_with_research_center)):
            location_out = get_location_id(all_locations_with_research_center[j])
            edges.append((location_in, location_out))
    return edges


def get_all_locations(playroom) -> Dict:
    all_locations = MapLocation.objects.filter(map=playroom.map).prefetch_related("neighbors")
    return {loc.name: loc.serialize() for loc in all_locations}
