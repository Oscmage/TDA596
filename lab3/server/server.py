# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: John Doe
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
from threading import Thread

from bottle import Bottle, run, request, template, HTTPResponse
import requests


class Board:
    '''
    This class represents a blackboard. 
    You can add an element, delete, modify and get all entries on the blackboard
    '''

    def __init__(self):
        self.seq_num = 0
        self.entries = {}

    def add(self, entry_id, entry, ip):
        '''
        Adds a new element to the board and increase the seq num by one.
        '''
        entries = self.entries.get(entry_id)
        new_dict_entry = {'entry': entry, 'ip': ip}
        if entries:
            entries.append(new_dict_entry)
            entries.sort(key=lambda k: k['ip'])
        else:
            # First time adding an element with this entry id
            l = [new_dict_entry]
            entries[entry_id] = l
        if entry_id > self.seq_num:
            self.seq_num = entry_id + 1

        return entry_id

    def delete(self, id, ip):
        '''
        Deletes the element from entries
        '''

        del self.entries[id]
        return True

    def modify(self, id, entry):
        '''
        Modifies the entry for the specified id.
        '''
        self.entries[id] = entry
        return True

    def getEntries(self):
        '''
        Returns all entries
        '''
        return self.entries

    def updateSeqNum(self, new_seq_num):
        if self.seq_num > new_seq_num:
            raise ValueError(
                "New Sequence Number can't be lower than the existing one")
        self.seq_num = new_seq_num


# --------------------
# CONSTANTS
# -----------------
ADD = "add"
MODIFY = "modify"
DELETE = "delete"

# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = Board()

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_id, vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post(
                    'http://{}{}'.format(vessel_ip, path), json=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        if not success:
            print "\n\nCould not contact vessel {}\n\n".format(vessel_id)

    def propagate_to_vessels_in_thread(path, payload=None, req='POST'):
        global vessel_list, node_id

        # Loop over vessels
        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id:  # don't propagate to yourself
                # Start a thread for each propagation
                t = Thread(target=contact_vessel, args=(
                    vessel_id, vessel_ip, path, payload, req))
                t.daemon = True
                t.start()

    def propagate_to_vessels(action, id, payload=None):
        # Validate input
        if (id == None):
            return False

        # Check action
        path = None
        base_string = '/propagate/{}/{}'
        if (action == ADD):
            path = base_string.format(ADD, id)

        if (action == MODIFY):
            path = base_string.format(MODIFY, id)

        if (action == DELETE):
            path = base_string.format(DELETE, id)

        # Invalid action/Not supported
        if (path == None):
            return False

        # Propagate to all vessels in a thread for each request.
        propagate_to_vessels_in_thread(path, payload)
        return True

    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------

    @app.route('/')
    def index():
        global board, node_id
        entries = board.getEntries()
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(entries.iteritems()), members_name_string='YOUR NAME')

    @app.get('/board')
    def get_board():
        global board, node_id
        entries = board.getEntries()
        return template('server/boardcontents_template.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(entries.iteritems()))
    # ------------------------------------------------------------------------------------------------------

    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id
        try:
            # Retrieve the entry from the form
            new_entry = request.forms.get('entry')
            # Get the id from the board and make sure everything went ok.
            element_id = board.add(new_entry)
            if (element_id < 0):
                return format_response(500, 'Failed to create new entry')

            # Propagate the new entry to other vessels
            payload = {'entry': new_entry}
            propagate_to_vessels(ADD, element_id, payload)
            return format_response(200)
        except Exception as e:
            print e
        return format_response(400)

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        # Try to retrieve the delete field from the form and cast to int.
        delete_or_modify = None
        try:
            delete_or_modify = int(request.forms.get('delete'))
        except Exception as e:
            print(e)
            return format_response(400, 'Could not parse delete status from form')

        # Try to retrieve the entry from the form.
        entry = request.forms.get('entry')
        if (entry == None):
            return format_response(400, 'Form needs to contain entry')

        # Make sure we have the delete_or_modify field retrieved.
        if (delete_or_modify != None):
            # Modify code
            if delete_or_modify == 0:
                # Modify and propagate modify to other vessels.
                board.modify(element_id, entry)
                payload = {'entry': entry}
                propagate_to_vessels(MODIFY, element_id, payload)
                return format_response(200)

            # Delete code
            if delete_or_modify == 1:
                # Dlete and propagate to other vessels.
                board.delete(element_id)
                propagate_to_vessels(DELETE, element_id)
                return format_response(200)
        return format_response(400, 'Invalid delete status, should be either 0 or 1')

    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        # Try to parse the element_id as an int.
        try:
            element_id = int(element_id)
        except Exception as e:
            print e
            return format_response(400, 'Element id needs to be an integer')
        # ADD or Modify action
        if (action in [ADD, MODIFY]):
            # Try to retrieve entry from propagation
            entry = None
            try:
                json_dict = request.json
                entry = json_dict.get('entry')

            except Exception as e:
                # Can't parse entry from response
                print e
                return format_response(400, 'Could not retrieve entry from json')

            # Make sure we have an entry
            if (entry == None):
                print 'Entry none'

            if (action == ADD):
                print 'Adding element'
                board.add(entry)
                return format_response(200)
            if (action == MODIFY):
                print 'Modify element'
                board.modify(element_id, entry)
                return format_response(200)

        # Delete action
        if (action == DELETE):
            board.delete(element_id)
            print 'Delete element'
            return format_response(200)
        return format_response(400, 'Not a valid action')

    def format_response(status_code, message=''):
        '''
        Simple function for formatting response code.
        '''
        if status_code == 200:
            return HTTPResponse(status=200)
        return HTTPResponse(status=status_code, body={'message': message})
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code

    def main():
        global vessel_list, node_id, app
        port = 80
        parser = argparse.ArgumentParser(
            description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid',
                            default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1,
                            type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            traceback.print_exc()
            print 'error'
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
    traceback.print_exc()
    while True:
        time.sleep(60.)
