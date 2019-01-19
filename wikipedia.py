#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import wikipedia

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

LANG = 'fr'

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):

    ERROR_SENTENCES = {
                'en': {
                    'DisambiguationError': u"Many pages was found on Wikipedia for your query: ",
                    'PageError': u"Wikipedia no matched your query"
                },
                'fr': {
                    'DisambiguationError': u"Plusieurs pages on été trouvé sur wikipédia pour votre recherche, la quel souaitez vous: ",
                    'PageError': u"Aucune page n'a été trouvé sur wikipédia pour votre recherche"
                },
                'es': {
                    'DisambiguationError': u"Muchas pagas Wikipedia ",
                    'PageError': u""
                }
            }
    if intentMessage.slots.article_indicator:
            query = intentMessage.slots.article_indicator[0].slot_value.value.value
    else:
            print('article_indicator not found')
            hermes.publish_end_session(intentMessage.session_id, '')


    sentences = None
    if intentMessage.slots.sentences:
            sentences = intentMessage.slots.sentences[0].slot_value.value

        # Do the summary search

    session_continue = False
    wikipedia.set_lang(LANG)

    print('Type query: {}, query: {}'.format(type(query), str(query)))
    print('intentMessage.slots: {}'.format(intentMessage.slots))

    try:
            result = wikipedia.summary(str(query), auto_suggest=True, sentences=sentences)

    #except wikipedia.exceptions.DisambiguationError, e:
    except wikipedia.exceptions.DisambiguationError:
            # Exception raised when a page resolves to a Disambiguation page.
            # The options property contains a list of titles of Wikipedia pages that the query may refer to.
            # may_refer = e.options

            # Removing duplicates in lists.
            # may_refer = list(set(may_refer))
            # session_continue = True
            result = '{}{}'.format(ERROR_SENTENCES[LANG]['DisambiguationError'], str(e.options))

    except wikipedia.exceptions.PageError:
            # Exception raised when no Wikipedia matched a query.
            result = ERROR_SENTENCES[LANG]['PageError']

    if session_continue:
            print('Session continue')
            publish_continue_session(intentMessage.session_id, result, ['searchWikipediaSummary'])
    else:
            hermes.publish_end_session(intentMessage.session_id, result)



if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("Tealque:searchWikipedia", subscribe_intent_callback) \
         .start()
