import sys
from wit import Wit

import json

import inspect

if len(sys.argv) < 3:
    print('usage: python ' + sys.argv[0] + ' <wit-token>' + ' Case-Short-Name' + ' [-nv]')
    exit(1)
access_token = sys.argv[1]
case_short_name = sys.argv[2]

print( '\nWelcome to the CASE INTERVIEWING App. Press Ctrl+C to exit')

if len(sys.argv) == 4:
    verbose = 0
    print( '\nVerbose mode OFF\n')
else:
    verbose = 1
    print( '\nVerbose mode ON')

if verbose: print( '\nInit...')

state = "I"  # Intro is start state"
prev_state = "Unknown"
micro_state = 'Unknown'
cursor = 'Unknown'

case_json_file_name = case_short_name + '.json'

with open(case_json_file_name) as data_file:
    data = json.load(data_file)
    if verbose: print( '\n JSON FILE READ OK\n')

#######################################################

def first_entity_value(entities, entity):
    if entity not in entities:
        return None
    val = entities[entity][0]['value']
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val

def second_entity_value(entities, entity):
    if entity not in entities:
        return None
    if len(entities[entity]) < 2 : # return if it has no 2nd value
        return None
    val = entities[entity][1]['value'] # return second value of the variable
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val

def entity_contains(entities, entity):
    for ent in entities:
        #print(ent)
        if (ent == entity):
            #print("found")
            return True
    #print("not found")
    return False


def send(request, response):
    if verbose:
        print(('\n'+response['text'] \
            +'\n\nrequest:'+str(request) \
            +'\n\nresponse:'+str(response)+'\n'))
    else:
        print( response['text'] + '\n')

#######################################################

def explain_case(request):
    global state, prev_state, micro_state, cursor, verbose
    context = request['context']
    entities = request['entities']

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))

    if state != "I": # we should come here only in I state ideally
        if verbose: print( '\nUnexpected state in explain case or Unlearnt story/intent - train inside wit. Should be only I')
        if context.get('response_text') is not None:
            del context['response_text']
        return context

    # I--> DCS state transition function

    prev_state = state;
    state = 'DCS'
    if verbose:
        print( 'STATE TRANSITION: from %s to %s' % (prev_state, state))
        print( 'CASE TITLE:' + data["states"][state]["title"])

    context['response_text'] = data["states"][state]["title"]
    micro_state = 'title'
    cursor = 'title_stated'

    return context

#######################################################

def more_info(request):
    context = request['context']
    entities = request['entities']
    global state, prev_state, micro_state, cursor

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))

    if state == "Unknown":
        if verbose: print( 'Unknown State')
    elif state == "I":
        context['response_text'] = data["states"]["I"]["app_scope"]
        micro_state = 'app_scope'
        cursor = 'app_scope_stated'
    elif state == "DCS":
        context['response_text'] = data["states"]["DCS"]["overview"]
        micro_state = 'overview'
        cursor = 'overview_stated'

    return context

################################
# we come here for anything that needs programmatic response text.

def get_info(request):
    context = request['context']
    entities = request['entities']
    global state, prev_state, micro_state, cursor

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))
        print( 'ENTITIES:')
        print( entities)
        print( 'CONTEXT:')
        print( context)

    # clean prev resp txt
    if context.get('response_text') is not None:
        del context['response_text']

    if state == "I" or state =="Unknown": # shouldnt come here in non DCS/DDA states. those are handled by wit or other routines
        if verbose: print( '\nUnexpected state: state:%s. Expected: DCS'% (state))
        return context

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    #get_info is key param to be acted/responded upon based on context. shouldnt be null. wit needs more keyw training in this case
    get_info_val = first_entity_value(entities, 'get_info')
    if get_info_val is None:
        if verbose:   print( 'unexpected error: get_info entity not present. train wit more')
        context['response_text'] = "unexpected error: get_info entity not present. train wit more"
        return context

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# DCS handling - currently handles 1 line query responses. TODO: add multi line queries as need be. enough for proto

    if state == "DCS":
        if verbose:  print( 'DCS: get_info() \n')
        context['response_text'] = data["states"]["DCS"][get_info_val]
        micro_state = get_info_val
        cursor = get_info_val
        return context

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    if state == "DDA":
        if verbose:    print( 'DDA: get_info() \n')
