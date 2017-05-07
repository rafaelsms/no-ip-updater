import os
import atexit
import base64
import getpass
import logging
import http.client
import configparser

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

if os.path.exists('noip-updater.log'):
    os.remove('noip-updater.log')
logger = logging.basicConfig(filename='noip-updater.log', format='%(asctime)s %(levelname)s: %(message)s',
                             datefmt='%d-%m-%Y %H:%M:%S', level='INFO')


class Configuration:
    def __init__(self):
        self.sectionName = 'DEFAULT'
        self.configuration = configparser.ConfigParser()
        self.configurationFile = os.path.expanduser('configuration.ini')
        # Writing default configuration file
        if not os.path.exists(self.configurationFile):
            self.configuration[self.sectionName] = {
                'no-ip-authorization': '',
                'no-ip-hostname': 'mytest.testdomain.com',
                'no-ip-update-interval-minutes': 5
            }
            self.save_configuration()
        else:
            self.read_configuration()

    def __contains__(self, index):
        return index in self.configuration[self.sectionName]

    def __getitem__(self, index):
        return self.configuration[self.sectionName][index]

    def __setitem__(self, index, value):
        self.configuration[self.sectionName][index] = value

    def save_configuration(self):
        with open(str(self.configurationFile), 'w') as fileWriter:
            self.configuration.write(fileWriter)
            logging.info('Wrote configuration file on ' + self.configurationFile)

    def read_configuration(self):
        self.configuration.read(self.configurationFile)


def task_listener(event):
    if event.exception:
        logging.error("Task didn't work as excepted: " + str(event.exception))
    else:
        logging.info('No-ip should be updated!')


def noip_update(authorization, hostname, ip=None):
    headers = {
        'Host': hostname,
        'Authorization': 'Basic {}'.format(authorization),
        'User-Agent': 'PythonPersonalUpdater/v0.1 rafael.sartori96@gmail.com'
    }

    connection = http.client.HTTPConnection('dynupdate.no-ip.com', 80, timeout=5)
    url = '/nic/update?hostname={}'.format(hostname) if ip is None \
        else '/nic/update?hostname={}&myip={}'.format(hostname, ip)
    connection.request('GET', url, headers=headers)
    response = connection.getresponse()
    logging.debug('HTTP Response: {} {} "{}"'.format(response.status, response.reason, response.read()))


class Updater:
    def __init__(self):
        logging.info('Reading configuration')
        self.configuration = Configuration()
        if len(self.configuration['no-ip-authorization']) is 0:
            username = input("Enter the no-ip username: ")
            password = getpass.getpass("Enter the password: ")
            self.configuration['no-ip-authorization'] = base64.b64encode("{}:{}".format(username, password)
                                                                         .encode('utf-8')).decode()
            self.configuration['no-ip-hostname'] = input("Enter the hostname (ex. mytest.testdomain.com): ")
            self.configuration['no-ip-update-interval-minutes'] = \
                input("Enter the interval to no-ip update in minutes: ")
            self.configuration.save_configuration()
            print("Configuration was saved. Install application on /opt/No-IP-Updater/ and " + \
                  "use 'systemctl start noip-updater.service'")
            exit(0)

        logging.info('Creating scheduler')
        jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')}
        self.scheduler = BlockingScheduler(jobstores)

        if self.scheduler.get_job(job_id='no-ip-update-task') is None:
            logging.info("Registering job 'no-ip-update-task'")
            self.scheduler.add_job(noip_update, 'interval', [
                self.configuration['no-ip-authorization'],
                self.configuration['no-ip-hostname']
            ], id='no-ip-update-task', max_instances=1, replace_existing=True,
                                   minutes=int(self.configuration['no-ip-update-interval-minutes']))

        # Register listener
        logging.info('Registering listener')
        self.scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        logging.info('Registering quit task')
        atexit.register(self.exit_handler)

        logging.info('Starting scheduler')
        self.scheduler.start()

    def exit_handler(self):
        logging.info('Quitting scheduler')
        self.scheduler.shutdown()
        logging.shutdown()


def main():
    logging.info("=== No-IP Updater - Rafael 'jabyftw' Sartori v0.1 ===")
    updater = Updater()


if __name__ == '__main__':
    main()
