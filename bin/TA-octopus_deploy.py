import os
import platform
import sys
import requests
import logging
import logging.handlers
import splunk
import time
import md5
import json

from splunklib.modularinput import *

# ENVIRONMENTAL INFORMATION
__author__ = 'Coen Meerbeek'
_MI_APP_NAME = 'TA-octopus_deploy'
_SPLUNK_HOME = os.getenv('SPLUNK_HOME')
if _SPLUNK_HOME is None:
    _SPLUNK_HOME = os.getenv('SPLUNKHOME')
if _SPLUNK_HOME is None:
    _SPLUNK_HOME = '/opt/splunk'

_OPERATING_SYSTEM = platform.system()
_APP_HOME = _SPLUNK_HOME + '/etc/apps/' + _MI_APP_NAME
_APP_BIN = _APP_HOME + '/bin'

if _OPERATING_SYSTEM.lower() == 'windows':
    _IS_WINDOWS = True
    _APP_HOME.replace('/', '\\')
    _APP_BIN.replace('/', '\\')

###############################
####### Logger functions ######
###############################


def setup_logging():
    """
    Setup logging

    Log is written to /opt/splunk/var/log/splunk/octopus.log
    """
    logger = logging.getLogger('splunk.octopus')
    logger.setLevel(logging.INFO)
    SPLUNK_HOME = os.environ['SPLUNK_HOME']

    LOGGING_DEFAULT_CONFIG_FILE = os.path.join(_SPLUNK_HOME, 'etc', 'log.cfg')
    LOGGING_LOCAL_CONFIG_FILE = os.path.join(
        _SPLUNK_HOME, 'etc', 'log-local.cfg')
    LOGGING_STANZA_NAME = 'python'
    LOGGING_FILE_NAME = "octopus.log"
    BASE_LOG_PATH = os.path.join('var', 'log', 'splunk')
    LOGGING_FORMAT = "%(asctime)s %(levelname)-s\t%(module)s:%(lineno)d - %(message)s"

    splunk_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(_SPLUNK_HOME, BASE_LOG_PATH, LOGGING_FILE_NAME), mode='a')
    splunk_log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(splunk_log_handler)
    splunk.setupSplunkLogger(logger, LOGGING_DEFAULT_CONFIG_FILE,
                             LOGGING_LOCAL_CONFIG_FILE, LOGGING_STANZA_NAME)

    return logger

###############################
### Checkpointing functions ###
###############################

# creates a checkpoint file to store it's value


def save_checkpoint(checkpoint, checkpoint_dir, event_id):
    logger = setup_logging()
    chk_file = os.path.join(checkpoint_dir, checkpoint)
    logger.info("save_checkpoint: " + chk_file)

    try:
        with open(chk_file, 'w') as f:
            f.write(event_id.strip(' \t\n\r'))
    except IOError as exception:
        logger.error('Could not save checkpoint to: ' + chk_file)

# returns true if the checkpoint file exists


def exists_checkpoint(checkpoint, checkpoint_dir):
    chk_file = os.path.join(checkpoint_dir, checkpoint)

    try:
        open(chk_file, "r").close()
    except:
        # assume that this means the checkpoint is not there
        return False

    return True

# returns last checkpoint or 0


def load_checkpoint(checkpoint, checkpoint_dir):
    logger = setup_logging()
    chk_file = os.path.join(checkpoint_dir, checkpoint)
    logger.info("load_checkpoint: " + chk_file)

    try:
        f = open(chk_file, "r")
        event_id = int(f.readline().strip(' \t\n\r'))
        f.close()
        return event_id
    except:
        return 0

###############################
### Octopus Deploy functions ##
###############################


def getEntries(endpoint, hostname, api_key, use_checkpoint, checkpoint):
    logger = setup_logging()
    logger.info("getEntries: " + time.strftime("%d-%m-%Y %H:%M:%S"))
    octopus_url = "%s/api/%s" % (hostname, endpoint)
    if int(use_checkpoint) == 1:
        checkpoint_dir = os.path.join(
            _SPLUNK_HOME, 'var', 'lib', 'splunk', 'modinputs', 'TA-octopus_deploy')
        last_checkpoint_id = load_checkpoint(checkpoint, checkpoint_dir)
    data = []

    while True:
        response = requests.get(
            url=octopus_url,
            headers={
                "X-Octopus-ApiKey": api_key,
            },
            verify=False,
        )
        response.raise_for_status()

        # Handle response
        json_response = json.loads(response.content)

        # Get item ID from first item returned by the API which is the most
        # recent item
        if int(use_checkpoint) == 1:
            try:
                if json_response['Links']['Page.Current'].split('=')[1][:1] == '0':
                    checkpoint_id = json_response[
                        'Items'][0]['Id'].split('-')[1]
                    save_checkpoint(checkpoint, checkpoint_dir, checkpoint_id)
            except Exception as exc:
                logger.error("use_checkpoint: " + exc)
                break

        # Iterate deployments and print results to Splunk if it hasn't been
        # printed before
        for item in json_response['Items']:
            # Get deployment ID
            item_id = item['Id'].split('-')[1]

            if int(use_checkpoint) == 1:
                if int(item_id) > int(last_checkpoint_id):
                    data.append(item)
            else:
                data.append(item)

        # Try to get next page if available, else write most recent deployment
        # id and exit
        try:
            octopus_url = hostname + \
                json_response['Links']['Page.Next']
        except Exception:
            break

    return data