#            print( '*** DDA STRUCT ***\n')
#            print( data["states"]["DDA"])

        # sentence type states if its a question, statement, positive, negative, etc..  used in comprehension. normally must be present.
        # train wit if not present.  mandatory in DDA sentences
        sentenceType = first_entity_value(entities, 'sentence_type')
        if sentenceType is None:
            if verbose:    print( 'unexpected error: sentenceType entity not present. train wit more')
            context['response_text'] = "unexpected error: sentenceType entity not present. train wit more"
            return context
        if verbose:   print( '***sentence-type:' + sentenceType + '  ***get_info:' + get_info_val + '\n')

        # action is the verb acting on the keyw. ex: increase/decrease on market-share for ex: this is used to make sense in context
        # train wit if not present. mandatory in DDA sentences
        action = first_entity_value(entities, 'action')
        if action is None:
            if verbose:  print( 'unexpected error: action entity not present. train wit more')
            context['response_text'] = "unexpected error: action entity not present. train wit more"
            return context
        if verbose:  print( '***action:' + action + '\n')

        cur_keyw = data["states"]["DDA"]["cur-compr-keyw"]
        if verbose:  print( '***curkeyw: ' + cur_keyw + '\n')

        if cur_keyw == 'NONE': # new keyw comprehension
            if verbose:  print( '***SETTING New Comprehension Keyword:  ' + get_info_val + '\n')
            data["states"]["DDA"]["comprehension-state"]='STILL-LISTENING-ON-KEYW'
            data["states"]["DDA"]["cur-compr-keyw"] = get_info_val
            data["states"]["DDA"]["wrong_match_count"] = 0
        else:
            if verbose:
                print( '***CONTINUE PREV Comprehension Keyword comprehension:  ' + cur_keyw +  '\n')
                print( '***no-match count  ' + str(data["states"]["DDA"]["wrong_match_count"]) +  '\n')
                print( '***no-match bailout count  ' + str(data["states"]["DDA"]["matchfail_bailout_count"]) + '\n')

        match=False;
        for i, j in enumerate(data["states"]["DDA"]["right-answers"]):
            if (j == get_info_val):
                if data["states"]["DDA"]["right-answers"][get_info_val]["action"] == action:
                    match=True

        if verbose:  print( '**Match' + str(match))

        #[i for i, j in enumerate(data["states"]["DDA"][cur_keyw]["right-answers"]) if (j == get_info_val) &&
        #        data["states"]["DDA"][cur_keyw]["right-answers"][get_info_val]["action"] == action ]

        #if get_info_val in data["states"]["DDA"][cur_keyw]["right-answers"]:
        if match:
            # user said something thats in template right answers
            if verbose:  print( '*sub-keyw & *action match hit..' + get_info_val + '  ' + action + '\n')
            # hitcount incremented later below after checking context match if any existing. else incremented below
            context['response_text'] = data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] + ". Please share some more info on this.."

