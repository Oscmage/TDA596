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
        self.delete_queue = {}
        self.modify_queue = {}

    def add(self, entry_id, entry, ip):
        '''
        Adds a new element to the board and increase the seq num by one. 
        Uses some logic to check if the added element has pening delete or modifies. 
        Also uses a inner method for actualy adding the entry to the bord.
        '''
        entry_id = int(entry_id)
        # Check if in delete queue, if so, do nothing and remove it from the delete queue
        inDeleteQueue = self.inDeleteQueue(entry_id, entry, ip)
        # If in modifyQueue
        inModifyQueue = self.inModifyQueue(entry_id, entry, ip)

        # Only consider adding element if not in delete queue
        if not inDeleteQueue:
            # If in modifyQueue add the modified version of the element.
            if inModifyQueue:
                self.add_inner(entry_id, inModifyQueue, ip)
            else:
                # Not in modifyQueue or deleteQueue, add the element.
                self.add_inner(entry_id, entry, ip)

    def add_inner(self, entry_id, entry, ip):
        '''
        Inner add-method, does the actual adding of new elements to the board and increase the seq num by one.
        '''
        entry_id = int(entry_id)
        entries = self.entries.get(entry_id)
        if entries:
            entries[ip] = entry
        else:
            d = {ip: entry}
            self.entries[entry_id] = d
        if entry_id >= self.seq_num:
            self.seq_num = entry_id + 1
        return entry_id

    # Method inDeleteQueue() will return true if it WAS in the queue, it will also remove the item from the queue
    def inDeleteQueue(self, entry_id, entry, ip):
        entry_id = int(entry_id)

        id_dict = self.delete_queue.get(entry_id)
        if id_dict:
            entry = id_dict.get(ip)
            if entry:
                # There is a delete pending for the entry_id and ip
                # Don't add it and remove from queue
                del id_dict[ip]
                return True
        return False

    # Method inModifyQueue() will return the modified entry if it WAS in the queue, it will also remove the item from the queue
    def inModifyQueue(self, entry_id, entry, ip):
        entry_id = int(entry_id)
        id_dict = self.modify_queue.get(entry_id)
        if id_dict:
            entry = id_dict.get(ip)
            if entry:
                # There is a modify pending for the entry_id and ip
                # return the modified and correct entry and remove from queue
                del id_dict[ip]
                return entry
        return None

    def delete(self, entry_id, ip):
        '''
        Deletes the element from entries
        '''
        entry_id = int(entry_id)
        # Find the dict for an entry_id
        entry_dict = self.entries.get(entry_id)
        if entry_dict:
            # Get entry for that ip
            entry = entry_dict.get(ip)
            if entry:
                # Delete entry if exists
                del entry_dict[ip]
                if len(entry_dict) == 0:
                    del self.entries[entry_id]
            else:
                self.add_to_delete_queue(entry_id, ip)
        else:
            self.add_to_delete_queue(entry_id, ip)
        return True

    def add_to_delete_queue(self, entry_id, ip):
        # There is no entry, will come later
        # Get delete set for that entry_entry_id
        delete_dict = self.delete_queue.get(entry_id)
        if delete_dict:
            # If there is an delete set for that entry_entry_id append the ip
            delete_dict[ip] = True
        else:
            # Create a new delete set for that entry_entry_id
            self.delete_queue[entry_id] = {ip: True}

    def modify(self, entry_id, ip, entry):
        '''
        Modifies the entry for the specified entry_id.
        '''
        entry_id = int(entry_id)
        # Get entries dict for that entry_id
        entry_dict = self.entries.get(entry_id)
        if entry_dict:
            # Get a specific entry for an ip
            old_entry = entry_dict.get(ip)
            if old_entry:
                # There is an entry for this ip, so we can modify
                entry_dict[ip] = entry
            else:
                # There is no entry, might come later, add to queue
                self.modify_queue[entry_id] = {ip: entry}
        else:
            self.modify_queue[entry_id] = {ip: entry}
        return True

    def getEntries(self):
        '''
        Returns all entries
        '''
        temp = {}
        for k, v in self.entries.iteritems():
            temp[k] = sorted(v.iteritems())
        big_arr = sorted(temp.iteritems())
        arr = []
        for i in range(0, len(big_arr)):
            arr.append(big_arr[i][1])
        return arr

    def get_seq_num(self):
        return self.seq_num


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
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=entries, members_name_string='YOUR NAME')

    @app.get('/board')
    def get_board():
        global board, node_id
        entries = board.getEntries()
        print(entries)
        return template('server/boardcontents_template.tpl', board_title='Vessel {}'.format(node_id), board_dict=entries)
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
            id = board.get_seq_num()
            board.add(id, new_entry, node_id)

            # Propagate the new entry to other vessels
            payload = {'entry': new_entry, 'node_id': node_id}
            propagate_to_vessels(ADD, id, payload)
            return format_response(200)
        except Exception as e:
            print e
        return format_response(400)

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        global board, node_id
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
            return format_response(400, 'Form needs to contain entry and node_id')

        # Make sure we have the delete_or_modify field retrieved.
        if (delete_or_modify != None):
            # Modify code
            if delete_or_modify == 0:
                # Modify and propagate modify to other vessels.
                board.add(element_id, entry, node_id)
                payload = {'entry': entry, 'node_id': node_id}
                propagate_to_vessels(MODIFY, element_id, payload)
                return format_response(200)

            # Delete code
            if delete_or_modify == 1:
                # Dlete and propagate to other vessels.
                board.delete(element_id, node_id)
                payload = {'node_id': node_id}
                propagate_to_vessels(DELETE, element_id, payload)
                return format_response(200)
        return format_response(400, 'Invalid delete status, should be either 0 or 1')

    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        # Try to parse the element_id as an int.
        node_id = None
        json_dict = request.json
        try:
            element_id = int(element_id)
            node_id = json_dict.get('node_id')
        except Exception as e:
            print e
            return format_response(400, 'Element id needs to be an integer')

        if (node_id == None):
            print 'Node id is none'

        # ADD or Modify actiona
        if (action in [ADD, MODIFY]):
            # Try to retrieve entry from propagation
            entry = None
            try:
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
                board.add(element_id, entry, node_id)
                return format_response(200)
            if (action == MODIFY):
                print 'Modify element'
                board.modify(element_id, node_id, entry)
                return format_response(200)

        # Delete action
        if (action == DELETE):
            board.delete(element_id, node_id)
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
