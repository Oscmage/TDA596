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
# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()
    tot_nodes = 4  # TODO Make this properly
    status = {}  # Step 1, keeps track of votes received, node_id -> vote
    result_vectors = {}  # Step 2, keeps track of vectors received, node_id -> vectors
    ATTACK = "ATTACK"
    RETREAT = "RETREAT"
    BYZANTINE = "BYZANTINE"

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------

    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
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
        return success

    def propagate_to_vessels(path, payload=None, req='POST'):
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id:  # don't propagate to yourself
                # Start a thread for each propagation
                t = Thread(target=contact_vessel, args=(
                        vessel_ip, path, payload, req))
                t.daemon = True
                t.start()

    def propogate_client_vote(decision, node_id):
        path = "/propagate/{}/{}".format(decision, node_id)
        propagate_to_vessels(path)

    def propogate_result(node_id):
        payload = {'status': status}
        path = "/propagate/result/{}".format(node_id)
        propagate_to_vessels(path, payload)

    def get_result_vector():
        result_vector = []
        attack = None
        retreat = None
        # Loop over each position in each node vector.
        for i in range(0, 4):
            # Count for each position in the final vector, need to reset for each position
            attack = 0
            retreat = 0
            for k, val in result_vectors:
                if val[i] == ATTACK:
                    attack += 1
                else:
                    retreat += 1
            # Determine result for each position in the vector.
            if attack >= retreat:
                result_vector.append(ATTACK)
            else:
                result_vector.append(RETREAT)
        return result_vector

    def determine_result():
        result_vector = get_result_vector()
        result = None
        attack = 0
        retreat = 0
        for v in result_vector:
            if v == ATTACK:
                attack += 1
            else:
                retreat += 1

        # Decide final winner.
        if attack >= retreat:
            result = ATTACK
        else:
            result = RETREAT
        return result, result_vector

    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------

    @app.route('/')
    def index():
        global node_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), members_name_string='YOUR NAME')

    @app.get('/vote/result')
    def get_result():
        global node_id
        # Have received all other nodes vectors
        if len(result_vectors) == tot_nodes - 1:
            return determine_result

        # If len (result) == tot_nodes returnera vettigt
        # Annars returnera att vi väntar

    @app.post('/vote/attack')
    def client_attack_received():
        global node_id
        status[node_id] = ATTACK
        propogate_client_vote(ATTACK, node_id)
        return format_response(200)

    @app.post('/vote/retreat')
    def client_retreat_received():
        global node_id
        status[node_id] = RETREAT
        propogate_client_vote(RETREAT, node_id)
        return format_response(200)

    @app.post('/vote/byzantine')
    def client_byzantine_received():
        global node_id
        # TODO MAKE UP YOUR MIND
        status[node_id] = "Something something"
        propogate_client_vote("Something", node_id)
        return format_response(200)

    #Propagation step 2
    @app.post('/propagate/result/<node_id>')
    def propagation_result_received(node_id):
        json_dict = request.json
        status_dict_for_node = json_dict.get('status')
        result_vectors[node_id] = status_dict_for_node
        return format_response(200)


    # Propagation step 1
    @app.post('/propagate/<vote>/<external_node_id>')
    def propagation_received(vote, external_node_id):
        global node_id
        status[external_node_id] = vote
        if len(status) == tot_nodes:
            print(status)
            propogate_result(node_id)
        return format_response(200)

 
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
        for i in range(1, args.nbv+1):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
    traceback.print_exc()
    while True:
        time.sleep(60.)