# !!!  SECOND PART OF SENTENCE PARSING

            sentence2_type = second_entity_value(entities, 'sentence_type')
            if verbose:  print( '***sentence2-type:' + str(sentence2_type) + '\n')

            if sentence2_type is None: # no 2nd part of sentence. need more info
                if verbose: print( 'no sentence2 part\n')

                # when still on prev keyw-s0 (that had no s2) and another s1 comes (with no s2), need to co-relate prev s1 and s2 to change states or keep still listening.
                if data["states"]["DDA"]["comprehension-state"] == "STILL-LISTENING-ON-KEYW":
                    # match prev context S0. ex: market share increase (S0-prev context).  sell online (S1)
                    if verbose: print( 'A:In LISTENING: checking match making sense\n')

                    # to handle case of S0 processing, when there is no s2 and listening is turned on already above. skip same S0 check
                    if data["states"]["DDA"]["cur-compr-keyw"] == get_info_val: return context

                    matchMakesSense = False

                    for i, j in enumerate(data["states"]["DDA"]["right-answers"]):
                        if (j == get_info_val):
                            if data["states"]["DDA"]["right-answers"][get_info_val]["parent"] == data["states"]["DDA"]["cur-compr-keyw"]:
                                matchMakesSense=True

                    if verbose:  print( '**A:matchMakesSense' + str(matchMakesSense) + '\n')

                    if matchMakesSense:
                        if verbose: print( 'A:s1 making sense with s0/context found!\n')
                        data["states"]["DDA"]["right-answers"][get_info_val]["hit-count"] += 1
                        keyw = data["states"]["DDA"]["cur-compr-keyw"]
                        context['response_text'] = data["states"]["DDA"]["right-answers"][keyw]["rsp"] + "  " + data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] +  ". Thats very nice.."
                        # we got S1 making sense with prev context. so can move to some new keyword/topic
                        if verbose:  print( '*** A: Resetting New Comprehension Keyword State:  ' + '\n')
                        data["states"]["DDA"]["comprehension-state"]='NONE'
                        data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                        data["states"]["DDA"]["wrong_match_count"] = 0
                        return context
                    else: # s1 matched right answers, but not making sense with cur-keyw being listened
                        if verbose: print( 'A: sentence1 not making sense with sentence0/context. pl check if json backend needs addition\n')
                        data["states"]["DDA"]["wrong_match_count"] += 1
                        keyw = data["states"]["DDA"]["cur-compr-keyw"]
                        context['response_text'] =data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] + "..Ok.. and previously..." + data["states"]["DDA"]["right-answers"][keyw]["rsp"] + "  " +  ". Please share some more information related to this to make it complete.."
                        # To avoid getting stuck on a keyword and not making progress, bailout if necessary
                        if data["states"]["DDA"]["comprehension-state"] == "STILL-LISTENING-ON-KEYW":
                            if data["states"]["DDA"]["wrong_match_count"] >= data["states"]["DDA"]["matchfail_bailout_count"]:
                                if verbose: print( '*** A: BAILING out on keyword comprehension after no match till bailout count' + '\n')
                                if verbose: print( '*** A: BAILOUT: Resetting New Comprehension Keyword State:  ' + '\n')
                                data["states"]["DDA"]["comprehension-state"]='NONE'
                                data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                                data["states"]["DDA"]["wrong_match_count"] = 0
                    return context
                else: # not in LISTENING state
                    if verbose: print( 'A: s1 match in right answers. NOT LISTENING mode\n')
                    data["states"]["DDA"]["right-answers"][get_info_val]["hit-count"] += 1
                    context['response_text'] = data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] + "  " + ". Thats good.."
                    # we got sentence1 making sense. so can move to some new keyword/topic
                    if verbose:  print( '*** A: s1 match. Resetting New Comprehension Keyword State:  ' + '\n')
                    data["states"]["DDA"]["comprehension-state"]='NONE'
                    data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                    data["states"]["DDA"]["wrong_match_count"] = 0
                return context

            # second part sentence valid if we come here. parse and check
            # parse second part of sentence to see if it connects with 1st part of sentence to form full sense
            get_info_val2 = second_entity_value(entities, 'get_info')
            if verbose:  print( '***get_info2:' + str(get_info_val2) + '\n')
            if get_info_val2 is None:
                if verbose:  print( 'unexpected error: get_info2 entity not present. train wit more')
                return context

            # valid getinfoval2, check action
            action2 = second_entity_value(entities, 'action')
            if action2 is None:
                if verbose:  print( 'unexpected error: action2 entity not present. train wit more')
                return context
            if verbose:  print( '***action2:' + str(action2) + '\n')

            match=False;

            for i, j in enumerate(data["states"]["DDA"]["right-answers"]):
                if (j == get_info_val2):
                    if data["states"]["DDA"]["right-answers"][get_info_val2]["action"] == action2:
                        match=True

            if verbose:  print( '**Match2' + str(match))

            if match: # sentence2 has a match in right answers
                if verbose:  print( '*sentence2: sub-keyw & *action match hit..' + get_info_val2 + '  ' + action2 + '\n')

                if data["states"]["DDA"]["comprehension-state"] == "STILL-LISTENING-ON-KEYW":
                    # related S1, S2 keywords connector in match logic. ex: market increase by selling online
                    if verbose: print( 'In LISTENING: checking match making sense\n')
                    matchMakesSense = False

                    for i, j in enumerate(data["states"]["DDA"]["right-answers"]):
                        if (j == get_info_val2):
                            if data["states"]["DDA"]["right-answers"][get_info_val2]["parent"] == data["states"]["DDA"]["cur-compr-keyw"]:
                                matchMakesSense=True

                    if verbose:  print( '**matchMakesSense' + str(matchMakesSense) + '\n')

                    if matchMakesSense:
                        if verbose: print( 's2 making sense with s1/context found!\n')
                        data["states"]["DDA"]["right-answers"][get_info_val2]["hit-count"] += 1
                        context['response_text'] = data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] + "  " + data["states"]["DDA"]["right-answers"][get_info_val2]["rsp"] +  ". Thats very good.."
                        # we got sentence2 making sense. so can move to some new keyword/topic
                        if verbose:  print( '*** Resetting New Comprehension Keyword State:  ' + '\n')
                        data["states"]["DDA"]["comprehension-state"]='NONE'
                        data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                        data["states"]["DDA"]["wrong_match_count"] = 0
                        return context
                    else: # s2 matched right answers, but not making sense with cur-keyw being listened
                        if verbose: print( 'sentence2 not making sense with sentence1/context. pl check if json backend needs addition\n')
                        data["states"]["DDA"]["wrong_match_count"] += 1
                        # To avoid getting stuck on a keyword and not making progress, bailout if necessary
                        if data["states"]["DDA"]["comprehension-state"] == "STILL-LISTENING-ON-KEYW":
                            if data["states"]["DDA"]["wrong_match_count"] >= data["states"]["DDA"]["matchfail_bailout_count"]:
                                if verbose: print( '*** BAILING out on keyword comprehension after no match till bailout count' + '\n')
                                if verbose: print( '*** BAILOUT: Resetting New Comprehension Keyword State:  ' + '\n')
                                data["states"]["DDA"]["comprehension-state"]='NONE'
                                data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                                data["states"]["DDA"]["wrong_match_count"] = 0
                    return context
                else: # not in LISTENING state, ideally we shouldnt come here when s2 is present as s1 wud make listeneing ON
                    if verbose: print( 's2 match in right answers. NOT LISTENING mode\n')
                    data["states"]["DDA"]["right-answers"][get_info_val2]["hit-count"] += 1
                    context['response_text'] = data["states"]["DDA"]["right-answers"][get_info_val2]["rsp"] +  ". Thats nice.."
                    # we got sentence2 in right answers. so can move to some new keyword/topic
                    if verbose:  print( '*** s2 match. Resetting New Comprehension Keyword State:  ' + '\n')
                    data["states"]["DDA"]["comprehension-state"]='NONE'
                    data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                    data["states"]["DDA"]["wrong_match_count"] = 0
                    return context
            else: # sentence2 no match in right answers
                if verbose:  print( 'unknown sentence2 detected. check if backend json needs addition' + '\n')
                data["states"]["DDA"]["wrong_match_count"] += 1
                context['response_text'] = "Previously..." + data["states"]["DDA"]["right-answers"][get_info_val]["rsp"] + "  Now...  " +  ". Please share some more info around this to make it more complete.."
                # To avoid getting stuck on a keyword and not making progress, bailout if necessary
                if data["states"]["DDA"]["comprehension-state"] == "STILL-LISTENING-ON-KEYW":
                    if data["states"]["DDA"]["wrong_match_count"] >= data["states"]["DDA"]["matchfail_bailout_count"]:
                        if verbose: print( '*** BAILING out on keyword comprehension after no match till bailout count' + '\n')
                        if verbose: print( '*** BAILOUT: Resetting New Comprehension Keyword State:  ' + '\n')
                        data["states"]["DDA"]["comprehension-state"]='NONE'
                        data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
                        data["states"]["DDA"]["wrong_match_count"] = 0
                return context
        else: # no match on sentence1 keyw.
            if verbose:  print( 'unknown sentence1 detected. check if backend json needs addition' + '\n')
            context['response_text'] = data["states"]["DDA"]["tell-me-more"]
            if verbose: print( '*** RESETTING New Comprehension Keyword State on no match1:  ' + '\n')
            data["states"]["DDA"]["comprehension-state"]='NONE'
            data["states"]["DDA"]["cur-compr-keyw"] = 'NONE'
            data["states"]["DDA"]["wrong_match_count"] = 0

        return context