class OctopusDeploy(Script):

    def get_scheme(self):
        # Returns scheme.
        scheme = Scheme("Octopus Deploy API")
        scheme.description = "Streams events from the Octopus Deploy API"

        # Don't validate the input, assume this is correct.
        scheme.use_external_validation = True
        scheme.use_single_instance = False

        endpoint_argument = Argument("endpoint")
        endpoint_argument.title = "Endpoint"
        endpoint_argument.data_type = Argument.data_type_string
        endpoint_argument.description = "Octopus Deploy API endpoint to stream"
        endpoint_argument.require_on_create = True
        scheme.add_argument(endpoint_argument)

        hostname_argument = Argument("hostname")
        hostname_argument.title = "Hostname"
        hostname_argument.data_type = Argument.data_type_string
        hostname_argument.description = "Hostname of Octopus Deploy environment (http(s)://hostname:port)"
        hostname_argument.require_on_create = True
        scheme.add_argument(hostname_argument)

        apikey_argument = Argument("api_key")
        apikey_argument.title = "API key"
        apikey_argument.data_type = Argument.data_type_string
        apikey_argument.description = "Key for accessing the Octopus Deploy API"
        apikey_argument.require_on_create = True
        scheme.add_argument(apikey_argument)

        usecheck_argument = Argument("use_checkpoint")
        usecheck_argument.title = "Use check pointing"
        usecheck_argument.data_type = Argument.data_type_boolean
        usecheck_argument.description = "Decide if check pointing is needed for this endpoint"
        usecheck_argument.require_on_create = True
        scheme.add_argument(usecheck_argument)

        return scheme

    def validate_input(self, validation_definition):
        logger = setup_logging()
        logger.info("validate_inputs: " + time.strftime("%d-%m-%Y %H:%M:%S"))

        # Get the values of the parameters, and construct a URL for the Octopus
        # Deploy API
        endpoint = validation_definition.parameters["endpoint"]
        hostname = validation_definition.parameters["hostname"]
        api_key = validation_definition.parameters["api_key"]
        octopus_url = "%s/api/%s" % (hostname, endpoint)
        logger.info("URL: " + octopus_url)

        # Read the response from the Octopus Deploy API, then parse the JSON data into an object
        # Setup response object and execute GET request
        try:
            response = requests.get(
                url=octopus_url,
                headers={
                    "X-Octopus-ApiKey": api_key,
                },
                verify=False,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise requests.exceptions.HTTPError(
                "An HTTP Error occured while trygin to access the Octopus Deploy API: " + str(err))

        # If the API response seems normal, validate the endpoint count
        # If there's something wrong with getting endpoint_count, raise a
        # ValueError
        try:
            json_response = json.loads(response.content)
            endpoint_count = int(json_response["TotalResults"])
        except ValueError as ve:
            raise ValueError("Invalid endpoint count: %s", ve.message)

    def stream_events(self, inputs, ew):
        # Splunk Enterprise calls the modular input,
        # streams XML describing the inputs to stdin,
        # and waits for XML on stdout describing events.
        logger = setup_logging()
        logger.debug("stream_events: " + time.strftime("%d-%m-%Y %H:%M:%S"))

        for input_name, input_item in inputs.inputs.iteritems():
            endpoint = input_item['endpoint']
            hostname = input_item['hostname']
            api_key = input_item['api_key']
            use_checkpoint = input_item['use_checkpoint']
            checkpoint = md5.new(input_name).hexdigest()

            data = getEntries(endpoint, hostname,
                              api_key, use_checkpoint, checkpoint)

            for d in data:
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(d)

                ew.write_event(event)

if __name__ == "__main__":
    sys.exit(OctopusDeploy().run(sys.argv))
