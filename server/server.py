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
    def __init__(self):
        self.seq_num = 0
        self.entries = {}

    def add(self, entry):
        entry_id = self.seq_num
        self.entries[entry_id] = entry
        self.seq_num += 1
        return entry_id

    def delete(self, id):
        del self.entries[id]
        return True

    def modify(self, id, entry):
        self.entries[id] = entry
        return True

    def getEntries(self):
        return self.entries


ADD = "add"
MODIFY = "modify"
DELETE = "delete"

# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = Board() 


    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(element, is_propagated_call=False):
        global board, node_id
        try:
            return board.add(element)
        except Exception as e:
            print e
        return -1

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            board.modify(entry_sequence, modified_element)
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            board.delete(entry_sequence)
            success = True
        except Exception as e:
            print e
        return success

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), json=payload)
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
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                if not success:
                    print "\n\nCould not contact vessel {}\n\n".format(vessel_id)

    def propagate_to_vessels_in_thread(action, id, payload = None):
        if (id == None):
            return False

        path = None
        if (action == ADD):
            path = '/propagate/{}/{}'.format(ADD, id)
          
        if (action == MODIFY):
            path = '/propagate/{}/{}'.format(MODIFY, id)

        if (action == DELETE):
            path = '/propagate/{}/{}'.format(DELETE, id)

        t = Thread(target=propagate_to_vessels, args = (path, payload))
        t.daemon = True
        t.start()
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
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(entries.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id
        try:
            new_entry = request.forms.get('entry')
            element_id = add_new_element_to_store(new_entry)
            if (element_id < 0):
                return False

            payload = {'entry': new_entry}
            propagate_to_vessels_in_thread(ADD, element_id, payload)
            return True
        except Exception as e:
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        delete_or_modify = None
        try:
            delete_or_modify = int(request.forms.get('delete'))
        except Exception as e:
            print(e)
            
        entry = request.forms.get('entry')
        if (delete_or_modify != None and entry != None):
            if delete_or_modify == 0:
                modify_element_in_store(element_id, entry)
                propagate_to_vessels_in_thread(MODIFY, element_id,  entry)

            if delete_or_modify == 1:
                delete_element_from_store(element_id)
                propagate_to_vessels_in_thread(DELETE, element_id)

    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        try:
            element_id = int(element_id)
        except Exception as e:
            print e
            return HTTPResponse(status=400)
        if (action in [ADD, MODIFY]):
            entry = None
            try:     
                json_dict = request.json
                entry = json_dict.get('entry')

            except Exception as e:
                # Can't parse entry from response
                print e
                return HTTPResponse(status=400)

            if (entry == None):
                print "Entry none"

            if (action == ADD):
                print "Adding element"
                add_new_element_to_store(entry)
                return HTTPResponse(status=200)
            if (action == MODIFY):
                print "Modify element"
                modify_element_in_store(element_id, entry)
                return HTTPResponse(status=200)

        if (action == DELETE): 
            delete_element_from_store(element_id)
            print "Delete element"
            return HTTPResponse(status=200)
        return HTTPResponse(status=400)
        
        
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app
        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
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