#######################################################

def solve_case(request):
    context = request['context']
    entities = request['entities']
    global state, prev_state, micro_state, cursor

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))
        print( 'ENTITIES:')
        print( entities)
        print( 'CONTEXT:')
        print( context)

#    if state != "DCS":
#        if verbose:
#            print( '\nUnexpected state: state:%s. Expected: DCS'% (state))
#        if context.get('response_text') is not None:
#            del context['response_text']
#        return context

    # DCS-->DDA state transition function

    prev_state = state;
    state = 'DDA'
    if verbose:  print( 'STATE TRANSITION: from %s to %s' % (prev_state, state))

    context['response_text'] = data["states"]["DDA"]["solve_case"]
    micro_state = 'solve_case_start'
    cursor = 'solve_case'

    return context

#######################################################

def judge(request):
    context = request['context']
    entities = request['entities']
    global state, prev_state, micro_state, cursor

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))
        print( 'ENTITIES:')
        print( entities)
        print( 'CONTEXT:')
        print( context)

    class judgeInfoEntry:
        topic = ''
        topic_string = ''
        hit_count = 0
        total_children = 0
        def __init__(self, topic, topic_string, hit_count, total_children):
            self.topic = topic
            self.topic_string = topic_string
            self.hit_count = hit_count
            self.total_children = total_children

    judge_info = []

    for i, j in enumerate(data["states"]["DDA"]["right-answers"]):
        parent = data["states"]["DDA"]["right-answers"][j]["parent"]
        if parent != 'None':
            # add parent keyw to judge info if not present

            present=False
            for i in range(len(judge_info)):
                if judge_info[i].topic == parent: present=True

            if not present:
                if verbose: print( '***adding parent kw:%s to judge info \n' % (parent))
                judge_info.append(judgeInfoEntry(parent, data["states"]["DDA"]["right-answers"][parent]["topic-string"], 0, 0))

            idx=0
            for i in range(len(judge_info)):
                if judge_info[i].topic == parent:
                    idx=i
                    break

            if data["states"]["DDA"]["right-answers"][j]["hit-count"] > 0:
                if verbose: print( 'child topic: %s with positive hitcount. updating judge info \n' % j)
                judge_info[idx].hit_count += data["states"]["DDA"]["right-answers"][j]["hit-count"]

            # increment total children count for that parent keyw
            judge_info[idx].total_children +=  1

    for idx in range(len(judge_info)):
        if verbose: print( 'JUDGE INFO: %s, %s, %d, %d\n' % (judge_info[idx].topic, judge_info[idx].topic_string, judge_info[idx].hit_count, judge_info[idx].total_children))

    # Summarize the judge info into wit response text
    context['response_text'] = '*** JUDGE SUMMARY PER TOPIC/AREA ***\n\n'

    for i in range(len(judge_info)):
        context['response_text'] += '** ' + judge_info[i].topic_string + '** ' + '\t\t' + \
            '## Total hits: ' + str(judge_info[i].hit_count) + ' ' + \
            '## Topic Coverage Percentage: ' + str((100 * judge_info[i].hit_count)/judge_info[i].total_children) + '%' \
            + '\n'

    return context

