import initialize_game_elements
import numpy as np
from card_utility_actions import move_player_after_die_roll
import simple_background_agent_becky_v1
import json
import diagnostics
from action_choices import *
import location
from agent_helper_functions import identify_free_mortgage
class Interface(object):
    def __init__(self):
        self.board_owned = ['Mediterranean Avenue', 'Baltic Avenue', 'Reading Railroad', 'Oriental Avenue',
             'Vermont Avenue', 'Connecticut Avenue','St. Charles Place', 'Electric Company', 'States Avenue',
             'Virginia Avenue','Pennsylvania Railroad', 'St. James Place', 'Tennessee Avenue',
             'New York Avenue', 'Kentucky Avenue', 'Indiana Avenue','Illinois Avenue', 'B&O Railroad',
             'Atlantic Avenue', 'Ventnor Avenue', 'Water Works', 'Marvin Gardens', 'Pacific Avenue',
             'North Carolina Avenue', 'Pennsylvania Avenue', 'Short Line', 'Park Place', 'Boardwalk']
        self.board_building = ['Mediterranean Avenue', 'Baltic Avenue', 'Oriental Avenue',
                   'Vermont Avenue', 'Connecticut Avenue', 'St. Charles Place', 'States Avenue',
                   'Virginia Avenue', 'St. James Place', 'Tennessee Avenue',
                   'New York Avenue', 'Kentucky Avenue', 'Indiana Avenue', 'Illinois Avenue',
                   'Atlantic Avenue', 'Ventnor Avenue', 'Marvin Gardens', 'Pacific Avenue',
                   'North Carolina Avenue', 'Pennsylvania Avenue', 'Park Place', 'Boardwalk']
        self.board_state = ['Go','Mediterranean Avenue', 'Community Chest',
                'Baltic Avenue', 'Income Tax', 'Reading Railroad', 'Oriental Avenue',
                'Chance', 'Vermont Avenue', 'Connecticut Avenue', 'In Jail/Just Visiting',
                'St. Charles Place', 'Electric Company', 'States Avenue', 'Virginia Avenue',
                'Pennsylvania Railroad', 'St. James Place', 'Community Chest', 'Tennessee Avenue',
                'New York Avenue', 'Free Parking', 'Kentucky Avenue', 'Chance', 'Indiana Avenue',
                'Illinois Avenue', 'B&O Railroad', 'Atlantic Avenue', 'Ventnor Avenue',
                'Water Works', 'Marvin Gardens', 'Go to Jail', 'Pacific Avenue', 'North Carolina Avenue',
                'Community Chest', 'Pennsylvania Avenue', 'Short Line', 'Chance', 'Park Place',
                                        'Luxury Tax', 'Boardwalk']
        self.state_space = []
        self.masked_actions = []
        self.move_actions = []

    def board_to_state(self,current_board):
        '''
        :param current_board:
        :return: state_space
        '''

        state_space = []

        # 28 spaces which can be owned by players
        # -1 means other players, 0 means bank, and 1 means agent/ player 1
        state_space_owned = []
        for space in self.board_owned:
            if current_board['location_objects'][space].owned_by == current_board['bank']:
                state_space_owned.append(0)
            elif current_board['location_objects'][space].owned_by.player_name == 'player_1':
                state_space_owned.append(1)
            else:
                state_space_owned.append(-1)
        state_space += state_space_owned

        #22 spaces which can be built houses: # of houses in the space: 0,1,2,3,4,5
        state_space_building = []
        for space in self.board_building:
            if current_board['location_objects'][space].num_hotels == 0:
                state_space_building.append(current_board['location_objects'][space].num_houses)
            else:
                state_space_building.append(5) # 5 denotes hotel
        state_space += state_space_building

        #n cash ratio for all the players n = # of players
        sorted_player = sorted(current_board['players'], key=lambda player: int(player.player_name[-1]))
        state_space_cash = [int(p.current_cash) for p in sorted_player]
        state_space += state_space_cash

        #n positions of players n = # of players
        state_space_position = [int(p.current_position) for p in sorted_player]
        state_space += state_space_position

        #2 # of get-out_of_jail_card of players
        state_space_card = []
        com_card = [p.has_get_out_of_jail_community_chest_card for p in sorted_player]
        chance_card = [p.has_get_out_of_jail_chance_card for p in sorted_player]
        # first num denots the # of card agent has
        num_card_agent = int(com_card[0] + chance_card[0])
        state_space_card.append(num_card_agent)
        # second numes the cards other players have
        num_card_others = sum(com_card) + sum(chance_card) - num_card_agent
        state_space_card.append(num_card_others)
        state_space += state_space_card

        self.state_space = state_space
        return state_space

    def get_masked_actions(self, allowable_actions, param, current_player):
        masked_actions = []
        #1 first denotes the action -> buy or not buy
        if buy_property in allowable_actions:
            masked_actions.append(1)
        else:
            masked_actions.append(0)

        #22 improve property
        if improve_property in allowable_actions:
            if param:
                for space in self.board_building:
                    masked_actions.append(1) if space in param['asset'] else masked_actions.append(0)
            else:
                for space in self.board_building:
                    masked_actions.append(0)
        else:
            masked_actions += [0 for i in range(22)]

        #28 actions_allowed_morgage
        owned_space = [asset.name for asset in current_player.assets]
        for space in self.board_owned:
            masked_actions.append(1) if space in owned_space else masked_actions.append(0)

        # 28 actions: free morgage
        potentials = identify_free_mortgage(current_player)
        for space in self.board_owned:
            masked_actions.append(1) if space in potentials else masked_actions.append(0)

        self.masked_actions = masked_actions
        return masked_actions

    #action space 1+22+28+28
    def action_space(self, current_board, current_palyer):
        action_space = []
        site_space = []
        # 1 first denotes the action -> buy or not buy
        action_space.append(buy_property)
        site_space.append(current_board['location_objects'][self.board_state[current_palyer.current_position]])

        # 22 improve property
        for space in self.board_building:
            site_space.append(current_board['location_objects'][space])
        for i in range(len(self.board_building)):
            action_space.append(improve_property)

        #28 actions_allowed_mortgage
        for space in self.board_owned:
            site_space.append(current_board['location_objects'][space])
        for i in range(len(self.board_owned)):
            action_space.append(mortgage_property)

        # 28 actions: free mortgage
        for space in self.board_owned:
            site_space.append(current_board['location_objects'][space])
        for i in range(len(self.board_owned)):
            action_space.append(free_mortgage)

        return action_space,site_space

        #take into array/vector and output the actions
    actions_vector_default = [1] + [0 for i in range(22+28+28)]
    def vector_to_actions(self, current_board, current_palyer, actions_vector=actions_vector_default):
        move_actions = []
        action_space, site_space = self.action_space(current_board, current_palyer)
        for i,action in enumerate(actions_vector):
            if action == 1:
                move_actions.append((action_space[i], site_space[i]))

        self.move_actions = move_actions

        #####becky - may be deleted##########
        allowed_types = [location.UtilityLocation, location.RailroadLocation, location.RealEstateLocation]
        if type(move_actions[0][1]) in allowed_types:
            return move_actions
        else:
            return []