#######################################################


actions = {
    'send': send,
    'explain_case': explain_case,
    'more_info': more_info,
    'get_info': get_info,
    'solve_case': solve_case,
    'judge': judge
}

#######################################################

def handleMessage(request):
    request['context'] = {} # set for testing as its not coming from wit appears in latest version

    entities = request['entities']
    context = request['context']

    #context['response_text'] = "" # test setting
    context['response_text'] = ""

    global state, prev_state, micro_state, cursor

    if verbose:
        print( '\nIn:' + inspect.stack()[0][3])
        print( 'State:%s, Prev State:%s, micro_state:%s, cursor:%s' % (state, prev_state, micro_state, cursor))
        print(request)
        print( 'ENTITIES:')
        print( entities)
        print( 'CONTEXT:')
        print( context)

    # clean prev resp txt
    #if context.get('response_text') is not None:
    #    del context['response_text']

    if (entity_contains(entities,"welcome_greeting") or entity_contains(entities,"bot_scope")):
        context = more_info(request)

    elif (entity_contains(entities,"start_case")):
        context = explain_case(request)
        
    elif (entity_contains(entities,"solving")):
        context = solve_case(request)

    elif (entity_contains(entities,"judge")):
        context = judge(request)

    elif (entity_contains(entities,"sentence_type") or entity_contains(entities,"get_info")):
        context = get_info(request)

    elif (entity_contains(entities,"want_more_info")):
        context = more_info(request)    

    elif (entity_contains(entities,"exit_greeting")):
        judge(request)
        context['response_text'] = data["states"]["JUDGE"]["exit"]
        if verbose: print(data["states"]["JUDGE"]["exit"])
        sys.exit()

    #print("## RSP:")
    #print(context['response_text'])

    return context['response_text']


###################################################################

# client = Wit(access_token=access_token, actions=actions)
client = Wit(access_token=access_token)

client.interactive(handleMessage)
#client.interactive()
